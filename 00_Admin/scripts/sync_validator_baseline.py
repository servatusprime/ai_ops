#!/usr/bin/env python
"""
Sync validator baseline artifacts from ai_ops into one or more governed repos.

Usage:
  python 00_Admin/scripts/sync_validator_baseline.py --targets ../<governed_repo>
  python 00_Admin/scripts/sync_validator_baseline.py --targets ../<governed_repo> --dry-run
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from typing import Iterable, List

BASELINE_FILES = [
    "00_Admin/scripts/validate_repo_rules.py",
    "00_Admin/scripts/run_markdownlint.ps1",
    "00_Admin/configs/validator/validator_config.yaml",
    "00_Admin/runbooks/rb_repo_validator_01.md",
]


def _resolve_target(ai_ops_root: str, target: str) -> str:
    direct = os.path.abspath(os.path.join(ai_ops_root, target))
    if os.path.isdir(direct):
        return direct

    sibling = os.path.abspath(os.path.join(ai_ops_root, "..", target))
    return sibling


def _sync_one(ai_ops_root: str, target_root: str, dry_run: bool) -> List[str]:
    synced: List[str] = []
    for rel_path in BASELINE_FILES:
        src = os.path.join(ai_ops_root, rel_path)
        dst = os.path.join(target_root, rel_path)
        if not os.path.exists(src):
            raise FileNotFoundError(f"missing source artifact: {src}")

        if not dry_run:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
        synced.append(rel_path)
    return synced


def _print_summary(target_root: str, synced: Iterable[str], dry_run: bool) -> None:
    mode = "DRY-RUN" if dry_run else "SYNCED"
    print(f"[{mode}] {target_root}")
    for rel_path in synced:
        print(f"  - {rel_path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--targets",
        nargs="+",
        required=True,
        help="Target repo paths or names (for example ../<governed_repo> or <governed_repo>).",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Path to ai_ops repo root. Defaults to current directory.",
    )
    args = parser.parse_args()

    ai_ops_root = os.path.abspath(args.repo_root)
    failures: List[str] = []

    for target in args.targets:
        target_root = _resolve_target(ai_ops_root, target)
        if not os.path.isdir(target_root):
            failures.append(f"target repo not found: {target} -> {target_root}")
            continue

        try:
            synced = _sync_one(ai_ops_root, target_root, args.dry_run)
            _print_summary(target_root, synced, args.dry_run)
        except OSError as exc:
            failures.append(f"{target_root}: {exc}")

    if failures:
        print("Sync failures:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
