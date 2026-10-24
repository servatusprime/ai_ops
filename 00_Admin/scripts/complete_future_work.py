#!/usr/bin/env python3
"""Record a future-work outcome and safely complete registry items.

Only a ``success`` invocation with a completed or explicitly receipt-ready
workbook, artifact hashes, a run-log marker, and generated scorecard parity may
delete a registry entry. Failed, pending, and stale outcomes preserve the entry
and emit evidence for the next operator.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import build_closeout_packet as packet_builder
import generate_future_work_scorecard as scorecard
import yaml

RECEIPT_VERSION = "0.3.0"
RECEIPT_READY_STATE = "ready_for_receipt"
PACKET_ROOT = Path("90_Sandbox/ai_workbooks/_closeout_packets")
RECEIPT_SCHEMA_PATH = (
    Path(__file__).resolve().parents[1]
    / "configs"
    / "validator"
    / "schema_future_work_completion_receipt.yaml"
)


class CompletionError(RuntimeError):
    """The completion evidence is insufficient or unsafe."""


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256(path.read_bytes())


def _safe_relative(value: str) -> str:
    normalized = value.replace("\\", "/").strip()
    candidate = Path(normalized)
    if (
        not normalized
        or normalized.startswith("/")
        or ":" in normalized.split("/", 1)[0]
        or ".." in candidate.parts
    ):
        raise CompletionError(f"unsafe repository-relative path: {value!r}")
    return normalized


def _has_reparse_component(path: Path, root: Path) -> bool:
    candidate = Path(os.path.abspath(path))
    trusted = Path(os.path.abspath(root))
    try:
        relative = candidate.relative_to(trusted)
    except ValueError:
        candidate_real = Path(os.path.normcase(os.path.realpath(str(candidate))))
        trusted_real = Path(os.path.normcase(os.path.realpath(str(trusted))))
        try:
            relative = candidate_real.relative_to(trusted_real)
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


def _contained_path(repo: Path, value: Path, label: str) -> Path:
    candidate = value if value.is_absolute() else repo / value
    lexical = Path(os.path.abspath(candidate))
    trusted = Path(os.path.abspath(repo))
    lexical_real = Path(os.path.normcase(os.path.realpath(str(lexical))))
    trusted_real = Path(os.path.normcase(os.path.realpath(str(trusted))))
    try:
        lexical_real.relative_to(trusted_real)
    except ValueError as exc:
        raise CompletionError(f"{label} escapes repository: {value}") from exc
    if _has_reparse_component(lexical, trusted):
        raise CompletionError(f"{label} crosses a symlink/reparse point: {value}")
    return Path(os.path.realpath(str(lexical)))


def _load_mapping(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise CompletionError(f"cannot read YAML mapping: {path}") from exc
    if not isinstance(value, dict):
        raise CompletionError(f"YAML root must be a mapping: {path}")
    return value


def _read_registry(path: Path) -> dict[str, Any]:
    data = _load_mapping(path)
    entries = data.get("entries")
    if not isinstance(entries, list):
        raise CompletionError("registry entries must be a list")
    return data


def _entry_for(registry: dict[str, Any], registry_id: str) -> dict[str, Any]:
    for entry in registry["entries"]:
        if isinstance(entry, dict) and entry.get("id") == registry_id:
            return entry
    raise CompletionError(f"registry entry not found: {registry_id}")


def _repo_path(repo: Path, relative: str) -> Path:
    return _contained_path(repo, Path(_safe_relative(relative)), "artifact path")


def _workbook_frontmatter(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    frontmatter = yaml.safe_load(text[3:end]) or {}
    return frontmatter if isinstance(frontmatter, dict) else {}


def _workbook_receipt_state(path: Path, entry: dict[str, Any], relative: str) -> str | None:
    frontmatter = _workbook_frontmatter(path)
    if not str(frontmatter.get("id", "")).strip():
        return None
    proposed = entry.get("proposed_workbook")
    if not isinstance(proposed, str) or proposed != relative:
        return None
    if frontmatter.get("status") == "completed":
        return "completed"
    if (
        frontmatter.get("status") == "active"
        and frontmatter.get("execution_status") == "completed"
        and frontmatter.get("completion_state") == RECEIPT_READY_STATE
    ):
        return RECEIPT_READY_STATE
    return None


def _head_registry_entry(repo: Path, registry_path: Path, registry_id: str) -> dict[str, Any]:
    try:
        relative = registry_path.relative_to(repo).as_posix()
        raw = packet_builder._git(repo, "show", f"HEAD:{relative}")
    except (ValueError, packet_builder.PacketError) as exc:
        raise CompletionError("completion requires a readable HEAD registry binding") from exc
    try:
        head_registry = yaml.safe_load(raw) or {}
    except yaml.YAMLError as exc:
        raise CompletionError("HEAD registry is not valid YAML") from exc
    if not isinstance(head_registry, dict) or not isinstance(head_registry.get("entries"), list):
        raise CompletionError("HEAD registry entries must be a list")
    return _entry_for(head_registry, registry_id)


def _review_verdicts(text: str) -> list[str]:
    verdicts: list[str] = []
    in_fence = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if stripped.startswith("**"):
            stripped = stripped[2:].lstrip()
        if not stripped.lower().startswith("verdict:"):
            continue
        value = stripped.split(":", 1)[1].strip().strip("*").strip()
        verdicts.append(value)
    return verdicts


def _retained_nonblocking_reviews(repo: Path, refs: list[str], completion_workbook: str) -> list[str]:
    matches: list[str] = []
    expected_workbook = _safe_relative(completion_workbook)
    for relative in refs:
        lowered = relative.lower()
        if "crosscheck" not in lowered and "review" not in lowered:
            continue
        path = _repo_path(repo, relative)
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        frontmatter = _workbook_frontmatter(path)
        if frontmatter.get("status") != "completed":
            continue
        if frontmatter.get("review_type") != "completion":
            continue
        try:
            review_workbook = _safe_relative(str(frontmatter.get("workbook_ref", "")))
        except CompletionError:
            continue
        if review_workbook != expected_workbook:
            continue
        verdicts = _review_verdicts(text)
        if not verdicts:
            continue
        normalized = [value.lower() for value in verdicts]
        if normalized[0] not in {"pass", "acceptable with notes"}:
            continue
        if any(value.startswith("blocking") for value in normalized):
            continue
        if all(value == "pass" or value.startswith("acceptable with ") for value in normalized):
            matches.append(relative)
    return sorted(set(matches))


def _artifact_manifest(repo: Path, paths: list[str]) -> list[dict[str, Any]]:
    manifest: list[dict[str, Any]] = []
    for relative in paths:
        path = _repo_path(repo, relative)
        if not path.is_file():
            raise CompletionError(f"completion artifact is missing: {relative}")
        manifest.append({"path": _safe_relative(relative), "sha256": _sha256_file(path)})
    return manifest


def _normalized_scorecard(text: str) -> str:
    lines = [line for line in text.replace("\r\n", "\n").splitlines() if not line.startswith("updated:")]
    return "\n".join(lines).rstrip() + "\n"


def _scorecard_text(registry_path: Path, registry: dict[str, Any], repo: Path) -> str:
    rows = scorecard._build_rows(registry.get("entries", []))
    return scorecard._render_markdown(registry_path, rows, repo)


def _remove_registry_entry_text(text: str, registry_id: str) -> str:
    """Remove one two-space registry row without reserializing the registry."""
    lines = text.replace("\r\n", "\n").splitlines(keepends=True)
    marker = f"  - id: {registry_id}"
    start = next((index for index, line in enumerate(lines) if line.rstrip("\n") == marker), None)
    if start is None:
        raise CompletionError(f"registry entry not found in source text: {registry_id}")
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("  - id: ") or (
            lines[index].strip() and not lines[index].startswith((" ", "#"))
        ):
            end = index
            break
    while end > start and not lines[end - 1].strip():
        end -= 1
    replacement = lines[:start] + lines[end:]
    return "".join(replacement)


def _marker(
    *,
    registry_id: str,
    run_id: str,
    status: str,
    exit_code: int,
    scope_sha256: str,
    artifact_sha256: str | None,
    completion_workbook: str | None,
    completion_state: str | None,
    actor: str,
    scorecard_source_sha256: str,
    provenance_refs: list[str],
    review_refs: list[str],
) -> str:
    payload = {
        "future_work_completion": {
            "registry_id": registry_id,
            "run_id": run_id,
            "status": status,
            "exit_code": exit_code,
            "scope_sha256": scope_sha256,
            "completion_artifact_sha256": artifact_sha256,
            "completion_workbook": completion_workbook,
            "completion_state": completion_state,
            "actor": actor,
            "scorecard_source_sha256": scorecard_source_sha256,
            "evidence_refs": provenance_refs,
            "review_refs": review_refs,
        }
    }
    body = yaml.safe_dump(payload, sort_keys=False, allow_unicode=False)
    return (
        f"\n\n### Future-work completion receipt: {run_id}\n\n"
        "```yaml\n"
        f"{body}"
        "```\n"
    )


def _receipt_digest(receipt: dict[str, Any]) -> str:
    payload = dict(receipt)
    payload.pop("receipt_sha256", None)
    return _sha256(_canonical(payload))


def _validate_receipt_contract(receipt: dict[str, Any]) -> None:
    try:
        packet_builder.validate_contract(receipt, RECEIPT_SCHEMA_PATH, "receipt")
    except packet_builder.PacketError as exc:
        raise CompletionError(str(exc)) from exc


def _write(path: Path, text: str) -> None:
    _atomic_write(path, text.encode("utf-8"))


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _write_exclusive(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())


def _restore_target(path: Path, existed: bool, data: bytes) -> None:
    if existed:
        _atomic_write(path, data)
    elif path.exists():
        path.unlink()


def _cleanup_transaction(receipt_dir: Path) -> None:
    for name in ("transaction_journal.yaml", "registry.before", "run_log.before", "scorecard.before"):
        candidate = receipt_dir / name
        if candidate.exists():
            candidate.unlink()


def _configured_packet_root(repo: Path) -> Path:
    routing_path = repo / "00_Admin" / "configs" / "context_routing.yaml"
    if not routing_path.is_file():
        raise CompletionError("context_routing.yaml is required when packet_root is omitted")
    routing = _load_mapping(routing_path)
    contract = routing.get("closeout_packet")
    if not isinstance(contract, dict) or not isinstance(contract.get("packet_root"), str):
        raise CompletionError("context_routing.yaml is missing closeout_packet.packet_root")
    return _contained_path(repo, Path(contract["packet_root"]), "configured packet root")


def _existing_journals(packet_root: Path, repo: Path) -> list[Path]:
    if not packet_root.exists():
        return []
    journals: list[Path] = []
    for candidate in packet_root.rglob("transaction_journal.yaml"):
        if candidate.is_file():
            journals.append(_contained_path(repo, candidate, "transaction journal"))
    return sorted(journals)


def recover_journal(repo: Path, journal_path: Path) -> None:
    repo = repo.resolve()
    journal = _contained_path(repo, journal_path, "transaction journal")
    data = _load_mapping(journal)
    targets = data.get("targets")
    if not isinstance(targets, list):
        raise CompletionError("transaction journal targets must be a list")
    receipt_path = journal.parent / "future_work_completion.yaml"
    if receipt_path.exists():
        raise CompletionError(
            "transaction journal has a completion receipt; preserve both for manual evidence reconciliation"
        )
    for target in targets:
        if not isinstance(target, dict):
            raise CompletionError("transaction journal target must be a mapping")
        destination = _contained_path(repo, Path(str(target["path"])), "journal target")
        existed = bool(target.get("existed"))
        backup = _contained_path(repo, Path(str(target["backup"])), "journal backup")
        if existed:
            if not backup.is_file() or _sha256_file(backup) != target.get("sha256"):
                raise CompletionError(f"journal backup is missing or hash-mismatched: {backup}")
            _atomic_write(destination, backup.read_bytes())
        elif destination.exists():
            destination.unlink()
    receipt_dir = journal.parent
    _cleanup_transaction(receipt_dir)
    if receipt_dir.exists():
        receipt_dir.rmdir()


def _prepare_transaction(
    receipt_dir: Path,
    targets: list[tuple[str, Path, bool, bytes]],
    run_id: str,
) -> Path:
    receipt_dir.mkdir(parents=True, exist_ok=False)
    backups: list[dict[str, Any]] = []
    for name, path, existed, data in targets:
        backup = receipt_dir / f"{name}.before"
        if existed:
            _atomic_write(backup, data)
        backups.append(
            {
                "name": name,
                "path": str(path),
                "existed": existed,
                "sha256": _sha256(data) if existed else None,
                "backup": str(backup),
            }
        )
    journal = receipt_dir / "transaction_journal.yaml"
    _atomic_write(
        journal,
        yaml.safe_dump(
            {"version": "0.1.0", "run_id": run_id, "phase": "prepared", "targets": backups},
            sort_keys=False,
            allow_unicode=False,
        ).encode("utf-8"),
    )
    return journal


def complete(
    *,
    repo: Path,
    registry_path: Path,
    run_log_path: Path,
    scorecard_path: Path,
    registry_id: str,
    completion_workbook: str,
    artifacts: list[str],
    status: str,
    exit_code: int,
    actor: str,
    run_id: str | None = None,
    provenance_refs: list[str] | None = None,
    packet_root: Path | None = None,
) -> Path:
    if status not in {"success", "failed", "pending", "stale"}:
        raise CompletionError(f"unsupported status: {status}")
    run_id = run_id or str(uuid.uuid4())
    try:
        parsed_run_id = uuid.UUID(run_id)
    except ValueError as exc:
        raise CompletionError("run_id must be UUIDv4-compatible") from exc
    if str(parsed_run_id) != run_id.lower() or parsed_run_id.version != 4:
        raise CompletionError("run_id must be a canonical UUIDv4")
    if not actor.strip() or "\n" in actor or "\r" in actor:
        raise CompletionError("actor must be a non-empty single-line value")
    repo = repo.resolve()
    registry_path = _contained_path(repo, registry_path, "registry")
    run_log_path = _contained_path(repo, run_log_path, "run log")
    scorecard_path = _contained_path(repo, scorecard_path, "scorecard")
    effective_packet_root = (
        _contained_path(repo, packet_root, "packet root")
        if packet_root
        else _configured_packet_root(repo)
    )
    journals = _existing_journals(effective_packet_root, repo)
    if journals:
        raise CompletionError(f"unfinished completion journal requires recovery: {journals[0]}")
    registry = _read_registry(registry_path)
    entry = _entry_for(registry, registry_id)
    completion_workbook = _safe_relative(completion_workbook)
    artifacts = sorted({_safe_relative(path) for path in (artifacts or [completion_workbook])})
    refs = sorted(set(provenance_refs or []))
    scope_sha256 = _sha256(_canonical(entry))
    workbook_path = _repo_path(repo, completion_workbook)
    artifact_manifest: list[dict[str, Any]] = []
    completion_state: str | None = None
    if status == "success":
        head_entry = _head_registry_entry(repo, registry_path, registry_id)
        head_proposed = head_entry.get("proposed_workbook")
        if not isinstance(head_proposed, str) or head_proposed != completion_workbook:
            raise CompletionError(
                "success requires the HEAD registry entry to bind proposed_workbook to the completion workbook"
            )
    review_refs = _retained_nonblocking_reviews(repo, refs, completion_workbook) if status == "success" else []
    if status == "success":
        if exit_code != 0:
            raise CompletionError("success requires exit_code 0")
        if not review_refs:
            raise CompletionError("success requires a retained non-blocking crosscheck or review reference")
        completion_state = _workbook_receipt_state(workbook_path, entry, completion_workbook)
        if completion_state is None:
            raise CompletionError(
                "success requires a completion workbook with status: completed, or "
                "status: active plus execution_status: completed and "
                f"completion_state: {RECEIPT_READY_STATE}"
            )
        artifact_manifest = _artifact_manifest(repo, artifacts)
        if completion_workbook not in {item["path"] for item in artifact_manifest}:
            raise CompletionError("success artifact manifest must include the completion workbook")
    else:
        for relative in artifacts:
            candidate = _repo_path(repo, relative)
            if candidate.is_file():
                artifact_manifest.append({"path": relative, "sha256": _sha256_file(candidate)})
    artifact_sha256 = _sha256(_canonical(artifact_manifest)) if artifact_manifest else None
    started_at = datetime.now(timezone.utc)
    original_registry = registry_path.read_bytes()
    original_registry_text = original_registry.decode("utf-8")
    original_log_exists = run_log_path.exists()
    original_log = run_log_path.read_bytes() if original_log_exists else b""
    original_scorecard_exists = scorecard_path.exists()
    original_scorecard = scorecard_path.read_bytes() if original_scorecard_exists else b""
    original_scorecard_text = original_scorecard.decode("utf-8")
    if status == "success":
        next_registry_text = _remove_registry_entry_text(original_registry_text, registry_id)
        next_registry = yaml.safe_load(next_registry_text) or {}
        if not isinstance(next_registry, dict):
            raise CompletionError("registry after deletion is not a mapping")
        if next_registry.get("entries") is None:
            next_registry["entries"] = []
            next_registry_text = next_registry_text.replace("entries:\n", "entries: []\n", 1)
        next_scorecard = _scorecard_text(registry_path, next_registry, repo)
    else:
        next_registry_text = original_registry_text
        next_registry = registry
        next_scorecard = original_scorecard_text
    scorecard_source_sha256 = _sha256(_normalized_scorecard(next_scorecard).encode("utf-8"))
    marker = _marker(
        registry_id=registry_id,
        run_id=run_id,
        status=status,
        exit_code=exit_code,
        scope_sha256=scope_sha256,
        artifact_sha256=artifact_sha256,
        completion_workbook=completion_workbook,
        completion_state=completion_state,
        actor=actor,
        scorecard_source_sha256=scorecard_source_sha256,
        provenance_refs=refs,
        review_refs=review_refs,
    )
    marker_sha256 = _sha256(marker.replace("\r\n", "\n").encode("utf-8"))
    next_log = original_log.decode("utf-8").rstrip("\n") + marker
    run_log_id = f"future-work-completion:{run_id}"
    run_log_sha256 = _sha256(next_log.replace("\r\n", "\n").encode("utf-8"))
    completed_at = datetime.now(timezone.utc)
    receipt: dict[str, Any] = {
        "receipt_version": RECEIPT_VERSION,
        "registry_id": registry_id,
        "run_id": run_id,
        "status": status,
        "exit_code": exit_code,
        "scope_sha256": scope_sha256,
        "completion_artifact_sha256": artifact_sha256,
        "actor": actor,
        "started_at": started_at.isoformat(),
        "completed_at": completed_at.isoformat(),
        "completion_workbook": completion_workbook,
        "completion_state": completion_state,
        "run_log_id": run_log_id,
        "run_log_sha256": run_log_sha256,
        "run_log_marker_sha256": marker_sha256,
        "scorecard_source_sha256": scorecard_source_sha256,
        "provenance_refs": refs,
        "review_refs": review_refs,
        "artifact_manifest": artifact_manifest,
        "registry_entry_sha256": scope_sha256,
        "registry_deleted": status == "success",
        "result": {
            "registry_entries_before": len(registry["entries"]),
            "registry_entries_after": len(next_registry["entries"]),
        },
    }
    receipt["receipt_sha256"] = _receipt_digest(receipt)
    receipt_dir = effective_packet_root / repo.name / run_id
    receipt_path = receipt_dir / "future_work_completion.yaml"
    journal_path = receipt_dir / "transaction_journal.yaml"
    if _has_reparse_component(receipt_dir, repo):
        raise CompletionError(f"receipt directory crosses a symlink/reparse point: {receipt_dir}")
    if receipt_path.exists():
        raise CompletionError(f"receipt already exists: {receipt_path}")
    if journal_path.exists():
        raise CompletionError(f"unfinished completion journal requires recovery: {journal_path}")
    if receipt_dir.exists():
        raise CompletionError(f"receipt directory already exists and requires recovery: {receipt_dir}")
    targets = [
        ("registry", registry_path, True, original_registry),
        ("run_log", run_log_path, original_log_exists, original_log),
        ("scorecard", scorecard_path, original_scorecard_exists, original_scorecard),
    ]
    try:
        _prepare_transaction(receipt_dir, targets, run_id)
        if status == "success":
            _write(registry_path, next_registry_text)
            _write(scorecard_path, next_scorecard)
        _write(run_log_path, next_log)
        actual_log = run_log_path.read_bytes()
        if status == "success":
            actual_registry = _load_mapping(registry_path)
            actual_scorecard = scorecard_path.read_text(encoding="utf-8")
            remaining_ids = {
                candidate.get("id")
                for candidate in actual_registry.get("entries", [])
                if isinstance(candidate, dict)
            }
            if registry_id in remaining_ids:
                raise CompletionError("registry entry survived successful completion")
            before_ids = {
                candidate.get("id")
                for candidate in registry.get("entries", [])
                if isinstance(candidate, dict)
            }
            if remaining_ids != before_ids - {registry_id}:
                raise CompletionError("successful completion changed an unrelated registry entry")
            persisted_registry = _read_registry(registry_path)
            independently_rendered = _scorecard_text(registry_path, persisted_registry, repo)
            if _normalized_scorecard(actual_scorecard) != _normalized_scorecard(independently_rendered):
                raise CompletionError("generated scorecard parity check failed")
        receipt["run_log_sha256"] = _sha256(actual_log)
        receipt["receipt_sha256"] = _receipt_digest(receipt)
        _validate_receipt_contract(receipt)
        _write_exclusive(receipt_path, yaml.safe_dump(receipt, sort_keys=False, allow_unicode=False))
    except Exception:
        try:
            _restore_target(registry_path, True, original_registry)
            _restore_target(run_log_path, original_log_exists, original_log)
            _restore_target(scorecard_path, original_scorecard_exists, original_scorecard)
            if receipt_path.exists():
                receipt_path.unlink()
            _cleanup_transaction(receipt_dir)
            receipt_dir.rmdir()
        except OSError:
            # Preserve the journal when recovery itself fails; the next run
            # will park rather than mutate through an unknown partial state.
            raise
        raise
    _cleanup_transaction(receipt_dir)
    return receipt_path


def verify_receipt(
    *, repo: Path, receipt_path: Path, run_log_path: Path, registry_path: Path
) -> None:
    repo = repo.resolve()
    receipt_path = _contained_path(repo, receipt_path, "receipt")
    run_log_path = _contained_path(repo, run_log_path, "run log")
    registry_path = _contained_path(repo, registry_path, "registry")
    receipt = _load_mapping(receipt_path)
    _validate_receipt_contract(receipt)
    if _receipt_digest(receipt) != receipt.get("receipt_sha256"):
        raise CompletionError("receipt digest does not match its persisted content")
    log_text = run_log_path.read_text(encoding="utf-8")
    heading = f"### Future-work completion receipt: {receipt['run_id']}"
    start = log_text.find(f"\n\n{heading}\n")
    if start < 0:
        raise CompletionError("receipt marker is missing from the run log")
    fence_start = log_text.find("```yaml\n", start)
    fence_end = log_text.find("\n```\n", fence_start)
    if fence_start < 0 or fence_end < 0:
        raise CompletionError("receipt marker YAML fence is malformed")
    marker_end = fence_end + len("\n```\n")
    marker = log_text[start:marker_end]
    if _sha256(marker.replace("\r\n", "\n").encode("utf-8")) != receipt["run_log_marker_sha256"]:
        raise CompletionError("run-log marker hash does not match the receipt")
    marker_data = yaml.safe_load(log_text[fence_start + len("```yaml\n") : fence_end]) or {}
    marker_payload = marker_data.get("future_work_completion") if isinstance(marker_data, dict) else None
    if not isinstance(marker_payload, dict):
        raise CompletionError("run-log marker payload is not a mapping")
    for key in (
        "registry_id",
        "run_id",
        "status",
        "exit_code",
        "scope_sha256",
        "completion_artifact_sha256",
        "completion_workbook",
        "completion_state",
        "actor",
        "scorecard_source_sha256",
        "review_refs",
    ):
        if marker_payload.get(key) != receipt.get(key):
            raise CompletionError(f"run-log marker does not bind receipt field: {key}")
    review_refs = receipt.get("review_refs", [])
    if (
        receipt["status"] == "success"
        and _retained_nonblocking_reviews(repo, review_refs, receipt["completion_workbook"])
        != sorted(set(review_refs))
    ):
        raise CompletionError("successful receipt review evidence is missing or no longer non-blocking")
    registry = _read_registry(registry_path)
    ids = {entry.get("id") for entry in registry.get("entries", []) if isinstance(entry, dict)}
    if receipt["status"] == "success":
        manifest = receipt.get("artifact_manifest")
        expected_artifact_hash = _sha256(_canonical(manifest)) if isinstance(manifest, list) else None
        if not manifest or expected_artifact_hash != receipt.get("completion_artifact_sha256"):
            raise CompletionError("successful receipt artifact manifest is incomplete or unbound")
        workbook = receipt.get("completion_workbook")
        manifest_paths = {item.get("path") for item in manifest if isinstance(item, dict)}
        if workbook not in manifest_paths:
            raise CompletionError("successful receipt artifact manifest omits the completion workbook")
        if receipt["registry_id"] in ids:
            raise CompletionError("successful receipt does not match registry deletion")
    print(f"verified {receipt_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Record a future-work completion outcome.")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--recover", action="store_true")
    parser.add_argument("--receipt", default=None)
    parser.add_argument("--journal", default=None)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--registry", default="00_Admin/backlog/future_work_registry.yaml")
    parser.add_argument("--run-log", default="00_Admin/logs/log_workbook_run.md")
    parser.add_argument("--scorecard", default="00_Admin/backlog/future_work_scorecard.md")
    parser.add_argument("--registry-id", default=None)
    parser.add_argument("--completion-workbook", default=None)
    parser.add_argument("--artifact", action="append", default=[])
    parser.add_argument("--status", choices=["success", "failed", "pending", "stale"], default=None)
    parser.add_argument("--exit-code", type=int, default=0)
    parser.add_argument("--actor", default=None)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--provenance-ref", action="append", default=[])
    parser.add_argument("--packet-root", default=None)
    args = parser.parse_args()
    try:
        if args.recover:
            repo = Path(args.repo_root).resolve()
            packet_root = (
                _contained_path(repo, Path(args.packet_root), "packet root")
                if args.packet_root
                else _configured_packet_root(repo)
            )
            journals = _existing_journals(packet_root, repo)
            if args.journal:
                journals = [_contained_path(repo, Path(args.journal), "transaction journal")]
            if len(journals) != 1:
                raise CompletionError("--recover requires exactly one transaction journal or --journal")
            recover_journal(repo, journals[0])
            print(f"recovered {journals[0]}")
            return 0
        if args.verify:
            if not args.receipt:
                raise CompletionError("--verify requires --receipt")
            verify_receipt(
                repo=Path(args.repo_root),
                receipt_path=Path(args.receipt),
                run_log_path=Path(args.run_log),
                registry_path=Path(args.registry),
            )
            return 0
        if not args.registry_id or not args.completion_workbook or not args.status or not args.actor:
            raise CompletionError("completion requires registry id, workbook, status, and actor")
        receipt = complete(
            repo=Path(args.repo_root),
            registry_path=Path(args.registry),
            run_log_path=Path(args.run_log),
            scorecard_path=Path(args.scorecard),
            registry_id=args.registry_id,
            completion_workbook=args.completion_workbook,
            artifacts=args.artifact,
            status=args.status,
            exit_code=args.exit_code,
            actor=args.actor,
            run_id=args.run_id,
            provenance_refs=args.provenance_ref,
            packet_root=Path(args.packet_root) if args.packet_root else None,
        )
    except (OSError, CompletionError, ValueError, yaml.YAMLError) as exc:
        print(f"future-work-completion: {exc}", file=sys.stderr)
        return 2
    print(receipt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
