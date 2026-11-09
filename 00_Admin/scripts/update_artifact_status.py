#!/usr/bin/env python3
"""Update artifact status in work_state.yaml.

Usage:
  python 00_Admin/scripts/update_artifact_status.py --id <artifact_id> --status <status>
  python 00_Admin/scripts/update_artifact_status.py --id <artifact_id> --status <status> --note "note text"
  python 00_Admin/scripts/update_artifact_status.py --id <artifact_id> --status <status> --dry-run
  python 00_Admin/scripts/update_artifact_status.py --id <artifact_id> --remove [--all-matches] [--dry-run]
  python 00_Admin/scripts/update_artifact_status.py --check [--id <artifact_id>]

Reads .ai_ops/local/work_state.yaml, finds the matching artifact by id, and updates
its status and optional note field; it writes no other file (the bundle README Status
checklist is updated by hand). Status values are the five in policy_status_values.md
(one-to-one aliases such as "complete" normalize); notes are capped at 300 characters.
--remove deletes the entry with that exact id only when every matching entry is
already `completed` or `deprecated`; an id matching
more than one entry is rejected unless --all-matches is passed. --check is read-only:
it reports off-policy statuses, over-cap notes and duplicate ids across the whole file,
or only the selected id when --id is supplied.

Exit codes:
  0  success (or dry-run success, or --check found nothing)
  1  artifact not found in work_state.yaml
  2  configuration, I/O or input error (including an id matching several entries)
  3  --check found an off-policy status, an over-cap note or a duplicate id
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Optional

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None  # type: ignore


# ---------------------------------------------------------------------------
# Path resolution and vocabulary
# ---------------------------------------------------------------------------

_SCRIPT_DIR = Path(__file__).resolve().parent  # 00_Admin/scripts/
_REPO_ROOT = _SCRIPT_DIR.parents[1]            # ai_ops/

_WORK_STATE_PATH = _REPO_ROOT / ".ai_ops" / "local" / "work_state.yaml"

STATUS_VALUES = ("planned", "stub", "active", "completed", "deprecated")  # policy_status_values.md
STATUS_ALIASES = {
    "complete": "completed",
    "draft": "stub",
    "wip": "stub",
    "in_progress": "stub",
    "beta": "stub",
}
REMOVABLE_STATUSES = frozenset({"completed", "deprecated"})
NOTE_CAP = 300


class StateError(Exception):
    """work_state.yaml cannot be read or written as expected (exit 2)."""


# ---------------------------------------------------------------------------
# YAML helpers
# ---------------------------------------------------------------------------

def _load_yaml(path: Path) -> Any:
    if yaml is None:
        print(
            "ERROR: PyYAML is not installed. Install it with: pip install pyyaml",
            file=sys.stderr,
        )
        sys.exit(2)
    try:
        with path.open("r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise StateError(f"could not read {path.name}: {exc}") from exc


def _dump_yaml(data: Any, path: Path) -> None:
    tmp = path.with_name(path.name + ".tmp")
    try:
        with tmp.open("w", encoding="utf-8", newline="\n") as fh:
            yaml.dump(data, fh, default_flow_style=False, allow_unicode=True, sort_keys=False)
        os.replace(tmp, path)  # atomic: readers never see a half-written file
    except OSError as exc:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        raise StateError(f"could not write {path.name}: {exc}") from exc


def _artifacts(data: Any) -> list[dict[str, Any]]:
    context = data.get("work_context") if isinstance(data, dict) else None
    if not isinstance(context, dict):
        raise StateError("work_state.yaml has no work_context mapping")
    if "active_artifacts" not in context:
        raise StateError("work_state.yaml has no work_context.active_artifacts list")
    if not isinstance(context["active_artifacts"], list):
        raise StateError("work_context.active_artifacts is not a list")
    for index, entry in enumerate(context["active_artifacts"]):
        if not isinstance(entry, dict):
            raise StateError(f"work_context.active_artifacts[{index}] is not a mapping")
        artifact_id = entry.get("id")
        if not isinstance(artifact_id, str) or not artifact_id.strip():
            raise StateError(f"work_context.active_artifacts[{index}] has no non-empty id")
    return context["active_artifacts"]


# ---------------------------------------------------------------------------
# work_state.yaml update
# ---------------------------------------------------------------------------

def _matching_artifacts(
    artifacts: list[dict[str, Any]], artifact_id: str
) -> list[dict[str, Any]]:
    return [entry for entry in artifacts if entry.get("id") == artifact_id]


def _update_work_state(
    artifact_id: str,
    new_status: str,
    note: Optional[str],
    dry_run: bool,
) -> bool:
    """Update the work_state.yaml entry. Returns False when the id is absent."""
    data = _load_yaml(_WORK_STATE_PATH)
    matches = _matching_artifacts(_artifacts(data), artifact_id)
    if not matches:
        return False
    if len(matches) > 1:
        raise StateError(
            f"id {artifact_id!r} matches {len(matches)} entries; refusing a status update"
        )
    entry = matches[0]

    old_status = entry.get("status", "(none)")

    if not dry_run:
        entry["status"] = new_status
        if note is not None:
            entry["note"] = note
        _dump_yaml(data, _WORK_STATE_PATH)

    mode = "[DRY-RUN] " if dry_run else ""
    print(f"{mode}work_state.yaml: {artifact_id}")
    print(f"  status: {old_status!r} -> {new_status!r}")
    if note is not None:
        print(f"  note: {note!r}")

    return True


def _remove_entries(artifact_id: str, all_matches: bool, dry_run: bool) -> int:
    """Remove eligible entries with this exact id; unrelated entries are kept as they are."""
    data = _load_yaml(_WORK_STATE_PATH)
    artifacts = _artifacts(data)
    matches = [e for e in artifacts if isinstance(e, dict) and e.get("id") == artifact_id]
    count = len(matches)
    if count == 0:
        print(f"ERROR: artifact id {artifact_id!r} not found in {_WORK_STATE_PATH}", file=sys.stderr)
        return 1
    if count > 1 and not all_matches:
        print(
            f"ERROR: id {artifact_id!r} matches {count} entries; pass --all-matches to remove all of them",
            file=sys.stderr,
        )
        return 2
    blocked = [
        (entry.get("id"), entry.get("status"))
        for entry in matches
        if entry.get("status") not in REMOVABLE_STATUSES
    ]
    if blocked:
        details = ", ".join(f"{entry_id!r} has status {status!r}" for entry_id, status in blocked)
        print(
            f"ERROR: --remove requires status completed or deprecated for every matching entry; {details}",
            file=sys.stderr,
        )
        return 2
    if not dry_run:
        artifacts[:] = [e for e in artifacts if not (isinstance(e, dict) and e.get("id") == artifact_id)]
        _dump_yaml(data, _WORK_STATE_PATH)
    mode = "[DRY-RUN] " if dry_run else ""
    print(f"{mode}work_state.yaml: removed {count} entry(ies) with id {artifact_id!r}")
    return 0


def _check_file(artifact_id: Optional[str] = None) -> int:
    """Read-only: report policy problems globally or for one exact artifact id."""
    problems = []
    entries = [e for e in _artifacts(_load_yaml(_WORK_STATE_PATH)) if isinstance(e, dict)]
    if artifact_id is not None:
        entries = [e for e in entries if e.get("id") == artifact_id]
        if not entries:
            print(f"ERROR: artifact id {artifact_id!r} not found in {_WORK_STATE_PATH}", file=sys.stderr)
            return 1
    ids = [e.get("id") for e in entries]
    for dup in sorted({i for i in ids if ids.count(i) > 1}, key=str):
        problems.append(f"{dup!r}: id appears {ids.count(dup)} times (remove or merge the duplicates)")
    for entry in entries:
        status, note = entry.get("status"), entry.get("note")
        if status not in STATUS_VALUES:
            problems.append(f"{entry.get('id')!r}: status {status!r} is not in policy_status_values.md")
        if note is not None and not isinstance(note, str):
            problems.append(f"{entry.get('id')!r}: note is not text or null")
        elif isinstance(note, str) and len(note) > NOTE_CAP:
            problems.append(f"{entry.get('id')!r}: note is {len(note)} characters (cap {NOTE_CAP})")
    for line in problems:
        print(f"CHECK: {line}")
    print(f"CHECK: {len(problems)} problem(s) in {_WORK_STATE_PATH.name}")
    return 3 if problems else 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Update artifact status in work_state.yaml.\n\n"
            "Reads .ai_ops/local/work_state.yaml, finds the artifact by --id, "
            "and updates its status (and optional note), or removes it with --remove. "
            "No other file is written. "
            "--check reports off-policy statuses, over-cap notes and duplicate ids without writing."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--id",
        metavar="ARTIFACT_ID",
        help=(
            "Artifact id to update or remove (must match the 'id' field in work_state.yaml)."
        ),
    )
    parser.add_argument(
        "--status",
        metavar="STATUS",
        help="New status value: planned, stub, active, completed or deprecated (policy_status_values.md).",
    )
    parser.add_argument(
        "--note",
        default=None,
        metavar="NOTE",
        help=f"Optional note to set on the artifact entry (at most {NOTE_CAP} characters).",
    )
    parser.add_argument(
        "--remove",
        action="store_true",
        help="Remove an exact id only after closeout sets every match to completed or deprecated.",
    )
    parser.add_argument(
        "--all-matches",
        action="store_true",
        help="With --remove: remove every entry with this id (otherwise several matches are rejected).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Read-only: exit 3 on an off-policy status, an over-cap note or a duplicate id.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without writing any files.",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.check and (args.status or args.note or args.remove):
        parser.error("--check may be combined only with --id")
    if not args.check and (not args.id or args.remove == bool(args.status)):
        parser.error("pass --id with exactly one of --status or --remove, or --check alone")
    if args.remove and args.note is not None:
        parser.error("--note cannot be used with --remove")
    if args.all_matches and not args.remove:
        parser.error("--all-matches needs --remove")

    for label, value in (("--status", args.status), ("--note", args.note)):
        if value and any(ch in value for ch in "\r\n"):
            print(f"ERROR: {label} must not contain newline or carriage return")
            return 2

    status = STATUS_ALIASES.get(args.status, args.status) if args.status else None
    if status is not None and status not in STATUS_VALUES:
        print(
            f"ERROR: --status must be one of {', '.join(STATUS_VALUES)} "
            f"(policy_status_values.md); got {args.status!r}",
            file=sys.stderr,
        )
        return 2
    if args.note is not None and len(args.note) > NOTE_CAP:
        print(f"ERROR: --note is {len(args.note)} characters; the cap is {NOTE_CAP}", file=sys.stderr)
        return 2

    if not _WORK_STATE_PATH.exists():
        print(f"ERROR: work_state.yaml not found at {_WORK_STATE_PATH}", file=sys.stderr)
        return 2

    try:
        return _dispatch(args, status)
    except StateError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


def _dispatch(args: argparse.Namespace, status: Optional[str]) -> int:
    if args.check:
        return _check_file(args.id)

    if args.dry_run:
        print("[DRY-RUN MODE] No files will be written.\n")

    if args.remove:
        return _remove_entries(args.id, args.all_matches, args.dry_run)

    found = _update_work_state(
        artifact_id=args.id,
        new_status=status,
        note=args.note,
        dry_run=args.dry_run,
    )

    if not found:
        print(
            f"ERROR: artifact id {args.id!r} not found in {_WORK_STATE_PATH}",
            file=sys.stderr,
        )
        return 1

    if args.dry_run:
        print("\n[DRY-RUN] Done. No files written.")
    else:
        print("\nDone. work_state.yaml only; update the bundle README Status checklist by hand.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
