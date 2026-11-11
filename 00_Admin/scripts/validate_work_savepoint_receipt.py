#!/usr/bin/env python3
"""Validate a hash-bound work-savepoint receipt without mutating the repo."""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from target_paths import resolve_repo_input, resolve_repo_root  # noqa: E402

SCHEMA = Path(__file__).resolve().parents[1] / "configs" / "validator" / "schema_work_savepoint_receipt.yaml"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
SHA40 = re.compile(r"^[0-9a-f]{40}$")


class ReceiptError(ValueError):
    """The savepoint receipt is incomplete or not bound to its target."""


def _repo_relative(repo: Path, raw: str) -> Path:
    normalized = raw.replace("\\", "/").strip()
    candidate = Path(normalized)
    if (
        not normalized
        or normalized.startswith("/")
        or re.match(r"^[A-Za-z]:", normalized)
        or ".." in candidate.parts
    ):
        raise ReceiptError(f"unsafe active_path: {raw!r}")
    path = (repo / candidate).resolve()
    try:
        path.relative_to(repo.resolve())
    except ValueError as exc:
        raise ReceiptError("active_path escapes repo_root") from exc
    return path


def _git_head(repo: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise ReceiptError(f"cannot resolve HEAD: {result.stderr.strip()}")
    return result.stdout.strip()


def validate_receipt(
    receipt_path: Path,
    *,
    repo_root: Path | None = None,
    expected_head: str | None = None,
    expected_branch: str | None = None,
) -> dict[str, Any]:
    value = yaml.safe_load(receipt_path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise ReceiptError("receipt must contain a mapping")
    schema = yaml.safe_load(SCHEMA.read_text(encoding="utf-8")) or {}
    allowed = set(schema.get("properties", {}))
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise ReceiptError("receipt has undeclared fields: " + ", ".join(unknown))
    if value.get("receipt_version") != schema["properties"]["receipt_version"]["const"]:
        raise ReceiptError("receipt_version is unsupported")
    required = schema["required"]
    missing = [key for key in required if key not in value]
    if missing:
        raise ReceiptError("receipt is missing: " + ", ".join(missing))
    text_fields = (
        "repo_root",
        "repo_id",
        "artifact_id",
        "active_path",
        "head",
        "branch",
        "include_set_sha256",
        "future_work",
        "status",
        "created_at",
    )
    for field in text_fields:
        if not isinstance(value[field], str) or not value[field].strip():
            raise ReceiptError(f"{field} must be a non-empty string")
    if not SHA40.fullmatch(value["head"]):
        raise ReceiptError("head must be a 40-character lowercase SHA")
    if expected_head is not None and value["head"] != expected_head:
        raise ReceiptError("receipt HEAD does not match the expected HEAD")
    if expected_branch is not None and value["branch"] != expected_branch:
        raise ReceiptError("receipt branch does not match the expected branch")
    if value["future_work"] not in {
        "not_applicable",
        "linked_only",
        "completion_handoff",
        "registry_sync",
    }:
        raise ReceiptError("future_work is invalid")
    if value["status"] not in {"checkpointed", "published"}:
        raise ReceiptError("status is invalid")
    include = value["include"]
    if not isinstance(include, list) or not include or any(
        not isinstance(item, str)
        or not item.strip()
        or item.replace("\\", "/").startswith("/")
        or re.match(r"^[A-Za-z]:", item.replace("\\", "/"))
        or ".." in Path(item.replace("\\", "/")).parts
        for item in include
    ):
        raise ReceiptError("include must be a non-empty safe path list")
    if include != sorted(set(include)):
        raise ReceiptError("include must be sorted and duplicate-free")
    expected_include_hash = hashlib.sha256("\n".join(include).encode("utf-8")).hexdigest()
    if value["include_set_sha256"] != expected_include_hash or not SHA256.fullmatch(
        value["include_set_sha256"]
    ):
        raise ReceiptError("include_set_sha256 does not bind include")
    try:
        created_at = datetime.fromisoformat(str(value["created_at"]).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ReceiptError("created_at must be ISO-8601") from exc
    if created_at.tzinfo is None:
        raise ReceiptError("created_at must include a timezone")
    if repo_root is not None:
        repo = repo_root.resolve()
        if Path(str(value["repo_root"])).resolve() != repo:
            raise ReceiptError("repo_root does not match the validation target")
        if str(value["repo_id"]) != repo.name:
            raise ReceiptError("repo_id does not match the validation target")
        active = _repo_relative(repo, str(value["active_path"]))
        if not active.exists():
            raise ReceiptError(f"active_path does not exist: {value['active_path']}")
        for include_path in include:
            _repo_relative(repo, include_path)
        if expected_head is None and value["head"] != _git_head(repo):
            raise ReceiptError("receipt HEAD does not match repository HEAD")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--workspace-root", type=Path, help="workspace containing named governed repositories")
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--head", dest="expected_head", required=True)
    parser.add_argument("--branch", dest="expected_branch", required=True)
    args = parser.parse_args()
    try:
        workspace_root = args.workspace_root.resolve() if args.workspace_root else None
        repo_root = resolve_repo_root(
            args.repo_root, workspace_root=workspace_root, cwd=Path.cwd()
        )
        receipt_path = resolve_repo_input(
            args.receipt,
            repo_root,
            workspace_root=workspace_root,
            cwd=Path.cwd(),
        )
        validate_receipt(
            receipt_path,
            repo_root=repo_root,
            expected_head=args.expected_head,
            expected_branch=args.expected_branch,
        )
    except (OSError, UnicodeError, yaml.YAMLError, ReceiptError) as exc:
        print(f"work-savepoint-receipt: {exc}", file=sys.stderr)
        return 2
    print(f"[OK] work savepoint receipt: {args.receipt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
