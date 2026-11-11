#!/usr/bin/env python3
"""Apply bounded reviewer attestations to a closeout receipt.

This replaces ad-hoc receipt editing and attaches the independently emitted
snapshot without allowing it to broaden the scope. The update file is
intentionally narrow: it may only change reviewer attestation fields for
already-scoped rows. Repository bytes, scope, and pre-pass findings remain
controlled by the pre-pass and validator.
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
    raise SystemExit("PyYAML is required; install it before recording review state") from exc

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
import validate_closeout_security_receipt as validator  # noqa: E402
from target_paths import resolve_repo_input, resolve_repo_root  # noqa: E402

ALLOWED_ROW_FIELDS = {
    "coverage",
    "reviewer",
    "reviewer_model",
    "reviewer_runtime",
    "review_method",
    "independent_pass",
    "independent_reviewer",
    "independent_evidence",
    "disposition",
    "coverage_notes",
    "finding_refs",
}


def fail(message: str) -> "NoReturn":
    raise SystemExit(f"record-closeout-security-review: {message}")


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


def load_mapping(path: Path, label: str) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        fail(f"cannot read {label}: {exc}")
    if not isinstance(value, dict):
        fail(f"{label} must contain a mapping")
    return value


def canonical_receipt(receipt: dict[str, Any]) -> bytes:
    return validator.canonical_receipt(receipt)


def relative_repo_path(repo: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        fail(f"path must be inside the target repository: {path}")


def validate_snapshot(
    repo: Path, receipt: dict[str, Any], snapshot_path: Path, touched: set[str]
) -> str:
    """Attach an existing independent artifact; never manufacture one here."""

    try:
        payload = snapshot_path.read_bytes()
    except OSError as exc:
        fail(f"cannot read independent snapshot: {exc}")
    value = load_mapping(snapshot_path, "independent snapshot")
    if value.get("snapshot_version") != "1.0.0":
        fail("independent snapshot must declare snapshot_version=1.0.0")
    if value.get("repo_root") != receipt.get("repo_root"):
        fail("independent snapshot repo_root does not match receipt")
    if value.get("base_head") != receipt.get("base_head"):
        fail("independent snapshot base_head does not match receipt")
    if value.get("scope_lock_sha256") != receipt.get("scope_lock_sha256"):
        fail("independent snapshot scope lock does not match receipt")
    snapshot_rows = {
        str(row.get("path")): row
        for row in value.get("rows", [])
        if isinstance(row, dict) and row.get("path")
    }
    for path in touched:
        row = next(item for item in receipt["rows"] if item["path"] == path)
        if row.get("tier") != "T2" or row.get("independent_pass") is not True:
            continue
        independent_reviewer = str(row.get("independent_reviewer", "pending"))
        if independent_reviewer in {"", "pending", str(row.get("reviewer"))}:
            fail(f"T2 row lacks a distinct independent reviewer: {path}")
        snapshot_row = snapshot_rows.get(path)
        if not isinstance(snapshot_row, dict):
            fail(f"independent snapshot does not cover T2 row: {path}")
        for key in ("sha256", "mode", "disposition"):
            if snapshot_row.get(key) != row.get(key):
                fail(f"independent snapshot {key} mismatch: {path}")
        if snapshot_row.get("reviewer") != independent_reviewer:
            fail(f"independent snapshot reviewer mismatch: {path}")
        if snapshot_row.get("disposition") != "pass":
            fail(f"independent snapshot disposition is not pass: {path}")
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--updates-file", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--workspace-root", type=Path)
    args = parser.parse_args()

    workspace_root = args.workspace_root.resolve() if args.workspace_root else None
    try:
        repo = resolve_repo_root(args.repo_root, workspace_root=workspace_root, cwd=Path.cwd())
    except ValueError as exc:
        fail(str(exc))
    receipt_path = resolve_repo_input(
        args.receipt, repo, workspace_root=workspace_root, cwd=Path.cwd()
    )
    updates_path = resolve_repo_input(
        args.updates_file, repo, workspace_root=workspace_root, cwd=Path.cwd()
    )
    if not receipt_path.is_file() or not updates_path.is_file():
        fail("receipt and updates-file must exist")
    receipt = load_mapping(receipt_path, "receipt")
    updates = load_mapping(updates_path, "updates-file")
    if receipt.get("receipt_version") != "0.2.0":
        fail("review updates are supported only for v0.2.0 reviewer-read receipts")
    validator.validate_shape(receipt)
    update_rows = updates.get("rows")
    if not isinstance(update_rows, list) or not update_rows:
        fail("updates-file.rows must be a non-empty list")
    rows_by_path = {str(row["path"]): row for row in receipt["rows"]}
    touched: set[str] = set()
    for update in update_rows:
        if not isinstance(update, dict) or not isinstance(update.get("path"), str):
            fail("each updates-file row needs a path")
        path = validator.safe_path(update["path"])
        if path in touched:
            fail(f"duplicate update row: {path}")
        touched.add(path)
        row = rows_by_path.get(path)
        if row is None:
            fail(f"updates-file row is outside the frozen receipt scope: {path}")
        unknown = set(update) - {"path"} - ALLOWED_ROW_FIELDS
        if unknown:
            fail(f"unsupported reviewer update fields for {path}: {', '.join(sorted(unknown))}")
        for key in ALLOWED_ROW_FIELDS & set(update):
            row[key] = update[key]

    if args.snapshot:
        snapshot_path = resolve_repo_input(
            args.snapshot, repo, workspace_root=workspace_root, cwd=Path.cwd()
        )
        snapshot_rel = relative_repo_path(repo, snapshot_path)
        snapshot_hash = validate_snapshot(repo, receipt, snapshot_path, touched)
        for path in touched:
            row = rows_by_path[path]
            if row.get("tier") == "T2" and row.get("independent_pass") is True:
                reviewer = str(row.get("independent_reviewer", "pending"))
                if reviewer not in {"", "pending", str(row.get("reviewer"))}:
                    row["independent_evidence"] = (
                        f"snapshot={snapshot_rel}; evidence_sha256={snapshot_hash}"
                    )

    validator.validate_shape(receipt)
    receipt.pop("receipt_sha256", None)
    receipt["receipt_sha256"] = hashlib.sha256(canonical_receipt(receipt)).hexdigest()
    atomic_write(
        receipt_path,
        yaml.safe_dump(receipt, sort_keys=False).encode("utf-8"),
    )
    print(f"UPDATED {len(touched)} reviewer rows in {receipt_path}")
    if args.snapshot:
        print(f"SNAPSHOT {relative_repo_path(repo, snapshot_path)}")
    print(f"receipt_sha256={receipt['receipt_sha256']}")
    return 0


if __name__ == "__main__":
    main()
