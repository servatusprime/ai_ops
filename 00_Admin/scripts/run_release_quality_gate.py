#!/usr/bin/env python3
"""Run canonical release-quality validation checks for ai_ops.

Includes the governance test/fixture suites (validator unit tests and the
validator's own fixture harness) so a broken validator is caught by its own
tests before it is trusted to judge the rest of the repo.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Sequence, Tuple

ALLOWED_CHECKS = {
    "governance-tests",
    "validator-fixtures",
    "repo-validator",
    "ci-requirements",
    "metadata-validator",
    "workflow-frontmatter",
    "workflow-export-generation",
    "export-drift",
    "lint-no-fix",
    "profiles-derivative-drift",
}


def _sanitize_child_diagnostics(text: str, cwd: Path) -> str:
    """Show useful child failures while removing machine-specific paths."""

    rendered = text or ""
    root = str(cwd.resolve())
    variants = {root, root.replace("\\", "/"), root.replace("/", "\\")}
    for variant in sorted(variants, key=len, reverse=True):
        rendered = re.sub(
            re.escape(variant) + r"[\\/]",
            "<repo-root>/",
            rendered,
            flags=re.IGNORECASE,
        )
        rendered = re.sub(re.escape(variant), "<repo-root>", rendered, flags=re.IGNORECASE)
    rendered = re.sub(
        r"(?<![\w<>])(?:[A-Za-z]:[\\/]|\\\\)(?:[^\s:()]+[\\/])*[^\s:()]+",
        "<external-path>",
        rendered,
    )
    rendered = re.sub(
        r"(?<![\w<>])/(?!/)(?:[^\s:()]+/)+[^\s:()]+",
        "<external-path>",
        rendered,
    )
    return rendered.replace("\\", "/")[-12000:]


def _safe_console_text(text: str, encoding: str | None = None) -> str:
    """Make diagnostics printable on legacy Windows console encodings."""

    target_encoding = encoding or getattr(sys.stdout, "encoding", None) or "utf-8"
    return text.encode(target_encoding, errors="backslashreplace").decode(target_encoding)


def run_check(name: str, cmd: Sequence[str], cwd: Path, dry_run: bool) -> Tuple[str, int]:
    if name not in ALLOWED_CHECKS:
        print(f"[FAIL] unapproved release check: {name}")
        return name, 1
    if not cwd.is_dir() or any("\x00" in part or "\n" in part or "\r" in part for part in cmd):
        print(f"[FAIL] invalid release check command or cwd for {name}")
        return name, 1
    print(f"[CHECK] {name}")
    print(f"  command: {name} (arguments omitted from logs)")
    if dry_run:
        print("  dry-run: skipped execution")
        return name, 0
    result = subprocess.run(
        cmd,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode:
        diagnostics = "\n".join(
            part for part in ((result.stdout or "").strip(), (result.stderr or "").strip()) if part
        )
        if diagnostics:
            print("  child diagnostics (sanitized):")
            print(_safe_console_text(_sanitize_child_diagnostics(diagnostics, cwd)))
        else:
            print("  child diagnostics unavailable; rerun locally for details")
    return name, int(result.returncode)


def detect_git_root(start: Path) -> Path:
    start = start.resolve()
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


def resolve_trusted_powershell() -> str | None:
    """Return a known PowerShell installation path without PATH resolution."""

    if os.name == "nt":
        candidates = (
            Path(r"C:\Program Files")
            / "PowerShell"
            / "7"
            / "pwsh.exe",
            Path(r"C:\Windows")
            / "System32"
            / "WindowsPowerShell"
            / "v1.0"
            / "powershell.exe",
        )
    else:
        candidates = (
            Path("/usr/bin/pwsh"),
            Path("/usr/local/bin/pwsh"),
            Path("/opt/microsoft/powershell/7/pwsh"),
        )

    for candidate in candidates:
        try:
            resolved = candidate.resolve(strict=True)
        except OSError:
            continue
        if resolved.is_file() and not candidate.is_symlink():
            return str(resolved)
    return None


def resolve_trusted_python_runtime() -> str | None:
    """Return the concrete Python executable used by every gate subprocess."""

    try:
        resolved = Path(sys.executable).resolve(strict=True)
    except OSError:
        return None
    return str(resolved) if resolved.is_file() else None


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run canonical release-quality checks (schema/validator, export drift, "
            "lint, and profile derivative drift checking)."
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
    try:
        structure_root.relative_to(repo_root)
    except ValueError:
        print("[FAIL] detected git root escapes ai_ops repo root")
        return 1
    python_exe = resolve_trusted_python_runtime()
    if python_exe is None:
        print("[FAIL] trusted Python runtime is unavailable")
        return 1
    os.environ["AI_OPS_PYTHON"] = python_exe

    checks: List[Tuple[str, List[str]]] = [
        (
            "governance-tests",
            [
                python_exe,
                "-m",
                "unittest",
                "00_Admin.tests.test_run_family_graph",
                "00_Admin.tests.test_future_work_registry_lifecycle",
                "00_Admin.tests.test_governance_seed_contracts",
                "00_Admin.tests.test_work_savepoint_contract",
                "00_Admin.tests.test_workflow_export_workspace_preview",
                "00_Admin.tests.test_claude_settings_policy",
                "00_Admin.tests.test_release_quality_gate",
                "00_Admin.tests.test_validation_command_policy",
            ],
        ),
        (
            "validator-fixtures",
            [python_exe, "00_Admin/scripts/fixtures/run_validate_repo_rules_fixtures.py"],
        ),
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
            "ci-requirements",
            [python_exe, "00_Admin/scripts/validate_ci_requirements.py"],
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
            "workflow-export-generation",
            [
                python_exe,
                "00_Admin/scripts/generate_workflow_exports.py",
                "--targets",
                "plugin",
                "claude",
                "codex",
            ],
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
        ps = resolve_trusted_powershell()
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

    profile_cmd = [
        python_exe,
        "00_Admin/scripts/regenerate_profiles.py",
        "--check",
        "--tracked-only",
    ]
    if args.profile:
        profile_cmd.extend(["--profile", args.profile])
    if args.model_family:
        profile_cmd.extend(["--model-family", args.model_family])
    checks.append(("profiles-derivative-drift", profile_cmd))

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
