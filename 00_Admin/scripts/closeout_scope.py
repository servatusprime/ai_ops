#!/usr/bin/env python3
"""Report closeout scope against HEAD, a projected include tree, and dirty state.

This command is read-only.  It never stages or rewrites files.  Validators can
use the report to run against the projected include set, or stop with an
explicit ``excluded_scope_conflict`` when a validator input is outside that
set.  Excluded files are never added to make validation pass.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Iterable

import build_closeout_packet as packet_builder


class ScopeError(RuntimeError):
    """The requested scope cannot be projected safely."""


def _safe_path(value: str) -> str:
    normalized = value.replace("\\", "/").strip()
    candidate = Path(normalized)
    if (
        not normalized
        or normalized.startswith("/")
        or re.match(r"^[A-Za-z]:", normalized)
        or ".." in candidate.parts
        or normalized.endswith("/")
    ):
        raise ScopeError(f"unsafe repository-relative path: {value!r}")
    return normalized


def _paths(repo: Path, *, ignored: bool) -> set[str]:
    command = [
        "git",
        "-C",
        str(repo),
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
    ]
    if ignored:
        command.append("--ignored=matching")
    completed = subprocess.run(command, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if completed.returncode:
        raise ScopeError(completed.stderr.decode("utf-8", "replace").strip())
    result: set[str] = set()
    for record in completed.stdout.split(b"\0"):
        if not record:
            continue
        if len(record) < 4:
            raise ScopeError(f"malformed git status record: {record!r}")
        status = record[:2].decode("ascii", "replace")
        if "R" in status or "C" in status:
            raise ScopeError("rename/copy status requires a new scope")
        if ignored and status != "!!":
            continue
        raw_path = record[3:].decode("utf-8")
        # Git marks ignored directories with a trailing slash when using
        # --ignored=matching. Normalize that status-only marker here; keep
        # _safe_path strict for caller-supplied include/related/validator
        # paths, where a trailing slash is still unsafe and rejected.
        if ignored:
            raw_path = raw_path.rstrip("/\\")
        result.add(_safe_path(raw_path))
    return result


def _head(repo: Path) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode:
        raise ScopeError(completed.stderr.strip())
    return completed.stdout.strip()


def scope_report(
    repo: Path,
    include: Iterable[str],
    *,
    related_scope_requires_confirmation: Iterable[str] = (),
    validator_inputs: Iterable[str] = (),
) -> dict[str, Any]:
    """Return the four-bucket scope and projected-tree validation decision."""

    repo = repo.resolve()
    include_set = {_safe_path(path) for path in include}
    if not include_set:
        raise ScopeError("at least one include path is required")
    related = {_safe_path(path) for path in related_scope_requires_confirmation}
    validator_paths = {_safe_path(path) for path in validator_inputs}
    if include_set & related:
        raise ScopeError("a path cannot be both include and related scope")

    dirty = _paths(repo, ignored=False)
    ignored = _paths(repo, ignored=True)
    missing_include = sorted(include_set - dirty)
    if missing_include:
        raise ScopeError("include paths are not dirty: " + ", ".join(missing_include))

    changes, projected_tree, _observed = packet_builder.projection(repo, sorted(include_set))
    del changes
    excluded = sorted(dirty - include_set - related)
    conflicts = sorted(validator_paths & (set(excluded) | ignored))
    status = "excluded_scope_conflict" if conflicts else "projected_tree_ready"
    return {
        "status": status,
        "current_head": _head(repo),
        "validation_tree": "projected_include_tree",
        "projected_include_tree": {
            "paths": sorted(include_set),
            "sha256": packet_builder.sha256_bytes(packet_builder._canonical_bytes(projected_tree)),
        },
        "dirty_worktree": {
            "include": sorted(include_set),
            "related_scope_requires_confirmation": sorted(related),
            "exclude": excluded,
            "ignored_unpublished": sorted(ignored),
        },
        "validator_inputs": sorted(validator_paths),
        "excluded_scope_conflict": {
            "paths": conflicts,
            "reason": "validator input changed outside the approved include tree",
        }
        if conflicts
        else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--include", action="append", required=True)
    parser.add_argument("--related", action="append", default=[])
    parser.add_argument("--validator-input", action="append", default=[])
    args = parser.parse_args()
    try:
        report = scope_report(
            args.repo_root,
            args.include,
            related_scope_requires_confirmation=args.related,
            validator_inputs=args.validator_input,
        )
    except (OSError, ScopeError, packet_builder.PacketError) as exc:
        print(f"closeout-scope: {exc}")
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
