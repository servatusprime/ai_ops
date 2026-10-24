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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--staged", action="store_true")
    parser.add_argument("--commit-msg-file", type=Path)
    args = parser.parse_args()
    repo = args.repo_root.resolve()
    receipt = (repo / args.receipt).resolve() if not args.receipt.is_absolute() else args.receipt.resolve()
    has_trailer = False
    if args.commit_msg_file:
        message = args.commit_msg_file.read_text(encoding="utf-8")
        matches = [line.strip() for line in message.splitlines() if line.strip().startswith("Closeout-Security:")]
        if not matches:
            print("closeout-security-hook: no trailer; ordinary commit is unchanged")
            return 0
        has_trailer = True
    if not receipt.exists():
        if has_trailer:
            print("closeout-security-hook: trailer present but receipt is missing", file=sys.stderr)
            return 1
        print("closeout-security-hook: no receipt; ordinary commit is unchanged")
        return 0
    header = receipt_header(receipt)
    current_head = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    if not has_trailer and (not header or header != (str(repo), current_head)):
        print("closeout-security-hook: receipt is for another repo or HEAD; ordinary commit is unchanged")
        return 0
    with tempfile.TemporaryDirectory(dir=repo / "tmp") as tmp:
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
