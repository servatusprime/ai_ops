#!/usr/bin/env python3
"""Emit the required machine-readable route metadata for a /work run.

The emitter is deliberately side-effect free: it validates the fields required
by ``context_routing.yaml`` and writes one JSON object to stdout.  The calling
agent or harness owns persistence of the execution output.
"""

from __future__ import annotations

import argparse
import json
from typing import Sequence

BOOTSTRAP_PATHS = ("fresh_bootstrap", "recenter")


def _non_empty(value: str, name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{name} must be non-empty")
    if any(char in normalized for char in "\r\n"):
        raise ValueError(f"{name} must not contain a newline")
    return normalized


def _boolean(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise ValueError("context-reset-applied must be true or false")


def build_metadata(
    *,
    bootstrap_path: str,
    resume_basis: str,
    reads_applied: Sequence[str],
    context_reset_applied: str,
    scope_echo: str,
) -> dict[str, object]:
    if bootstrap_path not in BOOTSTRAP_PATHS:
        raise ValueError(f"bootstrap-path must be one of {', '.join(BOOTSTRAP_PATHS)}")
    reads = [_non_empty(read, "reads-applied entry") for read in reads_applied]
    if not reads:
        raise ValueError("at least one reads-applied entry is required")
    return {
        "work_route_metadata": {
            "bootstrap_path": bootstrap_path,
            "resume_basis": _non_empty(resume_basis, "resume-basis"),
            "reads_applied": reads,
            "context_reset_applied": _boolean(context_reset_applied),
            "scope_echo": _non_empty(scope_echo, "scope-echo"),
        }
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Emit validated /work route metadata as JSON on stdout."
    )
    parser.add_argument("--bootstrap-path", required=True, choices=BOOTSTRAP_PATHS)
    parser.add_argument("--resume-basis", required=True)
    parser.add_argument("--reads-applied", action="append", required=True)
    parser.add_argument("--context-reset-applied", required=True)
    parser.add_argument("--scope-echo", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        metadata = build_metadata(
            bootstrap_path=args.bootstrap_path,
            resume_basis=args.resume_basis,
            reads_applied=args.reads_applied,
            context_reset_applied=args.context_reset_applied,
            scope_echo=args.scope_echo,
        )
    except ValueError as exc:
        _parser().error(str(exc))
    print(json.dumps(metadata, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
