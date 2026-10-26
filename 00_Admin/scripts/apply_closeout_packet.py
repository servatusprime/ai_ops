#!/usr/bin/env python3
"""Apply an approved closeout packet without widening its scope.

The applier is the only packet operation that stages or commits. It never
pushes. Any drift parks or fails the packet and preserves the pre-commit
repository state where possible. A post-commit validation failure records the
existing commit and an explicit recovery handoff; it never presents that
packet as push-ready.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import build_closeout_packet as builder
import yaml


def _load(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise builder.PacketError("packet or approval file must contain a mapping")
    return value


def _write_packet(path: Path, packet: dict[str, Any]) -> None:
    packet["packet_sha256"] = builder.packet_digest(packet)
    path.write_text(yaml.safe_dump(packet, sort_keys=False, allow_unicode=False), encoding="utf-8", newline="\n")


def _set_state(path: Path, packet: dict[str, Any], state: str, result: dict[str, Any]) -> None:
    packet["state"] = state
    packet["approval_contract"]["packet_state"] = state
    packet["result"] = result
    packet["updated_at"] = datetime.now(timezone.utc).isoformat()
    _write_packet(path, packet)


def _run_commit(
    repo: Path, message: str, paths: list[str], hooks_path: Path | None = None
) -> tuple[int, str, str]:
    command = ["git", "-C", str(repo)]
    if hooks_path is not None:
        command.extend(["-c", f"core.hooksPath={hooks_path.as_posix()}"])
    message_file: Path | None = None
    try:
        descriptor, raw_path = tempfile.mkstemp(prefix="closeout-commit-", suffix=".msg")
        os.close(descriptor)
        message_file = Path(raw_path)
        message_file.write_text(message, encoding="utf-8", newline="\n")
        command.extend(["commit", "--only", "--cleanup=verbatim", "-F", str(message_file), "--", *paths])
        completed = subprocess.run(
            command,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=builder._git_env(),
        )
        return completed.returncode, completed.stdout, completed.stderr
    finally:
        if message_file is not None:
            message_file.unlink(missing_ok=True)


def _read_commit_message(repo: Path) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), "log", "-1", "--format=%B"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,
        env=builder._git_env(),
    )
    if completed.returncode:
        raise builder.PacketError(
            f"git log commit message lookup failed: {completed.stderr.decode('utf-8', 'replace').strip()}"
        )
    return completed.stdout.decode("utf-8")


def _index_entries(repo: Path, env: dict[str, str] | None = None) -> dict[str, dict[str, str]]:
    if env is None:
        raw = builder._git(repo, "ls-files", "-s", "-z", text=False)
    else:
        completed = subprocess.run(
            ["git", "-C", str(repo), "ls-files", "-s", "-z"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False,
            env=env,
        )
        if completed.returncode:
            raise builder.PacketError(
                f"git ls-files failed for isolated hook index: {completed.stderr.decode('utf-8', 'replace').strip()}"
            )
        raw = completed.stdout
    entries: dict[str, dict[str, str]] = {}
    for record in bytes(raw).split(b"\0"):
        if not record:
            continue
        metadata, path_bytes = record.split(b"\t", 1)
        mode, blob, _stage = metadata.decode("ascii").split(" ")
        path = builder._safe_path(path_bytes.decode("utf-8"))
        entries[path] = {"mode": mode, "blob_sha1": blob}
    return entries


def _prepare_hook_index(repo: Path, include: list[str]) -> tuple[Path, dict[str, str]]:
    index_root = Path(str(builder._git(repo, "rev-parse", "--git-path", "index")))
    if not index_root.is_absolute():
        index_root = (repo / index_root).resolve()
    descriptor, raw_path = tempfile.mkstemp(
        prefix="closeout-hook-index-", suffix=".idx", dir=str(index_root.parent)
    )
    os.close(descriptor)
    index_path = Path(raw_path)
    index_path.unlink()
    env = builder._git_env()
    env["GIT_INDEX_FILE"] = str(index_path)
    read_tree = subprocess.run(
        ["git", "-C", str(repo), "read-tree", "HEAD"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    if read_tree.returncode:
        index_path.unlink(missing_ok=True)
        raise builder.PacketError(f"isolated hook index initialization failed: {read_tree.stderr.strip()}")
    add = subprocess.run(
        ["git", "-C", str(repo), "add", "--", *include],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    if add.returncode:
        index_path.unlink(missing_ok=True)
        raise builder.PacketError(f"isolated hook index staging failed: {add.stderr.strip()}")
    return index_path, env


def _unstage(repo: Path, paths: list[str]) -> bool:
    if not paths:
        return True
    completed = subprocess.run(
        ["git", "-C", str(repo), "reset", "--", *paths],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=builder._git_env(),
    )
    return completed.returncode == 0


def _run_hook(repo: Path, hook_name: str, env: dict[str, str] | None = None) -> tuple[int, str, str]:
    effective_env = env if env is not None else builder._git_env()
    completed = subprocess.run(
        ["git", "-C", str(repo), "hook", "run", hook_name],
        cwd=repo,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=effective_env,
    )
    return completed.returncode, completed.stdout, completed.stderr


def _hook_failure_detail(stdout: str, stderr: str) -> str:
    """Return both hook streams so launcher failures remain diagnosable."""

    details = []
    if stdout.strip():
        details.append(f"stdout: {stdout.strip()}")
    if stderr.strip():
        details.append(f"stderr: {stderr.strip()}")
    return "\n".join(details) or "no hook diagnostics captured"


def _has_hook(packet: dict[str, Any], hook_name: str) -> bool:
    return any(
        Path(str(item.get("path", ""))).name == hook_name
        for item in packet.get("hook_fingerprint", {}).get("files", [])
    )


def _run_first_landing_gate(repo: Path, include: list[str], receipt_path: Path) -> None:
    """Validate a supplied staged first-landing receipt before commit."""
    _contained_repo_path(receipt_path, repo, "first-landing receipt")
    if not receipt_path.is_file():
        raise builder.PacketError(f"first-landing receipt does not exist: {receipt_path}")
    config = repo / "00_Admin/configs/closeout_security_tiers.yaml"
    validator = Path(__file__).with_name("validate_closeout_security_receipt.py")
    gate = subprocess.run(
        [
            sys.executable,
            str(validator),
            "--repo-root",
            str(repo),
            "--config",
            str(config),
            "--receipt",
            str(receipt_path),
            "--gate",
            "--staged",
            "--first-landing",
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=builder._git_env(),
    )
    if gate.returncode:
        detail = (gate.stderr or gate.stdout).strip()
        raise builder.PacketError(f"first-landing staged gate failed: {detail}")


def _recomputed_exceeded(
    packet: dict[str, Any], observed: dict[str, Any], started_at: datetime
) -> dict[str, dict[str, Any]]:
    now_elapsed = (datetime.now(timezone.utc) - started_at).total_seconds()
    observed["elapsed_seconds"] = now_elapsed
    limits = packet["routing_contract"]["limits"]
    return {
        key: {"limit": limits[key], "observed": observed[key]}
        for key in ("repositories", "roots_per_repository", "files", "bytes_searched", "elapsed_seconds")
        if observed[key] > limits[key]
    }


def _contained_repo_path(path: Path, repo: Path, label: str) -> None:
    lexical = Path(os.path.abspath(path))
    trusted = Path(os.path.abspath(repo))
    try:
        lexical.relative_to(trusted)
    except ValueError as exc:
        raise builder.PacketError(f"{label} escapes repository: {path}") from exc
    if builder._has_reparse_component(lexical, trusted):
        raise builder.PacketError(f"{label} crosses a symlink/reparse point: {path}")
    resolved = Path(os.path.normcase(os.path.realpath(str(lexical))))
    resolved_root = Path(os.path.normcase(os.path.realpath(str(trusted))))
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise builder.PacketError(f"{label} resolves outside repository: {path}") from exc


def apply_packet(packet_path: Path, approval_path: Path, first_landing_receipt: Path | None = None) -> str:
    packet = _load(packet_path)
    approval = _load(approval_path)
    builder.validate_contract(packet, builder.PACKET_SCHEMA_PATH, "packet")
    approval_schema = builder.PACKET_SCHEMA_PATH.parent / "schema_closeout_approval.yaml"
    builder.validate_contract(approval, approval_schema, "approval")
    if builder.packet_digest(packet) != packet.get("packet_sha256"):
        raise builder.PacketError("packet digest does not match its persisted content")
    if packet.get("packet_version") != builder.PACKET_VERSION:
        raise builder.PacketError("unsupported packet version")
    if builder.normalize_commit_message(str(packet.get("commit_message", ""))) != packet.get("commit_message"):
        raise builder.PacketError("packet commit message is not normalized")
    if packet.get("state") != "PENDING":
        raise builder.PacketError(f"packet is not applyable in state {packet.get('state')!r}")
    if packet.get("prepared_packet_sha256") != packet.get("packet_sha256"):
        raise builder.PacketError("pending packet no longer matches its prepared digest")
    if approval.get("decision") != "approve":
        raise builder.PacketError("approval decision must be approve")
    required = {
        "run_id": packet.get("run_id"),
        "packet_sha256": packet.get("prepared_packet_sha256"),
        "head": packet.get("head"),
        "branch": packet.get("branch"),
        "projected_tree_sha256": packet.get("projected_tree_sha256"),
        "include_set_sha256": packet.get("include_set_sha256"),
        "mutation_plan_sha256": packet.get("mutation_plan_sha256"),
    }
    for key, expected in required.items():
        if approval.get(key) != expected:
            raise builder.PacketError(f"approval does not bind {key}")
    if approval.get("run_id") != packet.get("run_id"):
        raise builder.PacketError("approval run_id does not bind packet")
    include = [builder._safe_path(path) for path in packet["include"]]
    policy_upgrade = "00_Admin/configs/closeout_security_tiers.yaml" in include
    if policy_upgrade and first_landing_receipt is None:
        raise builder.PacketError(
            "packet includes the closeout security policy; --first-landing-receipt is required"
        )
    expected_include_hash = builder.sha256_bytes("\n".join(include).encode("utf-8"))
    if expected_include_hash != packet["include_set_sha256"]:
        raise builder.PacketError("packet include-set hash is invalid")
    if builder.sha256_bytes(builder._canonical_bytes(builder.mutation_plan(packet))) != packet["mutation_plan_sha256"]:
        raise builder.PacketError("packet mutation-plan hash is invalid")
    projected_tree_hash = builder.sha256_bytes(
        builder._canonical_bytes(packet["projected_tree_manifest"])
    )
    if projected_tree_hash != packet["projected_tree_sha256"]:
        raise builder.PacketError("packet projected-tree hash is invalid")
    approved_by = str(approval.get("approved_by", "")).strip()
    if not approved_by or approved_by.lower() in {"pending", "unknown", "none", "missing"}:
        raise builder.PacketError("approval must name an actor")
    repo = Path(str(packet["repo_root"])).resolve()
    _contained_repo_path(packet_path, repo, "packet")
    _contained_repo_path(approval_path, repo, "approval")
    execution_started_at = datetime.now(timezone.utc)
    try:
        if str(builder._git(repo, "rev-parse", "HEAD")) != packet["head"]:
            raise builder.PacketError("HEAD changed since packet preparation")
        if str(builder._git(repo, "branch", "--show-current")) != packet["branch"]:
            raise builder.PacketError("branch changed since packet preparation")
        if builder.index_snapshot(repo) != packet["pre_existing_index"]:
            raise builder.PacketError("pre-existing index changed since packet preparation")
        if builder.hook_snapshot(repo) != packet["hook_fingerprint"]:
            raise builder.PacketError("hook fingerprint changed since packet preparation")
        if builder.policy_snapshot(repo) != packet["policy"]:
            raise builder.PacketError("closeout policy changed since packet preparation")
        if builder.routing_snapshot(
            repo,
            allow_fixture_defaults=packet["routing_contract"].get("source") == "builtin_defaults",
        ) != packet["routing_contract"]:
            raise builder.PacketError("context routing contract changed since packet preparation")
        if (builder._git_optional(repo, "remote", "get-url", packet["remote"]) or None) != packet.get("remote_url"):
            raise builder.PacketError("remote URL changed since packet preparation")
        changes, projected_tree, observed = builder.projection(repo, include)
        if changes != packet["changes"] or projected_tree != packet["projected_tree_manifest"]:
            raise builder.PacketError("projected bytes or tree changed since packet preparation")
        recomputed_exceeded = _recomputed_exceeded(packet, observed, execution_started_at)
        if recomputed_exceeded:
            _set_state(
                packet_path,
                packet,
                "PARKED",
                {"reason": "recomputed_cost_limit_mismatch", "limits": recomputed_exceeded},
            )
            raise builder.PacketError("packet execution exceeded a configured cost limit; packet is parked")
        if packet["cost_profile"].get("exceeded", {}):
            _set_state(
                packet_path,
                packet,
                "INVALIDATED",
                {"reason": "stored_cost_limit_exceeded_on_pending_packet"},
            )
            raise builder.PacketError("pending packet contains a stored cost-limit exceedance")
    except builder.PacketError as exc:
        if packet.get("state") not in {"PARKED", "INVALIDATED"}:
            _set_state(packet_path, packet, "INVALIDATED", {"reason": str(exc)})
        raise

    packet["state"] = "APPROVED"
    packet["approval_contract"].update(
        {
            "approval_state": "APPROVED",
            "packet_state": "APPROVED",
            "approved_by": approved_by,
            "approved_at": str(approval.get("approved_at", "")),
            "approval_ref": str(approval.get("approval_ref", "")),
        }
    )
    _write_packet(packet_path, packet)

    add = subprocess.run(
        ["git", "-C", str(repo), "add", "--", *include],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=builder._git_env(),
    )
    if add.returncode:
        unstaged = _unstage(repo, include)
        _set_state(packet_path, packet, "FAILED", {"operation": "stage", "stderr": add.stderr, "unstaged": unstaged})
        raise builder.PacketError(f"staging failed: {add.stderr.strip()}")
    staged = builder.index_snapshot(repo)
    expected_paths = sorted(set(packet["pre_existing_index"]["paths"]) | set(include))
    if staged["paths"] != expected_paths:
        unstaged = _unstage(repo, include)
        _set_state(
            packet_path,
            packet,
            "FAILED",
            {"operation": "stage", "staged_paths": staged["paths"], "unstaged": unstaged},
        )
        raise builder.PacketError("staged paths differ from pre-existing plus approved paths")
    staged_entries = _index_entries(repo)
    for change in packet["changes"]:
        path = change["path"]
        entry = staged_entries.get(path)
        if change["action"] == "delete":
            if entry is not None:
                unstaged = _unstage(repo, include)
                _set_state(
                    packet_path,
                    packet,
                    "FAILED",
                    {"operation": "stage", "reason": f"deleted path remains staged: {path}", "unstaged": unstaged},
                )
                raise builder.PacketError(f"deleted path remains staged: {path}")
        elif entry != {"mode": change["mode"], "blob_sha1": change["blob_sha1"]}:
            unstaged = _unstage(repo, include)
            _set_state(
                packet_path,
                packet,
                "FAILED",
                {"operation": "stage", "reason": f"staged blob or mode mismatch: {path}", "unstaged": unstaged},
            )
            raise builder.PacketError(f"staged blob or mode mismatch: {path}")

    if first_landing_receipt is not None:
        try:
            _run_first_landing_gate(repo, include, first_landing_receipt)
        except builder.PacketError as exc:
            unstaged = _unstage(repo, include)
            _set_state(
                packet_path,
                packet,
                "FAILED",
                {"operation": "first_landing_gate", "reason": str(exc), "unstaged": unstaged},
            )
            raise

    staged_index = builder.index_snapshot(repo)
    if _has_hook(packet, "pre-commit"):
        hook_index_path: Path | None = None
        try:
            try:
                hook_index_path, hook_env = _prepare_hook_index(repo, include)
            except builder.PacketError as exc:
                unstaged = _unstage(repo, include)
                _set_state(
                    packet_path,
                    packet,
                    "FAILED",
                    {"operation": "pre_commit_hook", "reason": str(exc), "unstaged": unstaged},
                )
                raise
            hook_code, hook_stdout, hook_stderr = _run_hook(repo, "pre-commit", hook_env)
            if hook_code:
                unstaged = _unstage(repo, include)
                _set_state(
                    packet_path,
                    packet,
                    "FAILED",
                    {
                        "operation": "pre_commit_hook",
                        "stdout": hook_stdout,
                        "stderr": hook_stderr,
                        "unstaged": unstaged,
                    },
                )
                raise builder.PacketError(
                    f"pre-commit hook failed: {_hook_failure_detail(hook_stdout, hook_stderr)}"
                )
            if builder.hook_snapshot(repo) != packet["hook_fingerprint"]:
                unstaged = _unstage(repo, include)
                _set_state(
                    packet_path,
                    packet,
                    "INVALIDATED",
                    {"reason": "hook changed during preflight", "unstaged": unstaged},
                )
                raise builder.PacketError("hook fingerprint changed during pre-commit preflight")
            expected_hook_entries = {
                entry["path"]: {"mode": entry["mode"], "blob_sha1": entry["blob_sha1"]}
                for entry in packet["projected_tree_manifest"]
            }
            if _index_entries(repo, hook_env) != expected_hook_entries:
                unstaged = _unstage(repo, include)
                _set_state(
                    packet_path,
                    packet,
                    "FAILED",
                    {"operation": "pre_commit_hook", "reason": "isolated hook index changed", "unstaged": unstaged},
                )
                raise builder.PacketError("pre-commit hook changed the isolated index")
            if builder.index_snapshot(repo) != staged_index:
                unstaged = _unstage(repo, include)
                _set_state(
                    packet_path,
                    packet,
                    "FAILED",
                    {
                        "operation": "pre_commit_hook",
                        "reason": "real index changed during preflight",
                        "unstaged": unstaged,
                    },
                )
                raise builder.PacketError("pre-commit hook changed the real index during preflight")
            hook_changes, hook_tree, _hook_observed = builder.projection(repo, include)
            if hook_changes != packet["changes"] or hook_tree != packet["projected_tree_manifest"]:
                unstaged = _unstage(repo, include)
                _set_state(
                    packet_path,
                    packet,
                    "FAILED",
                    {"operation": "pre_commit_hook", "reason": "hook changed approved bytes", "unstaged": unstaged},
                )
                raise builder.PacketError("pre-commit hook changed approved bytes before commit")
        except builder.PacketError:
            if packet.get("state") == "APPROVED":
                unstaged = _unstage(repo, include)
                _set_state(packet_path, packet, "FAILED", {"operation": "pre_commit_hook", "unstaged": unstaged})
            raise
        finally:
            if hook_index_path is not None:
                hook_index_path.unlink(missing_ok=True)

    try:
        final_changes, final_tree, final_observed = builder.projection(repo, include)
    except builder.PacketError as exc:
        unstaged = _unstage(repo, include)
        _set_state(
            packet_path,
            packet,
            "FAILED",
            {"operation": "pre_commit_preflight", "reason": str(exc), "unstaged": unstaged},
        )
        raise
    if final_changes != packet["changes"] or final_tree != packet["projected_tree_manifest"]:
        unstaged = _unstage(repo, include)
        _set_state(
            packet_path,
            packet,
            "FAILED",
            {"operation": "pre_commit_preflight", "reason": "approved bytes changed", "unstaged": unstaged},
        )
        raise builder.PacketError("approved bytes changed after pre-commit preflight")
    final_exceeded = _recomputed_exceeded(packet, final_observed, execution_started_at)
    if final_exceeded:
        unstaged = _unstage(repo, include)
        _set_state(
            packet_path,
            packet,
            "PARKED",
            {"reason": "execution_cost_limit_exceeded", "limits": final_exceeded, "unstaged": unstaged},
        )
        raise builder.PacketError("execution exceeded a configured cost limit before commit; packet is parked")

    if _has_hook(packet, "pre-commit"):
        hook_code, hook_stdout, hook_stderr = _run_hook(repo, "pre-commit", builder._git_env())
        if hook_code:
            unstaged = _unstage(repo, include)
            _set_state(
                packet_path,
                packet,
                "FAILED",
                {
                    "operation": "pre_commit_commit_gate",
                    "stdout": hook_stdout,
                    "stderr": hook_stderr,
                    "unstaged": unstaged,
                },
            )
            raise builder.PacketError(
                f"pre-commit hook failed before commit: {_hook_failure_detail(hook_stdout, hook_stderr)}"
            )
        if builder.hook_snapshot(repo) != packet["hook_fingerprint"]:
            unstaged = _unstage(repo, include)
            _set_state(
                packet_path,
                packet,
                "INVALIDATED",
                {"reason": "hook changed during commit gate", "unstaged": unstaged},
            )
            raise builder.PacketError("hook fingerprint changed during commit gate")
        if builder.index_snapshot(repo) != staged_index:
            unstaged = _unstage(repo, include)
            _set_state(
                packet_path,
                packet,
                "FAILED",
                {"operation": "pre_commit_commit_gate", "reason": "real index changed", "unstaged": unstaged},
            )
            raise builder.PacketError("pre-commit hook changed the real index before commit")
        try:
            gate_changes, gate_tree, gate_observed = builder.projection(repo, include)
        except builder.PacketError as exc:
            unstaged = _unstage(repo, include)
            _set_state(
                packet_path,
                packet,
                "FAILED",
                {"operation": "pre_commit_commit_gate", "reason": str(exc), "unstaged": unstaged},
            )
            raise
        if gate_changes != packet["changes"] or gate_tree != packet["projected_tree_manifest"]:
            unstaged = _unstage(repo, include)
            _set_state(
                packet_path,
                packet,
                "FAILED",
                {"operation": "pre_commit_commit_gate", "reason": "approved bytes changed", "unstaged": unstaged},
            )
            raise builder.PacketError("pre-commit hook changed approved bytes before commit")
        gate_exceeded = _recomputed_exceeded(packet, gate_observed, execution_started_at)
        if gate_exceeded:
            unstaged = _unstage(repo, include)
            _set_state(
                packet_path,
                packet,
                "PARKED",
                {"reason": "execution_cost_limit_exceeded", "limits": gate_exceeded, "unstaged": unstaged},
            )
            raise builder.PacketError("execution exceeded a configured cost limit at the commit gate; packet is parked")

    # The disposable native-hook dry run passed with ai_ops's real
    # pre-commit-framework shims. Keep the installed hooks active for the
    # ordinary commit; the earlier isolated and real-index preflights remain
    # evidence checks, while native pre-commit/commit-msg hooks retain final
    # authority at commit time.
    return_code, stdout, stderr = _run_commit(repo, packet["commit_message"], include)
    if return_code:
        unstaged = _unstage(repo, include)
        _set_state(
            packet_path,
            packet,
            "FAILED",
            {"operation": "commit", "stdout": stdout, "stderr": stderr, "unstaged": unstaged},
        )
        raise builder.PacketError(f"commit failed: {stderr.strip()}")
    commit_sha: str | None = None
    try:
        commit_sha = str(builder._git(repo, "rev-parse", "HEAD"))
        if str(builder._git(repo, "rev-parse", "HEAD^")) != packet["head"]:
            raise builder.PacketError("commit parent does not match packet HEAD")
        actual_message = builder.normalize_commit_message(_read_commit_message(repo))
        if actual_message != packet["commit_message"]:
            raise builder.PacketError("commit message does not match packet")
        actual_tree = builder._head_tree(repo)
        actual_manifest = [actual_tree[path] for path in sorted(actual_tree)]
        tree_ok = actual_manifest == packet["projected_tree_manifest"]
        worktree_ok = True
        for change in packet["changes"]:
            path = builder._repo_file(repo, change["path"])
            if change["action"] == "delete":
                worktree_ok = worktree_ok and not path.exists()
                continue
            if not path.exists():
                worktree_ok = False
                continue
            current_blob = str(builder._git(repo, "hash-object", f"--path={change['path']}", str(path)))
            current_sha256 = builder.sha256_file(path)
            worktree_ok = worktree_ok and current_blob == change["blob_sha1"] and current_sha256 == change["sha256"]
        index_ok = builder.index_snapshot(repo, exclude_paths=set(include)) == packet["pre_existing_index_preserved"]
        result = {
            "commit_sha": commit_sha,
            "tree_sha256": builder.sha256_bytes(builder._canonical_bytes(actual_manifest)),
            "expected_tree_sha256": packet["projected_tree_sha256"],
            "tree_match": tree_ok,
            "worktree_match": worktree_ok,
            "index_match": index_ok,
            "push_allowed": tree_ok and worktree_ok and index_ok,
            "stdout": stdout,
        }
        if not tree_ok or not worktree_ok or not index_ok:
            raise builder.PacketError("post-commit tree or worktree binding mismatch; push handoff is blocked")
        _set_state(packet_path, packet, "APPLIED", result)
        return commit_sha
    except (OSError, builder.PacketError, ValueError) as exc:
        if packet.get("state") == "APPROVED":
            _set_state(
                packet_path,
                packet,
                "FAILED",
                {
                    "operation": "post_commit_validation",
                    "commit_sha": commit_sha,
                    "reason": str(exc),
                    "recovery": (
                        "commit may already exist; inspect the recorded HEAD and do not push "
                        "until verify-push succeeds"
                    ),
                    "stdout": stdout,
                },
            )
        raise


def verify_push_ready(packet_path: Path) -> str:
    packet = _load(packet_path)
    builder.validate_contract(packet, builder.PACKET_SCHEMA_PATH, "packet")
    if builder.packet_digest(packet) != packet.get("packet_sha256"):
        raise builder.PacketError("packet digest does not match its persisted content")
    if packet.get("state") != "APPLIED":
        raise builder.PacketError("packet is not applied; push is not authorized")
    result = packet.get("result") or {}
    if not all(result.get(key) is True for key in ("tree_match", "worktree_match", "index_match", "push_allowed")):
        raise builder.PacketError("packet does not contain a verified push-ready result")
    commit_sha = result.get("commit_sha")
    if not isinstance(commit_sha, str) or not builder.HEX40.fullmatch(commit_sha):
        raise builder.PacketError("packet does not contain a verified commit SHA")
    repo = Path(str(packet["repo_root"])).resolve()
    _contained_repo_path(packet_path, repo, "packet")
    if str(builder._git(repo, "rev-parse", "HEAD")) != commit_sha:
        raise builder.PacketError("repository HEAD does not match the applied commit SHA")
    if str(builder._git(repo, "branch", "--show-current")) != str(packet["branch"]):
        raise builder.PacketError("repository branch does not match the applied packet")
    if (builder._git_optional(repo, "remote", "get-url", packet["remote"]) or None) != packet.get("remote_url"):
        raise builder.PacketError("repository remote URL does not match the applied packet")
    if str(builder._git(repo, "rev-parse", "HEAD^")) != str(packet["head"]):
        raise builder.PacketError("applied commit parent does not match the packet HEAD")
    if builder.normalize_commit_message(_read_commit_message(repo)) != packet["commit_message"]:
        raise builder.PacketError("applied commit message does not match the packet")
    actual_tree = builder._head_tree(repo)
    actual_manifest = [actual_tree[path] for path in sorted(actual_tree)]
    actual_tree_hash = builder.sha256_bytes(builder._canonical_bytes(actual_manifest))
    if actual_tree_hash != packet["projected_tree_sha256"]:
        raise builder.PacketError("repository HEAD tree does not match the applied packet")
    include = [builder._safe_path(path) for path in packet["include"]]
    for change in packet["changes"]:
        path = builder._repo_file(repo, change["path"])
        if change["action"] == "delete":
            if path.exists():
                raise builder.PacketError(f"applied deletion is not reflected in the worktree: {change['path']}")
            continue
        if not path.exists():
            raise builder.PacketError(f"applied file is missing from the worktree: {change['path']}")
        if str(builder._git(repo, "hash-object", f"--path={change['path']}", str(path))) != change["blob_sha1"]:
            raise builder.PacketError(f"worktree blob does not match the applied packet: {change['path']}")
        if builder.sha256_file(path) != change["sha256"]:
            raise builder.PacketError(f"worktree bytes do not match the applied packet: {change['path']}")
    if builder.index_snapshot(repo, exclude_paths=set(include)) != packet["pre_existing_index_preserved"]:
        raise builder.PacketError("unrelated staged index state changed after packet application")
    actual_result = {
        "commit_sha": commit_sha,
        "tree_match": actual_manifest == packet["projected_tree_manifest"],
        "worktree_match": True,
        "index_match": True,
        "push_allowed": True,
    }
    if actual_result["tree_match"] is not True:
        raise builder.PacketError("repository tree manifest does not match the applied packet")
    for key, value in actual_result.items():
        if result.get(key) is not value:
            raise builder.PacketError(f"stored push result does not match live state: {key}")
    return commit_sha


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply an approved closeout packet; never push.")
    parser.add_argument("--packet", required=True)
    parser.add_argument("--approval-file", default=None)
    parser.add_argument(
        "--first-landing-receipt",
        default=None,
        help="repository-contained path for a separate staged policy-upgrade receipt",
    )
    parser.add_argument("--verify-push", action="store_true")
    args = parser.parse_args()
    try:
        if args.verify_push:
            print(verify_push_ready(Path(args.packet)))
            return 0
        if not args.approval_file:
            raise builder.PacketError("--approval-file is required for packet application")
        first_landing_receipt = Path(args.first_landing_receipt) if args.first_landing_receipt else None
        commit_sha = apply_packet(Path(args.packet), Path(args.approval_file), first_landing_receipt)
    except (OSError, builder.PacketError, ValueError) as exc:
        print(f"closeout-packet-applier: {exc}", file=sys.stderr)
        return 2
    print(commit_sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
