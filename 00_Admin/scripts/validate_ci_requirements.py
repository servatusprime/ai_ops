#!/usr/bin/env python3
"""Verify that direct CI dependency pins match the generated hash lockfile."""

from __future__ import annotations

import re
from pathlib import Path

PIN_RE = re.compile(r"^([A-Za-z0-9_.-]+)==([^\s\\]+)")


def read_direct_pins(path: Path) -> dict[str, str]:
    pins: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        match = PIN_RE.match(raw.strip())
        if match:
            pins[match.group(1).lower()] = match.group(2)
    return pins


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    source = root / "requirements-ci.in"
    lockfile = root / "requirements-ci.txt"
    if not source.is_file() or not lockfile.is_file():
        print("[FAIL] CI requirements source or lockfile is missing")
        return 1
    source_pins = read_direct_pins(source)
    lock_pins = read_direct_pins(lockfile)
    mismatches = [
        f"{name} source={version} lockfile={lock_pins.get(name, '<missing>')}"
        for name, version in sorted(source_pins.items())
        if lock_pins.get(name) != version
    ]
    if mismatches:
        print(f"[FAIL] CI requirements direct-pin mismatches: {len(mismatches)}")
        for mismatch in mismatches:
            print(f"  {mismatch}")
        return 1
    print(f"[OK] CI requirements direct pins match ({len(source_pins)} packages)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
