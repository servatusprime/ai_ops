#!/usr/bin/env python
"""Run the validator engine against every work repo registered in the local ai_ops config.

Usage:
  python <ai_ops>/00_Admin/scripts/validate_workspace.py [--target <repo path>] [--require-hook]
  (--target is a path as registered, or `.` when run from inside the repo to review)

Reads workspace.work_repos from .ai_ops/local/config.yaml (machine-local, gitignored). An entry may
set validator_config (relative to that repo); the default is
00_Admin/configs/validator/validator_config.yaml. The engine always runs from this ai_ops checkout,
so every repo is checked by the same rules; each repo supplies only its own config.

Prints one line per repo. The exit code is 1 when the --target repo has errors or no usable config
(other repos are reported but do not block), or, without --target, when any repo does. With
--require-hook, a repo whose commit hook does not run the engine also fails (the target only, or
every repo without --target). A problem with the local config itself exits 2.
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import yaml

AI_OPS_ROOT = Path(__file__).resolve().parents[2]
ENGINE = AI_OPS_ROOT / "00_Admin" / "scripts" / "validate_repo_rules.py"
DEFAULT_CONFIG = "00_Admin/configs/validator/validator_config.yaml"
COMMIT_STAGES = {"pre-commit", "commit"}
RUNS_AT_COMMIT = "runs at commit"


def _load_engine():
    spec = importlib.util.spec_from_file_location("validate_repo_rules_engine", ENGINE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def hook_state(repo: Path) -> str:
    """Say whether a commit hook in this repo runs the engine."""
    state = "no commit hook found"
    pre_commit = repo / ".pre-commit-config.yaml"
    if pre_commit.is_file():
        try:
            data = yaml.safe_load(pre_commit.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            data = {}
        data = data if isinstance(data, dict) else {}
        default_stages = data.get("default_stages") or ["pre-commit"]
        for block in data.get("repos") or []:
            for hook in (block or {}).get("hooks") or []:
                if "validate_repo_rules" in str(hook.get("entry", "")):
                    stages = {str(stage) for stage in (hook.get("stages") or default_stages)}
                    if stages & COMMIT_STAGES:
                        return RUNS_AT_COMMIT
                    state = "not at commit (stage: " + ", ".join(sorted(stages)) + ")"
    hooks_dir = repo / ".githooks"
    if hooks_dir.is_dir():
        for hook in hooks_dir.iterdir():
            if hook.is_file() and "validate_repo_rules" in hook.read_text(encoding="utf-8", errors="replace"):
                return RUNS_AT_COMMIT
    return state


def check_repo(engine, workspace_root: Path, entry: object) -> dict:
    row = {
        "name": "?",
        "repo": None,
        "ok": False,
        "detail": "",
        "errors": "-",
        "warnings": "-",
        "undeclared": "-",
        "hook": "-",
    }
    relative = str(entry.get("path", "")).strip() if isinstance(entry, dict) else ""
    if not relative:
        row["detail"] = "entry has no path"
        return row
    repo = (workspace_root / relative).resolve()
    row["name"], row["repo"] = repo.name, repo
    if not repo.is_dir():
        row["detail"] = "repo folder missing"
        return row
    row["hook"] = hook_state(repo)
    config = repo / str(entry.get("validator_config") or DEFAULT_CONFIG)
    if not config.is_file():
        row["detail"] = "no validator config"
        return row
    command = [sys.executable, str(ENGINE), "--repo-root", str(repo), "--config", str(config)]
    if not (repo / ".git").exists():
        # A folder that is not itself a git checkout must not take an unrelated parent repo as its structure root.
        command += ["--structure-root", str(repo)]
    try:
        run = subprocess.run(
            command,
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=600,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        row["detail"] = f"engine did not finish ({type(exc).__name__})"
        return row
    errors = re.search(r"Validator errors: (\d+)", run.stdout)
    warnings = re.search(r"Validator warnings: (\d+)", run.stdout)
    row["errors"] = errors.group(1) if errors else "0"
    row["warnings"] = warnings.group(1) if warnings else "0"
    row["ok"] = run.returncode == 0
    if run.returncode != 0 and not errors:
        row["detail"] = (run.stdout.strip().splitlines() or ["engine failed"])[0][:60]
    try:
        declared = {rule["id"] for rule in engine.parse_config(str(config)).get("rules", [])}
        row["undeclared"] = str(len(engine.IMPLEMENTED_RULE_IDS - declared))
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        pass
    return row


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--target", help="repo path (as registered) whose result sets the exit code")
    parser.add_argument(
        "--require-hook", action="store_true", help="also fail a repo whose commit hook does not run the engine"
    )
    parser.add_argument("--local-config", default=str(AI_OPS_ROOT / ".ai_ops" / "local" / "config.yaml"))
    parser.add_argument("--workspace-root", default=str(AI_OPS_ROOT.parent))
    args = parser.parse_args(argv)

    try:
        local = yaml.safe_load(Path(args.local_config).read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        print(f"Cannot read the local config ({type(exc).__name__}): {args.local_config}")
        return 2
    entries = (local.get("workspace") or {}).get("work_repos") if isinstance(local, dict) else None
    if not isinstance(entries, list) or not entries:
        print("No work repos are registered in the local config.")
        return 2
    workspace_root = Path(args.workspace_root).resolve()
    engine = _load_engine()
    rows = [check_repo(engine, workspace_root, entry) for entry in entries]
    for row in rows:
        row["pass"] = row["ok"] and (not args.require_hook or row["hook"] == RUNS_AT_COMMIT)

    print(f"{'repo':20} {'result':8} {'errors':>6} {'warnings':>8} {'undeclared rules':>16}  commit hook")
    for row in rows:
        extra = f"  ({row['detail']})" if row["detail"] else ""
        result = "ok" if row["pass"] else "FAIL"
        print(
            f"{row['name']:20} {result:8} {row['errors']:>6} {row['warnings']:>8} "
            f"{row['undeclared']:>16}  {row['hook']}{extra}"
        )

    if args.target:
        # Accept a path relative to the workspace root (as registered) or to the current directory (`.`).
        targets = {(workspace_root / args.target).resolve(), Path(args.target).resolve()}
        match = [row for row in rows if row["repo"] in targets]
        if not match:
            print(f"Target is not a registered work repo: {args.target}")
            return 2
        return 0 if match[0]["pass"] else 1
    return 0 if all(row["pass"] for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
