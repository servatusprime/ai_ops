"""Validate module metadata and basic coherence."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None


def load_metadata(path: Path) -> Dict:
    if yaml:
        with path.open("r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    # Fallback: minimal key/value scrape
    data: Dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            data[key.strip()] = val.strip()
    return data


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    modules_dir = repo_root / "02_Modules"
    issues: List[str] = []

    for module_dir in sorted(p for p in modules_dir.iterdir() if p.is_dir() and not p.name.startswith("_")):
        meta_path = module_dir / "metadata" / "module.yaml"
        if not meta_path.exists():
            issues.append(f"{module_dir}: missing metadata/module.yaml")
            continue

        if meta_path.stat().st_size == 0:
            issues.append(f"{meta_path}: metadata file is empty")
            continue

        meta = load_metadata(meta_path)
        module_id = meta.get("id") or meta.get("module_id")
        if not module_id:
            issues.append(f"{meta_path}: missing required 'id'")
        elif module_id != module_dir.name:
            issues.append(f"{meta_path}: id '{module_id}' does not match folder '{module_dir.name}'")

    if issues:
        print("Metadata validation failed:")
        for msg in issues:
            print(f"- {msg}")
        return 1

    print("Metadata validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
