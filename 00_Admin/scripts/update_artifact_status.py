#!/usr/bin/env python3
"""Update artifact status in work_state.yaml and workbundle README.

Usage:
  python 00_Admin/scripts/update_artifact_status.py --id <artifact_id> --status <status>
  python 00_Admin/scripts/update_artifact_status.py --id <artifact_id> --status <status> --note "note text"
  python 00_Admin/scripts/update_artifact_status.py --id <artifact_id> --status <status> --dry-run

Reads .ai_ops/local/work_state.yaml, finds the matching artifact by id, and updates
its status and optional note field. If the artifact entry includes a path that
resolves to a workbundle README.md, also updates the status cell in the Status table
for that artifact.

Exit codes:
  0  success (or dry-run success)
  1  artifact not found in work_state.yaml
  2  configuration or I/O error
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any, Optional

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None  # type: ignore


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

_SCRIPT_DIR = Path(__file__).resolve().parent  # 00_Admin/scripts/
_REPO_ROOT = _SCRIPT_DIR.parents[1]            # ai_ops/
_WORKSPACE_ROOT = _REPO_ROOT.parent            # RE_Projects/ (workspace root)

_WORK_STATE_PATH = _REPO_ROOT / ".ai_ops" / "local" / "work_state.yaml"


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
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _dump_yaml(data: Any, path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        yaml.dump(data, fh, default_flow_style=False, allow_unicode=True, sort_keys=False)


# ---------------------------------------------------------------------------
# work_state.yaml update
# ---------------------------------------------------------------------------

def _find_artifact(
    artifacts: list[dict[str, Any]], artifact_id: str
) -> Optional[dict[str, Any]]:
    for entry in artifacts:
        if isinstance(entry, dict) and entry.get("id") == artifact_id:
            return entry
    return None


def _update_work_state(
    artifact_id: str,
    new_status: str,
    note: Optional[str],
    dry_run: bool,
) -> tuple[bool, Optional[str]]:
    """Update work_state.yaml entry. Returns (found, artifact_path_or_None)."""
    if not _WORK_STATE_PATH.exists():
        print(
            f"ERROR: work_state.yaml not found at {_WORK_STATE_PATH}",
            file=sys.stderr,
        )
        return False, None  # caller checks found=False; main() distinguishes via sentinel

    data = _load_yaml(_WORK_STATE_PATH)
    artifacts: list[dict[str, Any]] = (
        data.get("work_context", {}).get("active_artifacts", []) or []
    )

    entry = _find_artifact(artifacts, artifact_id)
    if entry is None:
        return False, None

    artifact_path: Optional[str] = entry.get("path")
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

    return True, artifact_path


# ---------------------------------------------------------------------------
# README Status table update
# ---------------------------------------------------------------------------

def _find_readme(artifact_path: Optional[str]) -> Optional[Path]:
    """Derive workbundle README path from an artifact's work_state path string."""
    if not artifact_path:
        return None

    # artifact_path is repo-relative: "ai_ops/..." or "<other_repo>/..."
    path_str = artifact_path.strip()

    # Try resolving from workspace root
    candidate = _WORKSPACE_ROOT / path_str
    if candidate.exists():
        # If the path IS a README, use it directly
        if candidate.name == "README.md":
            return candidate
        # Otherwise look for README.md in the same directory
        readme = candidate.parent / "README.md"
        if readme.exists():
            return readme

    return None


def _update_readme_status(
    readme_path: Path,
    artifact_id: str,
    new_status: str,
    dry_run: bool,
) -> bool:
    """Update the status cell in the README Status table for artifact_id."""
    content = readme_path.read_text(encoding="utf-8")

    # Find the row containing the artifact id (partial match on workbook filename)
    # Table row format: | `wb_id.md` | Status | Notes |
    # We match any row that contains the artifact_id (with or without .md)
    pattern = re.compile(
        r"(\|\s*`?" + re.escape(artifact_id) + r"(?:\.md)?`?\s*\|)([^|]+)(\|.*)",
        re.IGNORECASE,
    )
    match = pattern.search(content)
    if not match:
        print(
            f"  README: row for {artifact_id!r} not found in {readme_path}; skipping.",
            file=sys.stderr,
        )
        return False

    old_status_cell = match.group(2).strip()
    new_row = match.group(1) + f" {new_status} " + match.group(3)
    new_content = content[: match.start()] + new_row + content[match.end():]

    mode = "[DRY-RUN] " if dry_run else ""
    print(f"{mode}README: {readme_path.relative_to(_WORKSPACE_ROOT)}")
    print(f"  status cell: {old_status_cell!r} -> {new_status!r}")

    if not dry_run:
        readme_path.write_text(new_content, encoding="utf-8", newline="\n") # type: ignore[call-arg]

    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Update artifact status in work_state.yaml and workbundle README.\n\n"
            "Reads .ai_ops/local/work_state.yaml, finds the artifact by --id, "
            "and updates its status (and optional note). If the artifact entry "
            "includes a path to a workbundle README.md, also updates the status "
            "row in that README's Status table."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--id",
        required=True,
        metavar="ARTIFACT_ID",
        help=(
            "Artifact id to update (must match 'id' field in work_state.yaml). "
            "To update a specific workbook row in a bundle README, pass the workbook "
            "filename (e.g., 'wb_02_state_sync_friction.md'), not the bundle id."
        ),
    )
    parser.add_argument(
        "--status",
        required=True,
        metavar="STATUS",
        help="New status value (e.g. active, completed, planned, blocked).",
    )
    parser.add_argument(
        "--note",
        default=None,
        metavar="NOTE",
        help="Optional note to set on the artifact entry.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without writing any files.",
    )
    parser.add_argument(
        "--no-readme",
        action="store_true",
        help="Skip README status table update even if README is found.",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if args.dry_run:
        print("[DRY-RUN MODE] No files will be written.\n")

    if not _WORK_STATE_PATH.exists():
        # Error already printed inside _update_work_state; exit 2 = config/I-O error
        return 2

    found, artifact_path = _update_work_state(
        artifact_id=args.id,
        new_status=args.status,
        note=args.note,
        dry_run=args.dry_run,
    )

    if not found:
        print(
            f"ERROR: artifact id {args.id!r} not found in {_WORK_STATE_PATH}",
            file=sys.stderr,
        )
        return 1

    if not args.no_readme:
        readme_path = _find_readme(artifact_path)
        if readme_path:
            _update_readme_status(
                readme_path=readme_path,
                artifact_id=args.id,
                new_status=args.status,
                dry_run=args.dry_run,
            )
        else:
            print(
                "  README: no workbundle README found for this artifact; skipping.",
            )

    print("\nDone." if not args.dry_run else "\n[DRY-RUN] Done. No files written.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
