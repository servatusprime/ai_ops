"""Shared lexical reparse-point checks for setup and validation writers."""

from __future__ import annotations

import ctypes
import os
from pathlib import Path

REPARSE_POINT = 0x400


def _normalized_real_path(path: Path) -> str:
    """Return a case-normalized real path for containment comparisons."""

    return os.path.normcase(os.path.realpath(os.path.abspath(os.fspath(path))))


def _is_within(path: Path, root: Path) -> bool:
    """Return true when the resolved path is root or a descendant of root."""

    candidate = _normalized_real_path(path)
    trusted = _normalized_real_path(root)
    try:
        return os.path.commonpath([candidate, trusted]) == trusted
    except ValueError:
        return False


def is_reparse(path: Path) -> bool:
    """Return whether a path is a symlink or Windows reparse point."""

    if os.name == "nt":
        try:
            attributes = ctypes.windll.kernel32.GetFileAttributesW(str(path))
            if attributes != 0xFFFFFFFF:
                return bool(attributes & REPARSE_POINT)
        except (AttributeError, OSError):
            pass
    try:
        info = path.lstat()
    except OSError:
        return False
    return path.is_symlink() or bool(getattr(info, "st_file_attributes", 0) & REPARSE_POINT)


def has_reparse_component(path: Path, root: Path) -> bool:
    """Return whether a lexical path crosses a reparse point under ``root``."""

    candidate = Path(os.path.abspath(os.fspath(path)))
    trusted = Path(os.path.abspath(os.fspath(root)))
    if not _is_within(candidate, trusted):
        return True
    if is_reparse(trusted):
        return True
    # Walk the original lexical spelling so short names, case differences, and
    # link components remain visible to the reparse check.  Containment is
    # decided separately using the resolved spelling above.
    current = Path(candidate.anchor)
    for part in candidate.parts[1:]:
        current = current / part
        if os.path.lexists(os.fspath(current)) and is_reparse(current):
            return True
    return False


def assert_no_reparse_components(
    path: Path,
    root: Path | None = None,
    label: str = "path",
) -> None:
    """Raise when a lexical path or its trusted-root chain crosses a link."""

    lexical = Path(os.path.abspath(os.fspath(path)))
    if root is None:
        current = Path(lexical.anchor)
        parts = lexical.parts[1:]
    else:
        trusted = Path(os.path.abspath(os.fspath(root)))
        if not _is_within(lexical, trusted):
            raise ValueError(f"{label} escapes trusted root: {path}")
        if is_reparse(trusted):
            raise ValueError(f"{label} crosses a symlink/reparse point: {path}")
        current = Path(lexical.anchor)
        parts = lexical.parts[1:]
    for part in parts:
        current = current / part
        if os.path.lexists(os.fspath(current)) and is_reparse(current):
            raise ValueError(f"{label} crosses a symlink/reparse point: {path}")
