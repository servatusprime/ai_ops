from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import Iterable, List


def _load_yaml(path: Path) -> dict:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise RuntimeError("PyYAML is required to load the config file") from exc

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}, got {type(data).__name__}")
    return data


def _match_filters(path: Path, include_patterns: Iterable[str], exclude_patterns: Iterable[str]) -> bool:
    includes = list(include_patterns)
    excludes = list(exclude_patterns)
    rel = path.as_posix()

    if includes and not any(Path(rel).match(pattern) for pattern in includes):
        return False
    if excludes and any(Path(rel).match(pattern) for pattern in excludes):
        return False
    return True


def sync_external_context(config_path: Path, dry_run: bool = True) -> List[Path]:
    data = _load_yaml(config_path)
    customizations = data.get("customizations", {})
    external = customizations.get("external_context", {})
    include_patterns = external.get("include_patterns", [])
    exclude_patterns = external.get("exclude_patterns", [])

    manifest_path = Path(external.get("manifest_path", "90_Sandbox/ai_external_context/manifest.yaml"))
    bundle_root = Path(external.get("bundle_root", "90_Sandbox/ai_external_context"))

    repo_root = config_path.parent.resolve()
    manifest_path = (repo_root / manifest_path).resolve()
    bundle_root = (repo_root / bundle_root).resolve()

    copied: List[Path] = []
    if not manifest_path.exists():
        raise FileNotFoundError(f"External context manifest not found: {manifest_path}")

    manifest = _load_yaml(manifest_path)
    files = manifest.get("files", [])
    if not isinstance(files, list):
        raise ValueError("ai_external_context manifest 'files' must be a list")

    for entry in files:
        if not isinstance(entry, dict):
            continue
        source = entry.get("source_path")
        bundle = entry.get("bundle_path")
        if not source or not bundle:
            continue
        if not _match_filters(Path(bundle), include_patterns, exclude_patterns):
            continue
        src = (repo_root / source).resolve()
        dest = (bundle_root / bundle).resolve()
        if not src.exists():
            raise FileNotFoundError(f"Source file missing for external context export: {src}")
        copied.append(dest)
        if dry_run:
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
    return copied


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync external context into the repo work area.")
    parser.add_argument("--config", default="00_Admin/configs/setup_contract.yaml",
                        help="Path to config file (customizations section)")
    parser.add_argument("--apply", action="store_true", help="Apply changes (default: dry run)")
    args = parser.parse_args()

    copied = sync_external_context(Path(args.config), dry_run=not args.apply)
    print(f"Planned copies: {len(copied)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
