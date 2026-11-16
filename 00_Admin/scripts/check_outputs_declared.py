#!/usr/bin/env python
"""List changed files that a workbook's Outputs table does not declare; never mutates.

Usage:
  python <ai_ops>/00_Admin/scripts/check_outputs_declared.py --workbook <path> [--repo-root <path>]
      [--also <workbook> ...]

Reads the "## Outputs and Target Files" table of the workbook. Every backticked token in the first
column is a declared path, relative to the repo root: an exact file, a folder (with or without a
trailing slash), or a glob (`*` does not cross a folder boundary, `**` does). The workbook files
themselves, and the bundle folder that holds them, count as declared. It compares the declared paths
with the changed files from `git status` (modified, added, deleted, renamed, untracked).

The output is triage input, not a verdict: declare an in-scope file, or explain an out-of-scope one.
Exit 0 when every change is declared, 1 when any is not, 2 when the workbook has no Outputs table or
git cannot be read. Declared paths that did not change are listed for information only. Gitignored
files never appear in `git status`, so they are not checked. Use --repo-root when the workbook lives
in one repo and the work changed another.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

TOKEN = re.compile(r"`([^`]+)`")
SECTION = "## Outputs and Target Files"
BUNDLE_PREFIXES = ("wb_", "wp_", "work_program_")


def declared_paths(workbook_text: str) -> list[str] | None:
    """Return the declared paths, or None when the workbook has no Outputs section."""
    inside = False
    found = False
    paths: list[str] = []
    for line in workbook_text.splitlines():
        if line.startswith("## "):
            inside = line.strip() == SECTION
            found = found or inside
            continue
        if inside and line.lstrip().startswith("|"):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if not cells or set(cells[0]) <= set("-: "):
                continue
            for token in TOKEN.findall(cells[0]):
                token = token.strip().replace("\\", "/")
                if token and not re.fullmatch(r"[*?/]+", token):  # a bare wildcard would declare everything
                    paths.append(token)
    return paths if found else None


def _glob_regex(pattern: str) -> re.Pattern[str]:
    out: list[str] = []
    index = 0
    while index < len(pattern):
        if pattern.startswith("**", index):
            out.append(".*")
            index += 2
        elif pattern[index] == "*":
            out.append("[^/]*")
            index += 1
        elif pattern[index] == "?":
            out.append("[^/]")
            index += 1
        else:
            out.append(re.escape(pattern[index]))
            index += 1
    return re.compile("".join(out))


def covers(declared: str, path: str) -> bool:
    d = declared[2:] if declared.startswith("./") else declared
    if path == d or path.startswith(d.rstrip("/") + "/"):
        return True
    return bool(_glob_regex(d).fullmatch(path))


def parse_porcelain(raw: bytes) -> list[str]:
    """Parse `git status --porcelain=v1 -z` output into changed paths (a rename keeps only the new path)."""
    fields = raw.decode("utf-8", errors="replace").split("\0")
    files: list[str] = []
    index = 0
    while index < len(fields):
        entry = fields[index]
        index += 1
        if len(entry) < 4:
            continue
        if "R" in entry[:2] or "C" in entry[:2]:  # a rename or copy carries its source path as the next field
            index += 1
        files.append(entry[3:])
    return files


def changed_files(repo_root: Path) -> list[str]:
    run = subprocess.run(
        ["git", "-C", str(repo_root), "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        capture_output=True,
    )
    if run.returncode != 0:
        raise OSError(run.stderr.decode("utf-8", errors="replace").strip() or "git status failed")
    return parse_porcelain(run.stdout)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--workbook", required=True)
    parser.add_argument(
        "--also", action="append", default=[], help="another workbook whose outputs also count as declared"
    )
    parser.add_argument("--repo-root", help="defaults to the git root of the workbook's folder")
    args = parser.parse_args(argv)

    workbooks = [Path(name).resolve() for name in [args.workbook, *args.also]]
    declared: list[str] = []
    for workbook in workbooks:
        try:
            found = declared_paths(workbook.read_text(encoding="utf-8"))
        except OSError as exc:
            print(f"Cannot read {workbook}: {exc}")
            return 2
        if found is None:
            print(f"No '{SECTION}' section in {workbook}")
            return 2
        declared.extend(found)

    try:
        if args.repo_root:
            repo_root = Path(args.repo_root).resolve()
        else:
            top = subprocess.run(
                ["git", "-C", str(workbooks[0].parent), "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
            )
            if top.returncode != 0:
                raise OSError(top.stderr.strip() or "not inside a git repository")
            repo_root = Path(top.stdout.strip()).resolve()
        changed = changed_files(repo_root)
    except OSError as exc:
        print(f"Cannot read changed files: {exc}")
        return 2

    for workbook in workbooks:  # the workbook itself, and the bundle folder that holds it, are declared
        try:
            declared.append(workbook.relative_to(repo_root).as_posix())
            if workbook.parent != repo_root and workbook.parent.name.startswith(BUNDLE_PREFIXES):
                declared.append(workbook.parent.relative_to(repo_root).as_posix() + "/")
        except ValueError:
            continue

    undeclared = [path for path in changed if not any(covers(d, path) for d in declared)]
    unchanged = [d for d in declared if not any(covers(d, path) for path in changed)]
    print(f"{len(changed)} changed files; {len(undeclared)} not declared in the Outputs table")
    for path in undeclared:
        print(f"  undeclared: {path}")
    if unchanged:
        print(f"{len(unchanged)} declared paths show no change (information only):")
        for path in unchanged[:10]:
            print(f"  unchanged: {path}")
    return 1 if undeclared else 0


if __name__ == "__main__":
    sys.exit(main())
