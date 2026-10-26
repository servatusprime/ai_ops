#!/usr/bin/env python3
"""Fail closed when setup destinations cross symlinks or reparse points.

This helper is called by the legacy shell/batch setup surfaces before they
create or copy generated agent files. The Python exporter performs the same
check immediately before its own writes.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from path_safety import assert_no_reparse_components  # noqa: E402


def assert_safe(path: Path, label: str) -> None:
    assert_no_reparse_components(path, label=label)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", action="append", required=True)
    args = parser.parse_args()
    for raw_path in args.path:
        path = Path(raw_path)
        assert_safe(path, "setup destination")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print(f"[BLOCKED] {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
