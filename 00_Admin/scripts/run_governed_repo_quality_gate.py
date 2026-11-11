#!/usr/bin/env python3
"""Run the selected governed repository's configured minimum checks.

The ai_ops release gate is intentionally repository-specific.  This wrapper
provides the missing governed-target route by loading the machine-local
registration, validating each argv list, and executing it with the target
repository as cwd and ``shell=False``.
"""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
AI_OPS_ROOT = SCRIPT_DIR.parents[1]
WORKSPACE_ROOT = AI_OPS_ROOT.parent


def load_validator():
    path = SCRIPT_DIR / "op_validate_config.py"
    spec = importlib.util.spec_from_file_location("op_validate_config", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load config validator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def resolve_repo(value: Path, workspace_root: Path) -> Path:
    candidates = [value] if value.is_absolute() else [Path.cwd() / value, workspace_root / value]
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.is_dir() and (resolved / ".git").exists():
            return resolved
    rendered = ", ".join(str(candidate.resolve()) for candidate in candidates)
    raise SystemExit(f"governed quality gate: repository not found: {rendered}")


def find_registration(config: dict[str, Any], repo: Path, workspace_root: Path) -> dict[str, Any]:
    entries = config.get("workspace", {}).get("work_repos", [])
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        value = entry.get("path")
        if not isinstance(value, str):
            continue
        candidate = (workspace_root / value).resolve()
        if candidate == repo:
            return entry
    raise SystemExit(f"governed quality gate: target is not registered: {repo}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--workspace-root", type=Path, default=WORKSPACE_ROOT)
    parser.add_argument("--config", type=Path, default=AI_OPS_ROOT / ".ai_ops/local/config.yaml")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    workspace_root = args.workspace_root.resolve()
    repo = resolve_repo(args.repo_root, workspace_root)
    if args.config.is_absolute():
        config_path = args.config.resolve()
    else:
        config_candidates = [
            (Path.cwd() / args.config).resolve(),
            (workspace_root / args.config).resolve(),
            (AI_OPS_ROOT / args.config).resolve(),
        ]
        config_path = next(
            (candidate for candidate in config_candidates if candidate.is_file()),
            config_candidates[0],
        )
    if not config_path.is_file():
        raise SystemExit(f"governed quality gate: config not found: {config_path}")
    config_validator = load_validator()
    valid, errors = config_validator.validate_config(config_path)
    if not valid:
        for error in errors:
            print(f"[CONFIG] {error}", file=sys.stderr)
        return 1
    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    entry = find_registration(config, repo, workspace_root)
    commands = entry.get("savepoint_validation", {}).get("minimum_commands", [])
    if not isinstance(commands, list) or not commands:
        print(f"[RESULT] governed-repo quality gate: UNAVAILABLE ({repo.name} has no configured minimum_commands)")
        return 2
    failures = 0
    for index, command in enumerate(commands, start=1):
        label = f"minimum-command-{index}"
        errors = config_validator.validate_command_argv(
            command,
            label=label,
            repo_root=repo,
            workspace_root=workspace_root,
        )
        if errors:
            for error in errors:
                print(f"[CONFIG] {error}", file=sys.stderr)
            failures += 1
            continue
        argv = list(command)
        if argv[0].lower() in {"python", "python3", "py", "python.exe", "python3.exe", "py.exe"}:
            argv[0] = sys.executable
        print(f"[CHECK] {label}")
        print(f"  cwd: {repo}")
        print(f"  command: {' '.join(argv)}")
        if args.dry_run:
            print(f"[DRY_RUN] {label} not executed")
            continue
        completed = subprocess.run(argv, cwd=repo, shell=False, check=False)
        if completed.returncode:
            print(f"[FAIL] {label} exited with code {completed.returncode}")
            failures += 1
        else:
            print(f"[PASS] {label}")
    if args.dry_run:
        print("[RESULT] governed-repo quality gate: DRY_RUN (not admission eligible)")
        return 3
    if failures:
        print(f"[RESULT] governed-repo quality gate: FAIL ({failures} failure(s))")
        return 1
    print("[RESULT] governed-repo quality gate: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
