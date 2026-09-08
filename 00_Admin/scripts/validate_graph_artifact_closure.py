#!/usr/bin/env python
"""Compatibility entry point for the canonical run-family closure check."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validate_run_family_graph import (  # noqa: E402
    discover_manifests,
    validate_graph_artifact_closure,
)

validate_closure = validate_graph_artifact_closure


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--artifact", action="append", default=[])
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manifests = discover_manifests(args.repo_root)
    findings = validate_graph_artifact_closure(
        args.repo_root,
        manifests,
        artifact_ids=set(args.artifact) if args.artifact else None,
    )
    if findings:
        print(f"FAIL: unsatisfied graph inputs ({len(findings)}):", file=sys.stderr)
        for finding in findings:
            print(f"- {finding}", file=sys.stderr)
        return 1
    print("PASS: graph artifact closure is executable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
