#!/usr/bin/env python3
"""Resolve ai_ops control arguments consistently across governed repositories.

The workflow scripts are launched from different working directories.  A
relative governed-repository names should therefore be
resolved against the workspace root when they are not present in the caller's
current directory, while paths inside the selected repository remain
repository-relative at the validation boundary.
"""

from __future__ import annotations

import os
from pathlib import Path


def default_workspace_root(script_file: str | Path) -> Path:
    """Return the workspace containing the ai_ops repository."""

    resolved = Path(script_file).resolve()
    try:
        return resolved.parents[3]
    except IndexError as exc:
        raise ValueError(
            f"cannot derive workspace root from script path {resolved}; "
            "the path must have at least four parent levels"
        ) from exc


def _candidate_paths(value: str | Path, workspace_root: Path, cwd: Path | None) -> list[Path]:
    raw = Path(value)
    if raw.is_absolute():
        return [raw]
    current = (cwd or Path.cwd()).resolve()
    workspace = workspace_root.resolve()
    return [current / raw, workspace / raw]


def resolve_repo_root(
    value: str | Path,
    *,
    workspace_root: Path | None = None,
    cwd: Path | None = None,
) -> Path:
    """Resolve a repository argument from the caller or workspace root."""

    raw = Path(value)
    if raw.is_absolute():
        candidates = [raw]
    else:
        workspace = (workspace_root or default_workspace_root(__file__)).resolve()
        candidates = _candidate_paths(raw, workspace, cwd)
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.is_dir() and (resolved / ".git").exists():
            return resolved
    rendered = ", ".join(str(candidate) for candidate in candidates)
    raise ValueError(f"repository root was not found at any accepted location: {rendered}")


def resolve_input_path(
    value: str | Path,
    *,
    workspace_root: Path | None = None,
    cwd: Path | None = None,
    must_exist: bool = True,
) -> Path:
    """Resolve a control input from the caller or workspace root."""

    raw = Path(value)
    if raw.is_absolute():
        candidates = [raw]
    else:
        workspace = (workspace_root or default_workspace_root(__file__)).resolve()
        candidates = _candidate_paths(raw, workspace, cwd)
    if must_exist:
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved.exists():
                return resolved
    else:
        for candidate in candidates:
            if candidate.parent.exists():
                return candidate.resolve()
    return candidates[0].resolve()


def resolve_repo_output(
    value: str | Path,
    repo_root: Path,
    *,
    workspace_root: Path | None = None,
    cwd: Path | None = None,
) -> Path:
    """Resolve an output as repo-relative unless an existing workspace path wins."""

    raw = Path(value)
    if raw.is_absolute():
        return raw.resolve()
    workspace = (workspace_root or default_workspace_root(__file__)).resolve()
    candidates = _candidate_paths(raw, workspace, cwd)
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return (repo_root.resolve() / raw).resolve()


def resolve_repo_input(
    value: str | Path,
    repo_root: Path,
    *,
    workspace_root: Path | None = None,
    cwd: Path | None = None,
) -> Path:
    """Resolve a target-repository input before falling back to its repo path."""

    raw = Path(value)
    if raw.is_absolute():
        return raw.resolve()
    repo_candidate = (repo_root.resolve() / raw).resolve()
    if repo_candidate.exists():
        return repo_candidate
    workspace = (workspace_root or default_workspace_root(__file__)).resolve()
    for candidate in _candidate_paths(raw, workspace, cwd):
        resolved = candidate.resolve()
        if resolved.exists():
            return resolved
    return repo_candidate


def is_within(path: Path, root: Path) -> bool:
    """Return whether path is lexically contained by root."""

    try:
        Path(os.path.abspath(path)).relative_to(Path(os.path.abspath(root)))
    except ValueError:
        return False
    return True
