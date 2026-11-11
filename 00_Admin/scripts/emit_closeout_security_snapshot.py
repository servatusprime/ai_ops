#!/usr/bin/env python3
"""Serialize an independently authored T2 review manifest.

The evidence manifest is supplied by the independent reviewer.  This tool
only validates that manifest against the frozen receipt and writes the
HEAD-bound snapshot consumed by the receipt updater and validator.  It never
assigns a reviewer, disposition, or security finding.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, NoReturn

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment diagnostic
    raise SystemExit("PyYAML is required; install it before emitting a snapshot") from exc

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
import validate_closeout_security_receipt as validator  # noqa: E402
from target_paths import is_within, resolve_repo_input, resolve_repo_output, resolve_repo_root  # noqa: E402


def fail(message: str) -> NoReturn:
    raise SystemExit(f"emit-closeout-security-snapshot: {message}")


def load_mapping(path: Path, label: str) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        fail(f"cannot read {label}: {exc}")
    if not isinstance(value, dict):
        fail(f"{label} must contain a mapping")
    return value


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def build_snapshot(receipt: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    if receipt.get("receipt_version") != "0.2.0":
        fail("snapshot emission requires a v0.2.0 reviewer-read receipt")
    validator.validate_shape(receipt)
    independent_reviewer = evidence.get("independent_reviewer")
    if not isinstance(independent_reviewer, str) or independent_reviewer.strip() in {"", "pending"}:
        fail("evidence-file.independent_reviewer must identify the independent reviewer")
    independent_reviewer = independent_reviewer.strip()
    target_rows = {
        str(row["path"]): row
        for row in receipt["rows"]
        if isinstance(row, dict) and row.get("tier") == "T2"
    }
    if not target_rows:
        fail("receipt has no T2 rows requiring an independent snapshot")
    evidence_rows = evidence.get("rows")
    if not isinstance(evidence_rows, list) or not evidence_rows:
        fail("evidence-file.rows must be a non-empty list")
    supplied: dict[str, dict[str, Any]] = {}
    for item in evidence_rows:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            fail("each evidence-file row needs a path")
        path = validator.safe_path(item["path"])
        if path in supplied:
            fail(f"duplicate evidence row: {path}")
        supplied[path] = item
    if set(supplied) != set(target_rows):
        missing = sorted(set(target_rows) - set(supplied))
        extra = sorted(set(supplied) - set(target_rows))
        fail(f"evidence rows must exactly cover T2 receipt rows; missing={missing}; extra={extra}")

    snapshot_rows: list[dict[str, Any]] = []
    for path, receipt_row in target_rows.items():
        item = supplied[path]
        if independent_reviewer == str(receipt_row.get("reviewer")):
            fail(f"independent reviewer must differ from primary reviewer: {path}")
        if item.get("sha256") != receipt_row.get("sha256"):
            fail(f"evidence sha256 does not match receipt: {path}")
        if item.get("mode") != receipt_row.get("mode"):
            fail(f"evidence mode does not match receipt: {path}")
        if item.get("reviewer") != independent_reviewer:
            fail(f"evidence reviewer does not match independent_reviewer: {path}")
        if item.get("disposition") != "pass":
            fail(f"independent evidence disposition must be pass: {path}")
        notes = item.get("review_notes")
        if not isinstance(notes, str) or not notes.strip():
            fail(f"independent evidence needs review_notes: {path}")
        snapshot_rows.append(
            {
                "path": path,
                "sha256": receipt_row["sha256"],
                "mode": receipt_row["mode"],
                "reviewer": independent_reviewer,
                "disposition": "pass",
                "review_notes": notes.strip(),
            }
        )
    return {
        "snapshot_version": "1.0.0",
        "repo_root": receipt["repo_root"],
        "base_head": receipt["base_head"],
        "scope_lock_sha256": receipt["scope_lock_sha256"],
        "independent_reviewer": independent_reviewer,
        "rows": snapshot_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--evidence-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--workspace-root", type=Path)
    args = parser.parse_args()
    workspace_root = args.workspace_root.resolve() if args.workspace_root else None
    try:
        repo = resolve_repo_root(args.repo_root, workspace_root=workspace_root, cwd=Path.cwd())
    except ValueError as exc:
        fail(str(exc))
    receipt_path = resolve_repo_input(args.receipt, repo, workspace_root=workspace_root, cwd=Path.cwd())
    evidence_path = resolve_repo_input(args.evidence_file, repo, workspace_root=workspace_root, cwd=Path.cwd())
    output_path = resolve_repo_output(args.output, repo, workspace_root=workspace_root, cwd=Path.cwd())
    if not receipt_path.is_file() or not evidence_path.is_file():
        fail("receipt and evidence-file must exist")
    if not is_within(output_path, repo):
        fail("output must be inside the target repository")
    if output_path.resolve() in {receipt_path.resolve(), evidence_path.resolve()}:
        fail("output must not overwrite the receipt or evidence-file")
    receipt = load_mapping(receipt_path, "receipt")
    evidence = load_mapping(evidence_path, "evidence-file")
    snapshot = build_snapshot(receipt, evidence)
    payload = yaml.safe_dump(snapshot, sort_keys=False).encode("utf-8")
    atomic_write(output_path, payload)
    print(f"WROTE {output_path}")
    print(f"evidence_sha256={hashlib.sha256(payload).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
