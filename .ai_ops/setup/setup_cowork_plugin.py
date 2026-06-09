#!/usr/bin/env python3
"""Package ai_ops skills into a Cowork .plugin file."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import zipfile


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skills-root", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    skills_root = pathlib.Path(args.skills_root)
    manifest_path = pathlib.Path(args.manifest)
    output_path = pathlib.Path(args.output)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    skills = sorted(
        d.name
        for d in skills_root.iterdir()
        if d.is_dir() and (d / "SKILL.md").exists()
    )
    if not skills:
        print("ERROR: No skills found", file=sys.stderr)
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            ".claude-plugin/plugin.json",
            json.dumps(manifest, indent=2) + "\n",
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

    print(f"Created: {output_path}")
    print(f"  Skills packaged ({len(skills)}): {', '.join(skills)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
