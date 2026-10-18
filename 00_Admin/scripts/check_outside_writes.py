#!/usr/bin/env python
"""Report recent files under declared workspace escape roots; never mutates."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]

# Keep the shared helper import explicit so isolated execution cannot resolve a
# repository-local module through an ambient working-directory search path.
SCRIPTS_ROOT = Path(__file__).resolve().parent
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from hooks.guard_workspace_writes import expand  # noqa: E402


def load_report_signatures(config: Path, root: Path) -> list[Path]:
    try:
        data = yaml.safe_load(config.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise SystemExit(f"outside-write-check: containment policy is invalid: {exc}") from exc
    values = data.get("escape_root_signatures")
    if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
        raise SystemExit("outside-write-check: escape_root_signatures must be a string list")
    expanded: list[Path] = []
    for value in values:
        expanded.append(expand(value, root))
        if "<os-temp>" in value:
            stable = [
                Path(os.environ.get("USERPROFILE", str(Path.home()))) / "AppData/Local/Temp",
                Path(os.environ.get("SystemRoot", "C:/Windows")) / "Temp",
            ]
            expanded.extend(Path(str(value).replace("<os-temp>", str(base))).resolve() for base in stable)
    return list(dict.fromkeys(expanded))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", type=Path, default=ROOT)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--since-hours", type=float, default=24.0)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()
    root = args.workspace_root.resolve()
    config = (args.config or root / "00_Admin/configs/workspace_containment.yaml").resolve()
    signatures = load_report_signatures(config, root)
    cutoff = time.time() - max(args.since_hours, 0.0) * 3600
    rows: list[dict[str, object]] = []
    for signature in signatures:
        pattern = Path(str(signature))
        bases = list(pattern.parent.glob(pattern.name)) if "*" in str(signature) else [signature]
        for base in bases:
            if not base.exists():
                continue
            targets = [base] if base.is_file() else base.rglob("*")
            for target in targets:
                if not target.is_file():
                    continue
                try:
                    stat = target.stat()
                except OSError:
                    continue
                if stat.st_mtime >= cutoff:
                    resolved_target = target.resolve()
                    row = {"path": str(resolved_target), "modified_epoch": stat.st_mtime, "root": str(base)}
                    if target.is_symlink():
                        row["link_path"] = str(target)
                    rows.append(row)
    rows.sort(key=lambda row: (str(row["path"]), float(row["modified_epoch"])))
    if args.format == "json":
        print(json.dumps({"workspace_root": str(root), "since_hours": args.since_hours, "files": rows}, indent=2))
    else:
        print(f"workspace_root={root}")
        print(f"since_hours={args.since_hours}")
        for row in rows:
            print(f"{row['path']} | modified_epoch={row['modified_epoch']} | signature_root={row['root']}")
        print(f"files={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
