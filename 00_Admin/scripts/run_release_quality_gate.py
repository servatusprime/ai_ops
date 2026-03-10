#!/usr/bin/env python3
"""Run canonical release-quality validation checks for ai_ops."""

from __future__ import annotations

import argparse
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Sequence, Tuple


def format_cmd(parts: Sequence[str]) -> str:
    return " ".join(shlex.quote(p) for p in parts)


def run_check(name: str, cmd: Sequence[str], cwd: Path, dry_run: bool) -> Tuple[str, int]:
    print(f"[CHECK] {name}")
    print(f"  {format_cmd(cmd)}")
    if dry_run:
        print("  dry-run: skipped execution")
        return name, 0
    result = subprocess.run(cmd, cwd=cwd, check=False)
    return name, int(result.returncode)


def detect_git_root(start: Path) -> Path:
    try:
        result = subprocess.run(
            ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        top = result.stdout.strip()
        if top:
            return Path(top)
    except Exception:
        pass
    return start


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run canonical release-quality checks (schema/validator, export drift, "
            "lint, and profile regeneration dry-run)."
        )
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print check commands without executing them.",
    )
    parser.add_argument(
        "--skip-lint",
        action="store_true",
        help="Skip lint.ps1 execution (not recommended).",
    )
    parser.add_argument(
        "--repo-validator-advisory",
        action="store_true",
        help="Run repo-validator but do not fail the gate when it exits non-zero.",
    )
    parser.add_argument(
        "--profile",
        help="Optional profile source path passed through to regenerate_profiles.py.",
    )
    parser.add_argument(
        "--model-family",
        help="Optional model family passed through to regenerate_profiles.py.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    structure_root = detect_git_root(repo_root)
    python_exe = sys.executable

    checks: List[Tuple[str, List[str]]] = [
        (
            "repo-validator",
            [
                python_exe,
                "00_Admin/scripts/validate_repo_rules.py",
                "--structure-root",
                str(structure_root),
            ],
        ),
        (
            "metadata-validator",
            [python_exe, "00_Admin/scripts/validate_metadata.py"],
        ),
        (
            "workflow-frontmatter",
            [python_exe, "00_Admin/scripts/validate_workflow_frontmatter.py"],
        ),
        (
            "export-drift",
            [
                python_exe,
                "00_Admin/scripts/check_workflow_exports_drift.py",
                "--strict",
                "--require-manifest",
            ],
        ),
    ]

    if not args.skip_lint:
        ps = shutil.which("pwsh") or shutil.which("powershell")
        if ps is None:
            print("[FAIL] PowerShell is required for lint check (`00_Admin/scripts/lint.ps1`).")
            print("Use `--skip-lint` only when shell limitations are documented.")
            return 1
        checks.append(
            (
                "lint-no-fix",
                [ps, "-File", "00_Admin/scripts/lint.ps1", "-NoFix"],
            )
        )

    profile_cmd = [python_exe, "00_Admin/scripts/regenerate_profiles.py", "--dry-run"]
    if args.profile:
        profile_cmd.extend(["--profile", args.profile])
    if args.model_family:
        profile_cmd.extend(["--model-family", args.model_family])
    checks.append(("profiles-dry-run", profile_cmd))

    failures: List[Tuple[str, int]] = []
    for name, cmd in checks:
        _, rc = run_check(name, cmd, cwd=repo_root, dry_run=args.dry_run)
        if rc != 0:
            if args.repo_validator_advisory and name == "repo-validator":
                print(f"[WARN] {name} exited with code {rc} (advisory mode)")
                continue
            failures.append((name, rc))
            if not args.dry_run:
                print(f"[FAIL] {name} exited with code {rc}")
                break

    if failures:
        print("\n[RESULT] release-quality gate: FAIL")
        for name, rc in failures:
            print(f"- {name}: exit {rc}")
        return 1

    print("\n[RESULT] release-quality gate: PASS")
    if args.dry_run:
        print("No commands executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
