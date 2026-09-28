#!/usr/bin/env python3
"""Package ai_ops skills into a Cowork .plugin file."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import tempfile
import zipfile

MAX_SKILL_BYTES = 2 * 1024 * 1024
REPARSE_POINT = 0x400


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skills-root", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def _is_reparse(path: pathlib.Path) -> bool:
    try:
        info = path.lstat()
    except OSError:
        return False
    return path.is_symlink() or bool(getattr(info, "st_file_attributes", 0) & REPARSE_POINT)


def _assert_no_reparse_components(path: pathlib.Path, root: pathlib.Path, label: str) -> None:
    """Inspect lexical components so resolving a link cannot hide its parent."""
    trusted = pathlib.Path(os.path.abspath(os.fspath(root)))
    lexical = pathlib.Path(os.path.abspath(os.fspath(path)))
    try:
        relative = lexical.relative_to(trusted)
    except ValueError as exc:
        raise ValueError(f"{label} escapes workspace root: {path}") from exc
    current = trusted
    for part in relative.parts:
        current = current / part
        if current.exists() and _is_reparse(current):
            raise ValueError(f"{label} crosses a symlink/reparse point: {path}")


def _inside(path: pathlib.Path, root: pathlib.Path, *, label: str, must_exist: bool = True) -> pathlib.Path:
    if path.exists() and _is_reparse(path):
        raise ValueError(f"{label} is a symlink/reparse point: {path}")
    resolved = path.resolve(strict=False)
    trusted = root.resolve(strict=True)
    try:
        resolved.relative_to(trusted)
    except ValueError as exc:
        raise ValueError(f"{label} escapes workspace root: {path}") from exc
    if must_exist and not resolved.exists():
        raise ValueError(f"{label} does not exist: {path}")
    _assert_no_reparse_components(path, trusted, label)
    return resolved


def main() -> int:
    args = parse_args()
    workspace_root = pathlib.Path(__file__).resolve().parents[3]
    try:
        skills_root = _inside(pathlib.Path(args.skills_root), workspace_root, label="skills root")
        manifest_path = _inside(pathlib.Path(args.manifest), workspace_root, label="manifest")
        output_path = _inside(
            pathlib.Path(args.output), workspace_root, label="output", must_exist=False
        )
        if output_path.suffix.lower() != ".plugin":
            raise ValueError("output must use the .plugin extension")
        if output_path.exists() and _is_reparse(output_path):
            raise ValueError("output is a symlink/reparse point")
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: invalid manifest: {exc}", file=sys.stderr)
        return 1
    if not isinstance(manifest, dict):
        print("ERROR: manifest must be a JSON object", file=sys.stderr)
        return 1

    skills = []
    try:
        entries = sorted(skills_root.iterdir(), key=lambda item: item.name.lower())
        for entry in entries:
            if _is_reparse(entry):
                raise ValueError(f"skills root contains a symlink/reparse entry: {entry}")
            if not entry.is_dir():
                continue
            skill_file = entry / "SKILL.md"
            if skill_file.exists() and _is_reparse(skill_file):
                raise ValueError(f"skill contains a symlink/reparse SKILL.md: {skill_file}")
            if not skill_file.is_file():
                continue
            if skill_file.stat().st_size > MAX_SKILL_BYTES:
                raise ValueError(f"skill exceeds {MAX_SKILL_BYTES} bytes: {entry.name}")
            skills.append(entry.name)
    except (OSError, ValueError) as exc:
        print(f"ERROR: invalid skills root: {exc}", file=sys.stderr)
        return 1
    if not skills:
        print("ERROR: No skills found", file=sys.stderr)
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", prefix=f".{output_path.stem}.", suffix=".tmp", dir=output_path.parent, delete=False
        ) as handle:
            temp_name = handle.name
        with zipfile.ZipFile(temp_name, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(
                ".claude-plugin/plugin.json",
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            )
            for skill in skills:
                zf.write(
                    skills_root / skill / "SKILL.md",
                    f"skills/{skill}/SKILL.md",
                )
            readme = (
                f"# {manifest.get('name', 'plugin')} Plugin\n\n"
                f"{manifest.get('description', '')}\n\n"
                f"Skills: {', '.join(skills)}\n"
            )
            zf.writestr("README.md", readme)
        pathlib.Path(temp_name).replace(output_path)
    except (OSError, zipfile.BadZipFile, ValueError) as exc:
        if temp_name:
            pathlib.Path(temp_name).unlink(missing_ok=True)
        print(f"ERROR: package creation failed: {exc}", file=sys.stderr)
        return 1

    print(f"Created: {output_path}")
    print(f"  Skills packaged ({len(skills)}): {', '.join(skills)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
