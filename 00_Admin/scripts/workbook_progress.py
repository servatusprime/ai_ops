#!/usr/bin/env python
"""Print tasks-ticked progress per phase for one or more workbooks; computed, never stored.

Usage:
  python <ai_ops>/00_Admin/scripts/workbook_progress.py <workbook.md> [<workbook.md> ...]

Reads the "## Ordered Execution Queue" section of each workbook. Under each "### " heading it
counts the top-level checkbox items (`- [ ]`, `- [x]`, `- [~]`, `- [-]` or `- [!]`, or the same with `*`,
at column 0; only `x` counts as ticked) and prints ticked/total with a percentage (rounded down, so 100%
means every task is ticked) and a ten-step bar. It is an approximation: phases differ in size, and a
deferred task stays unticked. Headings and boxes inside code fences are ignored. A bundle gets one
block per workbook and no combined figure. The Completion phase counts, so 100% means the workbook
is accepted, not only executed. Exit 0, or 2 when a workbook has
no Ordered Execution Queue section. Writes nothing.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SECTION = "## Ordered Execution Queue"
HEADING = re.compile(r"^## Ordered Execution Queue\s*$")
FENCE = re.compile(r"^\s*(```|~~~)")
ITEM = re.compile(r"^[-*] \[([ xX~!-])\] ")


def percent(done: int, total: int) -> int:
    """Whole percent rounded down, so 100 means every task is ticked."""
    return 100 * done // total if total else 0


def phases(workbook_text: str) -> list[tuple[str, int, int]] | None:
    """Return (phase name, ticked, total) per `###` heading in the queue, or None without a queue."""
    rows: list[list] = []
    found = in_queue = fenced = False
    for line in workbook_text.splitlines():
        if FENCE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        if line.startswith("## "):
            if in_queue:
                break
            if HEADING.match(line):
                found = in_queue = True
            continue
        if not in_queue:
            continue
        if line.startswith("### "):
            name = re.sub(r"\s*\([^()]*\)\s*$", "", line[4:].strip())  # drop a trailing "(Agent -- Level n)"
            rows.append([name, 0, 0])
            continue
        match = ITEM.match(line)
        if match:
            if not rows:
                rows.append(["Queue", 0, 0])
            rows[-1][2] += 1
            rows[-1][1] += match.group(1) in "xX"
    return [(name, done, total) for name, done, total in rows] if found else None


def title(workbook_text: str, path: Path) -> str:
    match = re.search(r"^id:\s*(\S+)", workbook_text, flags=re.MULTILINE)
    return match.group(1) if match else path.stem


def bar(percent: int) -> str:
    filled = percent // 10
    return "#" * filled + "." * (10 - filled)


def render(name: str, rows: list[tuple[str, int, int]]) -> str:
    lines = [f"{name}  (tasks ticked; an approximation)"]
    done_all = sum(done for _, done, _ in rows)
    total_all = sum(total for _, _, total in rows)
    for phase, done, total in rows:
        share = percent(done, total)
        count = f"{done}/{total}" if total else "no tasks"
        lines.append(f"  {phase[:52]:52} {count:>8} {share:>4}%  {bar(share)}")
    share_all = percent(done_all, total_all)
    lines.append(f"  {'All phases':52} {f'{done_all}/{total_all}':>8} {share_all:>4}%  {bar(share_all)}")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__.split("\n\n")[0] + "\n" + __doc__.split("\n\n")[1])
        return 0
    status = 0
    blocks: list[str] = []
    for name in argv:
        path = Path(name)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            blocks.append(f"{path.name}: cannot read ({exc.__class__.__name__})")
            status = 2
            continue
        rows = phases(text)
        if rows is None:
            blocks.append(f"{path.name}: no '{SECTION}' section")
            status = 2
            continue
        blocks.append(render(title(text, path), rows))
    print("\n\n".join(blocks))
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
