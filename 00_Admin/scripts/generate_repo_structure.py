#!/usr/bin/env python3
"""Generate repo structure map for current git root.

Writes:
- <git_root>/repo_structure.txt
- <ai_ops_root>/90_Sandbox/ai_external_context/files/repo_structure_reference.txt
"""

from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path
from typing import Dict, List

EXCLUDES = {
    ".git",
    ".ruff_cache",
    "__pycache__",
    ".mypy_cache",
    ".idea",
    ".vscode",
    "node_modules",
    "99_Trash",
}


def resolve_git_root(script_dir: Path) -> Path:
    try:
        result = subprocess.run(
            ["git", "-C", str(script_dir), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        root = result.stdout.strip()
        if root:
            return Path(root)
    except Exception:
        pass

    # Fallback: scripts -> 00_Admin -> ai_ops (or repo root in split mode).
    return script_dir.parents[1]


def list_tracked_files(root: Path) -> List[str]:
    result = subprocess.run(
        ["git", "-c", "core.quotepath=false", "-C", str(root), "ls-files"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _should_exclude(parts: List[str]) -> bool:
    return any(part in EXCLUDES for part in parts)


def build_tree_from_paths(paths: List[str]) -> str:
    lines = ["."]
    root: Dict[str, object] = {"dirs": {}, "files": set()}

    for rel_path in paths:
        normalized = rel_path.replace("\\", "/").strip("/")
        if not normalized:
            continue
        parts = normalized.split("/")
        if _should_exclude(parts):
            continue

        node = root
        for part in parts[:-1]:
            dirs = node["dirs"]  # type: ignore[index]
            if part not in dirs:
                dirs[part] = {"dirs": {}, "files": set()}  # type: ignore[index]
            node = dirs[part]  # type: ignore[index]
        node["files"].add(parts[-1])  # type: ignore[index]

    def walk(node: Dict[str, object], prefix: str = "") -> None:
        dirs = node["dirs"]  # type: ignore[index]
        files = node["files"]  # type: ignore[index]
        entries: List[tuple[str, bool, Dict[str, object] | None]] = []

        for name in dirs:
            entries.append((name, True, dirs[name]))  # type: ignore[index]
        for name in files:
            entries.append((name, False, None))

        entries.sort(key=lambda item: item[0])
        count = len(entries)
        for idx, (name, is_dir, child) in enumerate(entries):
            last = idx == count - 1
            connector = "+-- " if last else "|-- "
            lines.append(f"{prefix}{connector}{name}{'/' if is_dir else ''}")
            if is_dir and child is not None:
                extension = "    " if last else "|   "
                walk(child, prefix + extension)

    walk(root)
    return "\n".join(lines)


def build_tree_from_filesystem(root: Path) -> str:
    lines = ["."]

    def walk(path: Path, prefix: str = "") -> None:
        entries: list[tuple[str, bool]] = []
        for name in sorted(os.listdir(path)):
            if name in EXCLUDES:
                continue
            full = path / name
            entries.append((name, full.is_dir()))
        count = len(entries)
        for idx, (name, is_dir) in enumerate(entries):
            last = idx == count - 1
            connector = "+-- " if last else "|-- "
            lines.append(f"{prefix}{connector}{name}{'/' if is_dir else ''}")
            if is_dir:
                extension = "    " if last else "|   "
                walk(path / name, prefix + extension)

    walk(root)
    return "\n".join(lines)


def build_tree(root: Path) -> str:
    tracked = list_tracked_files(root)
    if tracked:
        return build_tree_from_paths(tracked)
    return build_tree_from_filesystem(root)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate repo structure map for git root and external context reference.",
    )
    parser.add_argument(
        "--repo-root",
        default="",
        help="Optional repo root to map. Defaults to git root containing this script.",
    )
    parser.add_argument(
        "--reference-path",
        default="",
        help=(
            "Optional explicit output path for repo structure reference. "
            "Defaults to ai_ops/90_Sandbox/ai_external_context/files/repo_structure_reference.txt."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview write targets without modifying files.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    ai_ops_root = script_dir.parents[1]
    if args.repo_root:
        repo_root = Path(args.repo_root).expanduser()
        if not repo_root.is_absolute():
            repo_root = (Path.cwd() / repo_root).resolve()
    else:
        repo_root = resolve_git_root(script_dir)

    target_main = repo_root / "repo_structure.txt"
    if args.reference_path:
        target_reference = Path(args.reference_path).expanduser()
        if not target_reference.is_absolute():
            target_reference = (Path.cwd() / target_reference).resolve()
    else:
        target_reference = (
            ai_ops_root
            / "90_Sandbox"
            / "ai_external_context"
            / "files"
            / "repo_structure_reference.txt"
        )

    if not repo_root.exists() or not repo_root.is_dir():
        print(f"[ERR] repo root does not exist or is not a directory: {repo_root}")
        return 1

    tree = build_tree(repo_root)

    if args.dry_run:
        print(f"[DRY RUN] would write {target_main}")
        print(f"[DRY RUN] would write {target_reference}")
        return 0

    write_text(target_main, tree)
    write_text(target_reference, tree)

    print(f"[OK] wrote {target_main}")
    print(f"[OK] wrote {target_reference}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
