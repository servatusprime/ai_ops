#!/usr/bin/env python3
"""Plan or archive terminal closeout packet attempts.

Closeout packets are run-scoped evidence.  This command never deletes them:
with ``--apply`` it moves only terminal, non-final packets to the recoverable
``99_Trash/closeout_packets`` lane.  Pending, approved, malformed, and
unknown-state packets are preserved for explicit human disposition.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import build_closeout_packet as builder
import yaml
from path_safety import assert_no_reparse_components

DEFAULT_PACKET_ROOT = Path("90_Sandbox/ai_workbooks/_closeout_packets")
ARCHIVE_ROOT = Path("99_Trash/closeout_packets")
PACKET_FILENAME = "closeout_packet.yaml"
KNOWN_STATES = {"PENDING", "APPROVED", "APPLIED", "INVALIDATED", "PARKED", "FAILED"}
ACTIVE_STATES = {"PENDING", "APPROVED"}
TERMINAL_STATES = {"APPLIED", "INVALIDATED", "PARKED", "FAILED"}


class PruneError(ValueError):
    """Raised when the packet root or a packet cannot be safely evaluated."""


@dataclass(frozen=True)
class PacketRecord:
    run_id: str
    state: str | None
    source: Path
    destination: Path
    action: str
    reason: str


@dataclass(frozen=True)
class PrunePlan:
    records: tuple[PacketRecord, ...]
    non_closeout_entries: tuple[Path, ...]

    @property
    def candidates(self) -> tuple[PacketRecord, ...]:
        return tuple(record for record in self.records if record.action == "archive")

    @property
    def protected(self) -> tuple[PacketRecord, ...]:
        return tuple(record for record in self.records if record.action == "preserve")

    @property
    def blocked(self) -> tuple[PacketRecord, ...]:
        return tuple(record for record in self.records if record.action == "blocked")


def _contained(repo: Path, candidate: Path, label: str) -> Path:
    repo_resolved = repo.resolve()
    candidate_resolved = candidate.resolve()
    try:
        candidate_resolved.relative_to(repo_resolved)
    except ValueError as exc:
        raise PruneError(f"{label} escapes repository root: {candidate}") from exc
    return candidate_resolved


def _assert_no_reparse(path: Path, repo: Path, label: str) -> None:
    try:
        assert_no_reparse_components(path, root=repo, label=label)
    except ValueError as exc:
        raise PruneError(str(exc)) from exc


def _load_packet(path: Path, repo: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        _assert_no_reparse(path, repo, "packet file")
    except PruneError as exc:
        return None, str(exc)
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        return None, f"cannot read packet: {exc}"
    if not isinstance(value, dict):
        return None, "packet is not a mapping"
    try:
        builder.validate_contract(value, builder.PACKET_SCHEMA_PATH, "packet")
    except builder.PacketError as exc:
        return None, f"packet schema validation failed: {exc}"
    run_id = value.get("run_id")
    if not isinstance(run_id, str):
        return None, "packet run_id is missing"
    try:
        uuid.UUID(run_id)
    except ValueError:
        return None, "packet run_id is not a UUID"
    state = value.get("state")
    if state not in KNOWN_STATES:
        return None, f"packet state is unknown: {state!r}"
    contract = value.get("approval_contract")
    if not isinstance(contract, dict) or contract.get("packet_state") != state:
        return None, "packet approval_contract state does not bind packet state"
    packet_repo = value.get("repo_root")
    if not isinstance(packet_repo, str) or Path(packet_repo).resolve() != repo.resolve():
        return None, "packet repo_root does not match validation target"
    packet_sha = value.get("packet_sha256")
    if not isinstance(packet_sha, str) or packet_sha != builder.packet_digest(value):
        return None, "packet digest does not match persisted content"
    return value, None


def _effective_packet_root(repo: Path, packet_root: Path | None) -> Path:
    configured = packet_root or DEFAULT_PACKET_ROOT
    effective = configured if configured.is_absolute() else repo / configured
    effective = _contained(repo, effective, "packet root")
    _assert_no_reparse(effective, repo, "packet root")
    return effective


def _record_for_packet(
    repo: Path,
    packet_path: Path,
    keep_run_id: str | None,
) -> PacketRecord:
    source = packet_path.parent
    run_id = source.name
    destination = _contained(repo, repo / ARCHIVE_ROOT / repo.name / run_id, "archive destination")
    try:
        uuid.UUID(run_id)
    except ValueError:
        return PacketRecord(run_id, None, source, destination, "blocked", "directory name is not a UUID")

    packet, error = _load_packet(packet_path, repo)
    if error is not None or packet is None:
        return PacketRecord(run_id, None, source, destination, "blocked", error or "packet is invalid")
    if packet["run_id"] != run_id:
        return PacketRecord(
            run_id,
            str(packet["state"]),
            source,
            destination,
            "blocked",
            "directory and packet run IDs differ",
        )
    state = str(packet["state"])
    if state in ACTIVE_STATES:
        return PacketRecord(run_id, state, source, destination, "preserve", "active packet state")
    if state == "APPLIED" and run_id == keep_run_id:
        return PacketRecord(run_id, state, source, destination, "preserve", "operator-selected final packet")
    if state == "APPLIED" and keep_run_id is None:
        return PacketRecord(
            run_id,
            state,
            source,
            destination,
            "preserve",
            "final run ID is required before pruning applied packets",
        )
    if state in TERMINAL_STATES:
        return PacketRecord(run_id, state, source, destination, "archive", "terminal non-final packet")
    return PacketRecord(run_id, state, source, destination, "blocked", "packet state cannot be safely classified")


def plan_prune(
    repo_root: Path,
    *,
    packet_root: Path | None = None,
    keep_run_id: str | None = None,
) -> PrunePlan:
    repo = repo_root.resolve()
    if not repo.is_dir():
        raise PruneError(f"repository root does not exist: {repo}")
    effective_root = _effective_packet_root(repo, packet_root)
    repo_packets = effective_root / repo.name
    if not repo_packets.exists():
        if keep_run_id is not None:
            raise PruneError(f"keep run ID was not found: {keep_run_id}")
        return PrunePlan((), ())
    _assert_no_reparse(repo_packets, repo, "packet repository directory")
    records: list[PacketRecord] = []
    non_closeout: list[Path] = []
    for entry in sorted(repo_packets.iterdir(), key=lambda item: item.name):
        try:
            _assert_no_reparse(entry, repo, "packet directory")
        except PruneError as exc:
            records.append(PacketRecord(entry.name, None, entry, entry, "blocked", str(exc)))
            continue
        if not entry.is_dir():
            non_closeout.append(entry)
            continue
        packet_path = entry / PACKET_FILENAME
        if not packet_path.is_file():
            non_closeout.append(entry)
            continue
        records.append(_record_for_packet(repo, packet_path, keep_run_id))
    if keep_run_id is not None:
        selected = next((record for record in records if record.run_id == keep_run_id), None)
        if selected is None:
            raise PruneError(f"keep run ID was not found: {keep_run_id}")
        if selected.state != "APPLIED":
            raise PruneError(f"keep run ID must identify an APPLIED packet: {keep_run_id}")
    return PrunePlan(tuple(records), tuple(non_closeout))


def apply_plan(repo_root: Path, plan: PrunePlan) -> tuple[Path, ...]:
    if plan.blocked:
        reasons = "; ".join(f"{record.run_id}: {record.reason}" for record in plan.blocked)
        raise PruneError(f"refusing to archive while packet safety checks are blocked: {reasons}")
    repo = repo_root.resolve()
    for record in plan.candidates:
        _contained(repo, record.source, "packet source")
        _contained(repo, record.destination, "archive destination")
        _assert_no_reparse(record.source, repo, "packet source")
        _assert_no_reparse(record.destination, repo, "archive destination")
        if record.destination.exists():
            raise PruneError(f"archive destination already exists: {record.destination}")
    archived: list[Path] = []
    try:
        for record in plan.candidates:
            record.destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(record.source), str(record.destination))
            archived.append(record.destination)
    except (OSError, shutil.Error) as exc:
        rollback_errors: list[str] = []
        for destination in reversed(archived):
            source = next(record.source for record in plan.candidates if record.destination == destination)
            try:
                _assert_no_reparse(destination, repo, "archive destination")
                if source.exists() or source.is_symlink():
                    raise PruneError(f"rollback source already exists: {source}")
                shutil.move(str(destination), str(source))
            except (OSError, PruneError, shutil.Error) as rollback_exc:
                rollback_errors.append(f"{destination}: {rollback_exc}")
        detail = f"archive failed and rollback was {'incomplete' if rollback_errors else 'completed'}: {exc}"
        if rollback_errors:
            detail += "; " + "; ".join(rollback_errors)
        raise PruneError(detail) from exc
    return tuple(archived)


def _print_plan(plan: PrunePlan, *, apply: bool) -> None:
    mode = "ARCHIVE" if apply else "PLAN"
    print(f"[{mode}] closeout packet retention")
    for record in plan.records:
        print(f"[{record.action.upper()}] {record.run_id} state={record.state or 'unknown'}: {record.reason}")
        if record.action == "archive":
            print(f"        source: {record.source}")
            print(f"        destination: {record.destination}")
    for entry in plan.non_closeout_entries:
        print(f"[PRESERVE] {entry.name}: no closeout_packet.yaml; outside this retention sweep")
    print(f"[SUMMARY] archive={len(plan.candidates)} preserve={len(plan.protected)} blocked={len(plan.blocked)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--packet-root", type=Path, default=None)
    parser.add_argument("--keep-run-id", default=None, help="UUID of the final successful packet to preserve")
    parser.add_argument("--apply", action="store_true", help="archive terminal non-final packets to 99_Trash")
    args = parser.parse_args(argv)
    if args.apply and not args.keep_run_id:
        print("closeout-packet-prune: --keep-run-id is required with --apply", file=sys.stderr)
        return 2
    try:
        plan = plan_prune(args.repo_root, packet_root=args.packet_root, keep_run_id=args.keep_run_id)
        _print_plan(plan, apply=args.apply)
        if args.apply:
            archived = apply_plan(args.repo_root, plan)
            print(f"[OK] archived {len(archived)} terminal packet(s) to 99_Trash")
    except (OSError, PruneError, yaml.YAMLError) as exc:
        print(f"closeout-packet-prune: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
