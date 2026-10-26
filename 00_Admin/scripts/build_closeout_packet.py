#!/usr/bin/env python3
"""Build a read-only, tree-bound closeout approval packet.

The builder never stages, commits, pushes, archives, or edits target-repository
content. It snapshots the requested worktree paths and records enough state for
the applier to reject scope, index, hook, policy, or approval drift.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

PACKET_VERSION = "0.2.0"
PACKET_SCHEMA_PATH = (
    Path(__file__).resolve().parents[1]
    / "configs"
    / "validator"
    / "schema_closeout_approval_packet.yaml"
)
DEFAULT_PACKET_ROOT = Path("90_Sandbox/ai_workbooks/_closeout_packets")
DEFAULT_LIMITS = {
    "repositories": 1,
    "roots_per_repository": 8,
    "files": 25000,
    "bytes_searched": 2 * 1024 * 1024 * 1024,
    "elapsed_seconds": 120,
}
HEX40 = re.compile(r"^[0-9a-f]{40}$")


class PacketError(RuntimeError):
    """A packet cannot be built or revalidated safely."""


def _has_reparse_component(path: Path, root: Path) -> bool:
    """Reject symlink and Windows reparse components at a write boundary."""
    candidate = Path(os.path.abspath(path))
    trusted = Path(os.path.abspath(root))
    try:
        relative = candidate.relative_to(trusted)
    except ValueError:
        return True
    current = trusted
    for part in relative.parts:
        current = current / part
        if not os.path.lexists(current):
            continue
        info = current.lstat()
        if current.is_symlink() or bool(getattr(info, "st_file_attributes", 0) & 0x400):
            return True
    return False


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def validate_contract(instance: dict[str, Any], schema_path: Path, label: str) -> None:
    """Validate the supported JSON-schema subset without an optional dependency."""
    schema = yaml.safe_load(schema_path.read_text(encoding="utf-8")) or {}
    if not isinstance(schema, dict):
        raise PacketError(f"{label} schema root is not a mapping")

    def check(value: Any, spec: dict[str, Any], path: str) -> None:
        expected_type = spec.get("type")
        if expected_type is not None:
            types = expected_type if isinstance(expected_type, list) else [expected_type]
            valid = any(
                (kind == "null" and value is None)
                or (kind == "object" and isinstance(value, dict))
                or (kind == "array" and isinstance(value, list))
                or (kind == "string" and isinstance(value, str))
                or (kind == "integer" and isinstance(value, int) and not isinstance(value, bool))
                or (kind == "number" and isinstance(value, (int, float)) and not isinstance(value, bool))
                or (kind == "boolean" and isinstance(value, bool))
                for kind in types
            )
            if not valid:
                raise PacketError(f"{path} has invalid type")
        if "const" in spec and value != spec["const"]:
            raise PacketError(f"{path} does not match schema constant")
        if "enum" in spec and value not in spec["enum"]:
            raise PacketError(f"{path} is outside the schema enum")
        if isinstance(value, dict):
            missing = [key for key in spec.get("required", []) if key not in value]
            if missing:
                raise PacketError(f"{path} is missing schema fields: {', '.join(missing)}")
            properties = spec.get("properties") or {}
            if spec.get("additionalProperties") is False:
                unknown = sorted(set(value) - set(properties))
                if unknown:
                    raise PacketError(f"{path} has unexpected fields: {', '.join(unknown)}")
            for key, child in properties.items():
                if key in value and isinstance(child, dict):
                    check(value[key], child, f"{path}.{key}")
            minimum = spec.get("minProperties")
            if minimum is not None and len(value) < minimum:
                raise PacketError(f"{path} must contain at least {minimum} fields")
        if isinstance(value, list):
            minimum = spec.get("minItems")
            if minimum is not None and len(value) < minimum:
                raise PacketError(f"{path} must contain at least {minimum} items")
            item_spec = spec.get("items")
            if isinstance(item_spec, dict):
                for index, item in enumerate(value):
                    check(item, item_spec, f"{path}[{index}]")
        if isinstance(value, str):
            minimum = spec.get("minLength")
            if minimum is not None and len(value) < minimum:
                raise PacketError(f"{path} must not be empty")
            pattern = spec.get("pattern")
            if pattern and re.fullmatch(pattern, value) is None:
                raise PacketError(f"{path} does not match its schema pattern")
            if spec.get("format") == "uuid":
                try:
                    parsed = uuid.UUID(value)
                except ValueError as exc:
                    raise PacketError(f"{path} is not a UUID") from exc
                if str(parsed) != value.lower() or parsed.version != 4:
                    raise PacketError(f"{path} must be a canonical UUIDv4")
            elif spec.get("format") == "date-time":
                try:
                    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
                except ValueError as exc:
                    raise PacketError(f"{path} is not an ISO date-time") from exc
                if parsed.tzinfo is None:
                    raise PacketError(f"{path} must include a timezone")

    check(instance, schema, label)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_commit_message(message: str) -> str:
    """Return the exact message representation Git will be asked to commit."""
    if "\x00" in message:
        raise PacketError("commit message must not contain NUL bytes")
    normalized = message.replace("\r\n", "\n").replace("\r", "\n")
    normalized = "\n".join(line.rstrip() for line in normalized.split("\n"))
    normalized = normalized.strip("\n")
    if not normalized:
        raise PacketError("commit message must contain non-whitespace text")
    return normalized


def _git_env() -> dict[str, str]:
    env = os.environ.copy()
    for key in (
        "GIT_DIR",
        "GIT_INDEX_FILE",
        "GIT_WORK_TREE",
        "GIT_COMMON_DIR",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    ):
        env.pop(key, None)
    env["GIT_LITERAL_PATHSPECS"] = "1"
    return env


def _git(repo: Path, *args: str, text: bool = True) -> str | bytes:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=text,
        env=_git_env(),
    )
    if completed.returncode:
        stderr = completed.stderr if text else completed.stderr.decode("utf-8", "replace")
        raise PacketError(f"git {' '.join(args)} failed: {stderr.strip()}")
    if text:
        return completed.stdout.strip()
    return completed.stdout


def _git_optional_result(repo: Path, *args: str) -> tuple[int, str]:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=_git_env(),
    )
    return completed.returncode, completed.stdout.strip()


def _git_optional(repo: Path, *args: str) -> str:
    code, output = _git_optional_result(repo, *args)
    return output if code == 0 else ""


def _safe_path(value: str) -> str:
    normalized = value.replace("\\", "/").strip()
    candidate = Path(normalized)
    if (
        not normalized
        or normalized.startswith("/")
        or re.match(r"^[A-Za-z]:", normalized)
        or ".." in candidate.parts
        or normalized.endswith("/")
    ):
        raise PacketError(f"unsafe include path: {value!r}")
    return normalized


def _validate_generated_coupling(include: list[str]) -> None:
    workflow_paths = [path for path in include if path.startswith(".ai_ops/workflows/")]
    manifest = ".ai_ops/exports/manifest.yaml"
    if workflow_paths and manifest not in include:
        raise PacketError(
            "workflow changes require the generated export manifest in the same packet: "
            + ", ".join(workflow_paths)
        )


def _repo_file(repo: Path, relative: str) -> Path:
    lexical = repo / relative
    if _has_reparse_component(lexical, repo):
        raise PacketError(f"include path crosses a symlink/reparse point: {relative}")
    path = lexical.resolve(strict=False)
    try:
        path.relative_to(repo.resolve())
    except ValueError as exc:
        raise PacketError(f"path escapes repository: {relative}") from exc
    if path.exists() and (path.is_symlink() or not path.is_file()):
        raise PacketError(f"include path is not a regular file: {relative}")
    return path


def _head_tree(repo: Path) -> dict[str, dict[str, str]]:
    raw = _git(repo, "ls-tree", "-r", "-z", "--full-tree", "HEAD", text=False)
    tree: dict[str, dict[str, str]] = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        metadata, path_bytes = record.split(b"\t", 1)
        mode, entry_type, blob = metadata.decode("ascii").split(" ")
        path = path_bytes.decode("utf-8")
        if entry_type != "blob" or not HEX40.fullmatch(blob):
            raise PacketError(f"unsupported HEAD tree entry: {path}")
        tree[path] = {"mode": mode, "path": path, "blob_sha1": blob}
    return tree


def _status_paths(repo: Path) -> set[str]:
    raw = _git(repo, "status", "--porcelain=v1", "-z", "--untracked-files=all", text=False)
    paths: set[str] = set()
    for record in raw.split(b"\0"):
        if not record:
            continue
        if len(record) < 4:
            raise PacketError(f"malformed git status record: {record!r}")
        status = record[:2].decode("ascii", "replace")
        if "R" in status or "C" in status:
            raise PacketError("rename/copy status requires a new packet scope")
        path = record[3:].decode("utf-8")
        paths.add(_safe_path(path))
    return paths


def index_snapshot(repo: Path, *, exclude_paths: set[str] | None = None) -> dict[str, Any]:
    excluded = exclude_paths or set()
    pathspec = ["--", ".", *[f":(exclude){path}" for path in sorted(excluded)]]
    names = _git(repo, "diff", "--cached", "--name-only", "-z", "HEAD", *pathspec, text=False)
    paths = sorted(
        _safe_path(value.decode("utf-8"))
        for value in names.split(b"\0")
        if value
    )
    binary_diff = _git(repo, "diff", "--cached", "--binary", "HEAD", *pathspec, text=False)
    raw_index_entries = _git(repo, "ls-files", "-s", "-z", text=False)
    index_entries = b"\0".join(
        record
        for record in raw_index_entries.split(b"\0")
        if record
        and record.split(b"\t", 1)[-1].decode("utf-8") not in excluded
    )
    return {
        "fingerprint_sha256": sha256_bytes(binary_diff + b"\0" + index_entries),
        "paths": paths,
    }


def _nonignored_untracked_paths(repo: Path) -> set[str]:
    raw = _git(repo, "ls-files", "--others", "--exclude-standard")
    return {_safe_path(line) for line in str(raw).splitlines() if line.strip()}


def hook_snapshot(repo: Path, hooks_dir_override: Path | None = None) -> dict[str, Any]:
    hooks_dir = hooks_dir_override or Path(str(_git(repo, "rev-parse", "--git-path", "hooks")))
    if not hooks_dir.is_absolute():
        hooks_dir = (repo / hooks_dir).resolve()
    files: list[dict[str, str]] = []
    if hooks_dir.is_dir():
        for path in sorted(candidate for candidate in hooks_dir.rglob("*") if candidate.is_file()):
            files.append(
                {
                    "path": str(path.relative_to(hooks_dir)).replace("\\", "/"),
                    "sha256": sha256_file(path),
                }
            )
    payload = {"hooks_path": str(hooks_dir), "files": files}
    return {**payload, "sha256": sha256_bytes(_canonical_bytes(payload))}


def policy_snapshot(repo: Path) -> dict[str, str]:
    relative = "00_Admin/configs/closeout_security_tiers.yaml"
    code, _ = _git_optional_result(repo, "cat-file", "-e", f"HEAD:{relative}")
    if code != 0:
        return {"source": "missing_target_policy", "version": "missing", "path": relative, "sha256": "missing"}
    version = "unknown"
    head_bytes = b""
    try:
        head_bytes = bytes(_git(repo, "show", f"HEAD:{relative}", text=False))
        loaded = yaml.safe_load(head_bytes.decode("utf-8")) or {}
        version = str(loaded.get("version", "unknown"))
    except (OSError, yaml.YAMLError):
        version = "unreadable"
    return {"source": "target_HEAD", "version": version, "path": relative, "sha256": sha256_bytes(head_bytes)}


def routing_snapshot(repo: Path, *, allow_fixture_defaults: bool = False) -> dict[str, Any]:
    """Load the canonical packet limits instead of silently using code defaults."""
    path = repo / "00_Admin" / "configs" / "context_routing.yaml"
    if not path.is_file() or _has_reparse_component(path, repo):
        if not allow_fixture_defaults:
            raise PacketError("context_routing.yaml is required for a governed packet")
        return {
            "source": "builtin_defaults",
            "path": "",
            "version": "builtin",
            "sha256": "builtin",
            "limits": dict(DEFAULT_LIMITS),
            "packet_root": str(DEFAULT_PACKET_ROOT).replace("\\", "/"),
        }
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    contract = data.get("closeout_packet")
    if not isinstance(contract, dict) or not isinstance(contract.get("limits"), dict):
        raise PacketError("context_routing.yaml is missing closeout_packet.limits")
    limits: dict[str, int] = {}
    for key in DEFAULT_LIMITS:
        value = contract["limits"].get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise PacketError(f"closeout_packet.limits.{key} must be a positive integer")
        limits[key] = value
    packet_root = str(contract.get("packet_root", str(DEFAULT_PACKET_ROOT))).replace("\\", "/")
    _safe_path(packet_root)
    return {
        "source": "context_routing",
        "path": "00_Admin/configs/context_routing.yaml",
        "version": str(contract.get("version", "unknown")),
        "sha256": sha256_file(path),
        "limits": limits,
        "packet_root": packet_root,
    }


def _file_mode(repo: Path, path: Path, head_mode: str | None) -> str:
    if head_mode:
        return head_mode
    if _git_optional(repo, "config", "--get", "core.filemode").lower() == "false":
        return "100644"
    return "100755" if stat.S_IXUSR & path.stat().st_mode else "100644"


def projection(repo: Path, include: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, str]], dict[str, Any]]:
    head = _head_tree(repo)
    changed = _status_paths(repo)
    changes: list[dict[str, Any]] = []
    projected = dict(head)
    for path in include:
        if path not in changed:
            raise PacketError(f"include path is not dirty in the worktree: {path}")
        worktree_path = _repo_file(repo, path)
        head_entry = head.get(path)
        if worktree_path.exists():
            blob_sha1 = str(_git(repo, "hash-object", f"--path={path}", str(worktree_path)))
            raw_sha256 = sha256_file(worktree_path)
            mode = _file_mode(repo, worktree_path, head_entry["mode"] if head_entry else None)
            action = "add" if head_entry is None else "modify"
            if head_entry and head_entry["blob_sha1"] == blob_sha1 and head_entry["mode"] == mode:
                raise PacketError(f"include path has no projected change: {path}")
            entry = {"mode": mode, "path": path, "blob_sha1": blob_sha1}
            projected[path] = entry
            changes.append(
                {"path": path, "action": action, "mode": mode, "blob_sha1": blob_sha1, "sha256": raw_sha256}
            )
        else:
            if head_entry is None:
                raise PacketError(f"include path is missing from both HEAD and worktree: {path}")
            action = "delete"
            projected.pop(path, None)
            changes.append(
                {
                    "path": path,
                    "action": action,
                    "mode": head_entry["mode"],
                    "blob_sha1": None,
                    "sha256": None,
                }
            )
    tree_manifest = [projected[path] for path in sorted(projected)]
    observed = {
        "files": len(include),
        "bytes_searched": sum(
            int(change["sha256"] is not None and (repo / change["path"]).stat().st_size)
            for change in changes
        ),
        "repositories": 1,
        "roots_per_repository": len({path.split("/", 1)[0] for path in include}),
    }
    return changes, tree_manifest, observed


def _packet_payload(packet: dict[str, Any]) -> dict[str, Any]:
    payload = dict(packet)
    payload.pop("packet_sha256", None)
    payload.pop("prepared_packet_sha256", None)
    return payload


def packet_digest(packet: dict[str, Any]) -> str:
    return sha256_bytes(_canonical_bytes(_packet_payload(packet)))


def mutation_plan(packet: dict[str, Any]) -> dict[str, Any]:
    """Return the exact commit mutation plan bound by the packet digest."""
    return {
        "commit_only": True,
        "include": packet["include"],
        "changes": packet["changes"],
        "commit_message": packet["commit_message"],
        "remote": packet["remote"],
        "branch": packet["branch"],
        "approval_turn": "combined",
        "push_separate_approval": False,
        "merge_approval_in_same_turn": True,
    }


def write_packet(path: Path, packet: dict[str, Any], *, prepared_digest: str | None = None) -> None:
    digest = packet_digest(packet)
    packet["packet_sha256"] = digest
    packet["prepared_packet_sha256"] = prepared_digest or packet.get("prepared_packet_sha256") or digest
    path.parent.mkdir(parents=True, exist_ok=False)
    path.write_text(yaml.safe_dump(packet, sort_keys=False, allow_unicode=False), encoding="utf-8", newline="\n")


def build_packet(
    repo: Path,
    include: list[str],
    message: str,
    packet_root: Path | None = None,
    remote: str = "origin",
    *,
    allow_fixture_defaults: bool = False,
) -> Path:
    started = datetime.now(timezone.utc)
    repo = repo.resolve()
    message = normalize_commit_message(message)
    include = sorted({_safe_path(path) for path in include})
    if not include:
        raise PacketError("at least one include path is required")
    _validate_generated_coupling(include)
    index = index_snapshot(repo)
    overlap = sorted(set(include) & set(index["paths"]))
    if overlap:
        raise PacketError(f"included paths are already staged; rebuild after clearing that scope: {overlap}")
    unexpected_untracked = sorted(_nonignored_untracked_paths(repo) - set(include))
    if unexpected_untracked:
        raise PacketError(
            "nonignored untracked paths exist outside the approved include set; "
            "clean them or add them explicitly: " + ", ".join(unexpected_untracked)
        )
    branch = _git(repo, "branch", "--show-current")
    if not branch:
        raise PacketError("detached HEAD cannot produce a publication packet")
    remote_url = _git_optional(repo, "remote", "get-url", remote) or None
    changes, tree_manifest, observed = projection(repo, include)
    elapsed = (datetime.now(timezone.utc) - started).total_seconds()
    observed["elapsed_seconds"] = elapsed
    routing = routing_snapshot(repo, allow_fixture_defaults=allow_fixture_defaults)
    limits = dict(routing["limits"])
    exceeded = {
        key: {"limit": limits[key], "observed": observed[key]}
        for key in ("repositories", "roots_per_repository", "files", "bytes_searched", "elapsed_seconds")
        if observed[key] > limits[key]
    }
    run_id = str(uuid.uuid4())
    configured_root = Path(str(routing.get("packet_root", str(DEFAULT_PACKET_ROOT))))
    effective_packet_root = packet_root or (repo / configured_root)
    if not effective_packet_root.is_absolute():
        effective_packet_root = repo / effective_packet_root
    effective_packet_root = effective_packet_root.resolve()
    try:
        effective_packet_root.relative_to(repo)
    except ValueError as exc:
        raise PacketError("packet root must be contained by the repository") from exc
    base = effective_packet_root / repo.name / run_id
    include_hash = sha256_bytes("\n".join(include).encode("utf-8"))
    mutation_plan = {
        "commit_only": True,
        "include": include,
        "changes": changes,
        "commit_message": message,
        "remote": remote,
        "branch": branch,
        "approval_turn": "combined",
        "push_separate_approval": False,
        "merge_approval_in_same_turn": True,
    }
    packet: dict[str, Any] = {
        "packet_version": PACKET_VERSION,
        "run_id": run_id,
        "repo_id": repo.name,
        "repo_root": str(repo),
        "head": str(_git(repo, "rev-parse", "HEAD")),
        "branch": branch,
        "remote": remote,
        "remote_url": remote_url,
        "commit_message": message,
        "include": include,
        "exclude": [],
        "include_set_sha256": include_hash,
        "mutation_plan_sha256": sha256_bytes(_canonical_bytes(mutation_plan)),
        "changes": changes,
        "projected_tree_manifest": tree_manifest,
        "projected_tree_sha256": sha256_bytes(_canonical_bytes(tree_manifest)),
        "pre_existing_index": index,
        "pre_existing_index_preserved": index_snapshot(repo, exclude_paths=set(include)),
        "hook_fingerprint": hook_snapshot(repo),
        "policy": policy_snapshot(repo),
        "routing_contract": routing,
        "cost_profile": {"limits": limits, "observed": observed, "exceeded": exceeded},
        "frozen_clock": {"started_at": started.isoformat(), "prepared_at": datetime.now(timezone.utc).isoformat()},
        "approval_contract": {
            "approval_state": "PENDING",
            "packet_state": "PARKED" if exceeded else "PENDING",
            "required_decision": "combined_scope_clerical_commit_push_merge",
            "approval_turn": "combined",
            "push_separate": False,
            "approved_by": None,
            "approved_at": None,
            "approval_ref": None,
        },
        "state": "PARKED" if exceeded else "PENDING",
        "result": {"stop_reason": "cost_limit_exceeded", "limits": exceeded} if exceeded else None,
    }
    base.mkdir(parents=True, exist_ok=False)
    packet_path = base / "closeout_packet.yaml"
    digest = packet_digest(packet)
    packet["packet_sha256"] = digest
    packet["prepared_packet_sha256"] = digest
    validate_contract(packet, PACKET_SCHEMA_PATH, "packet")
    packet_path.write_text(yaml.safe_dump(packet, sort_keys=False, allow_unicode=False), encoding="utf-8", newline="\n")
    return packet_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a read-only closeout approval packet.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--include", action="append", required=True)
    parser.add_argument("--message", required=True)
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--packet-root", default=None)
    args = parser.parse_args()
    try:
        path = build_packet(
            Path(args.repo_root),
            args.include,
            args.message,
            Path(args.packet_root) if args.packet_root else None,
            args.remote,
        )
    except (OSError, PacketError, ValueError) as exc:
        print(f"closeout-packet-builder: {exc}", file=sys.stderr)
        return 2
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
