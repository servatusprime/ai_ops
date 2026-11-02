#!/usr/bin/env python
"""Run the HEAD copy of the closeout receipt validator from pre-commit."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

VALIDATOR = "00_Admin/scripts/validate_closeout_security_receipt.py"
FORCED_PREFIXES = (
    ".ai_ops/workflows/",
    "00_Admin/configs/",
    "00_Admin/policies/",
    "00_Admin/specs/",
    "plugins/",
    ".claude/",
    ".agents/",
    "01_Resources/templates/config/",
)
FORCED_FILES = {"AGENTS.md", "CLAUDE.md", ".pre-commit-config.yaml", "SECURITY.md"}
SECURITY_FILES = {
    "00_Admin/scripts/closeout_security_prepass.py",
    "00_Admin/scripts/validate_closeout_security_receipt.py",
    "00_Admin/scripts/check_outside_writes.py",
    "00_Admin/scripts/hooks/guard_workspace_writes.py",
    "00_Admin/scripts/hooks/validate_closeout_security_head.py",
    "00_Admin/configs/closeout_security_tiers.yaml",
}


def head_text(repo: Path, path: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), "show", f"HEAD:{path}"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        raise SystemExit(result.stderr.decode(errors="replace").strip())
    return result.stdout.decode("utf-8")


def receipt_header(path: Path) -> tuple[str, str] | None:
    text = path.read_text(encoding="utf-8")
    repo = re.search(r"^repo_root:\s*(.+)$", text, re.MULTILINE)
    head = re.search(r"^base_head:\s*([0-9a-f]{40})$", text, re.MULTILINE)
    return (repo.group(1).strip().strip('"\''), head.group(1)) if repo and head else None


def staged_paths(repo: Path) -> set[str]:
    result = subprocess.run(
        ["git", "-C", str(repo), "diff", "--cached", "--name-only", "--no-renames", "--"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        raise SystemExit(result.stderr.strip() or "closeout-security-hook: cannot inspect staged paths")
    return {line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()}


def security_paths(paths: set[str]) -> set[str]:
    return {
        path
        for path in paths
        if path in FORCED_FILES
        or path in SECURITY_FILES
        or any(path.startswith(prefix) for prefix in FORCED_PREFIXES)
    }


def trusted_validator_present(repo: Path) -> bool:
    return subprocess.run(
        ["git", "-C", str(repo), "cat-file", "-e", f"HEAD:{VALIDATOR}"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--staged", action="store_true")
    parser.add_argument("--commit-msg-file", type=Path)
    args = parser.parse_args()
    repo = args.repo_root.resolve()
    receipt = (repo / args.receipt).resolve() if not args.receipt.is_absolute() else args.receipt.resolve()
    protected = security_paths(staged_paths(repo))
    trusted = trusted_validator_present(repo)
    has_trailer = False
    if args.commit_msg_file:
        message = args.commit_msg_file.read_text(encoding="utf-8")
        matches = [line.strip() for line in message.splitlines() if line.strip().startswith("Closeout-Security:")]
        if not matches:
            if protected and trusted:
                print(
                    "closeout-security-hook: staged security-governed paths require "
                    "a Closeout-Security trailer",
                    file=sys.stderr,
                )
                return 1
            print("closeout-security-hook: no trailer; ordinary commit is unchanged")
            return 0
        has_trailer = True
    if not receipt.exists():
        if has_trailer:
            print("closeout-security-hook: trailer present but receipt is missing", file=sys.stderr)
            return 1
        if protected and trusted:
            print(
                "closeout-security-hook: staged security-governed paths require a current receipt",
                file=sys.stderr,
            )
            return 1
        print("closeout-security-hook: no receipt; ordinary commit is unchanged")
        return 0
    header = receipt_header(receipt)
    current_head = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    if not has_trailer and (not header or header != (str(repo), current_head)):
        if protected and trusted:
            print(
                "closeout-security-hook: staged security-governed paths require a current receipt",
                file=sys.stderr,
            )
            return 1
        print("closeout-security-hook: receipt is for another repo or HEAD; ordinary commit is unchanged")
        return 0
    with tempfile.TemporaryDirectory() as tmp:
        validator = Path(tmp) / "validate_closeout_security_receipt.py"
        validator.write_text(head_text(repo, VALIDATOR), encoding="utf-8")
        command = [
            sys.executable,
            str(validator),
            "--repo-root",
            str(repo),
            "--receipt",
            str(receipt),
            "--gate",
            "--staged",
        ]
        if args.commit_msg_file:
            command.extend(["--commit-msg-file", str(args.commit_msg_file)])
        return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
