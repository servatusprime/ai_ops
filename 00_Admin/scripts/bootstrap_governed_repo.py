#!/usr/bin/env python
"""Create and validate the minimum ai_ops-governed repository bootstrap."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from validate_governed_repo_shape import validate_repo_shape

DEFAULT_SETUP_CONTRACT = "1.0.0"


def _resolve_inside(root: Path, value: str) -> Path:
    candidate = Path(value)
    resolved = (candidate if candidate.is_absolute() else root / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"path escapes repository root: {value}") from exc
    return resolved


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise ValueError(f"expected a YAML mapping: {path}")
    return value


def _write_new(path: Path, content: str) -> None:
    if path.exists():
        if path.is_file() and path.read_text(encoding="utf-8").strip():
            return
        if not path.is_file():
            raise ValueError(f"cannot replace existing directory: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def _relative_registration_path(repo_root: Path, workspace_root: Path) -> str:
    try:
        return repo_root.resolve().relative_to(workspace_root.resolve()).as_posix() + "/"
    except ValueError:
        return repo_root.resolve().as_posix()


def _append_registration_text(
    registration_file: Path,
    repo_root: Path,
    workspace_root: Path,
) -> None:
    """Append a repo registration without rewriting operator-authored YAML."""

    text = registration_file.read_text(encoding="utf-8")
    newline = "\r\n" if "\r\n" in text else "\n"
    lines = text.splitlines(keepends=True)
    workspace_index = next(
        (
            index
            for index, line in enumerate(lines)
            if re.match(r"^workspace:\s*(?:#.*)?(?:\r?\n)?$", line)
        ),
        None,
    )
    if workspace_index is None:
        raise ValueError(
            f"workspace mapping not found; refusing to rewrite {registration_file}"
        )
    work_repos_index = next(
        (
            index
            for index in range(workspace_index + 1, len(lines))
            if re.match(r"^  work_repos:\s*(?:#.*)?(?:\r?\n)?$", lines[index])
            or re.match(r"^  work_repos:\s*\[\s*\]\s*(?:#.*)?(?:\r?\n)?$", lines[index])
        ),
        None,
    )
    if work_repos_index is None:
        raise ValueError(
            f"workspace.work_repos list not found; refusing to rewrite {registration_file}"
        )

    work_repos_line = lines[work_repos_index].rstrip("\r\n")
    empty_match = re.match(
        r"^(  work_repos:)\s*\[\s*\]\s*(#.*)?$", work_repos_line
    )
    insertion_index = work_repos_index + 1
    if empty_match:
        comment = empty_match.group(2)
        lines[work_repos_index] = empty_match.group(1) + newline
        if comment:
            lines.insert(insertion_index, f"  {comment}{newline}")
            insertion_index += 1
    else:
        while insertion_index < len(lines):
            candidate = lines[insertion_index].rstrip("\r\n")
            if re.match(r"^  \S", candidate) and not candidate.startswith("    "):
                break
            insertion_index += 1

    path_value = _relative_registration_path(repo_root, workspace_root)
    block = [
        f"    - path: {path_value}{newline}",
        f"      sandbox_dir: 90_Sandbox{newline}",
        f"      savepoint_validation:{newline}",
        f"        minimum_commands: []{newline}",
    ]
    lines[insertion_index:insertion_index] = block
    registration_file.write_text("".join(lines), encoding="utf-8", newline="")


def _ensure_registration(
    registration_file: Path,
    repo_root: Path,
    workspace_root: Path,
) -> None:
    data = _read_yaml(registration_file)
    workspace = data.setdefault("workspace", {})
    if not isinstance(workspace, dict):
        raise ValueError(f"workspace must be a mapping: {registration_file}")
    entries = workspace.setdefault("work_repos", [])
    if not isinstance(entries, list):
        raise ValueError(f"workspace.work_repos must be a list: {registration_file}")

    target = repo_root.resolve()
    for entry in entries:
        if not isinstance(entry, dict) or not entry.get("path"):
            continue
        candidate = Path(str(entry["path"]))
        if not candidate.is_absolute():
            candidate = workspace_root / candidate
        if candidate.resolve() == target:
            return

    entries.append(
        {
            "path": _relative_registration_path(repo_root, workspace_root),
            "sandbox_dir": "90_Sandbox",
            "savepoint_validation": {"minimum_commands": []},
        }
    )
    if registration_file.exists() and registration_file.read_text(encoding="utf-8").strip():
        _append_registration_text(registration_file, repo_root, workspace_root)
        return
    registration_file.parent.mkdir(parents=True, exist_ok=True)
    registration_file.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
        newline="\n",
    )


def _setup_contract_version(ai_ops_root: Path) -> str:
    contract = _read_yaml(ai_ops_root / "00_Admin/configs/setup_contract.yaml")
    value = contract.get("setup_contract", {}).get("required_version")
    return str(value or DEFAULT_SETUP_CONTRACT)


def bootstrap(
    repo_root: Path,
    ai_ops_root: Path,
    workspace_root: Path,
    domain_dir: str | None,
    exception_id: str | None,
) -> list[str]:
    repo_root = repo_root.resolve()
    ai_ops_root = ai_ops_root.resolve()
    workspace_root = workspace_root.resolve()
    if domain_dir == exception_id or (not domain_dir and not exception_id):
        raise ValueError("provide exactly one of --domain-dir or --exception-id")
    if not repo_root.exists():
        repo_root.mkdir(parents=True)
    if not repo_root.is_dir():
        raise ValueError(f"repository root is not a directory: {repo_root}")
    if not ai_ops_root.is_dir():
        raise ValueError(f"ai_ops root is not a directory: {ai_ops_root}")
    if not workspace_root.is_dir():
        raise ValueError(f"workspace root is not a directory: {workspace_root}")

    if domain_dir:
        domain_path = _resolve_inside(repo_root, domain_dir)
        if domain_path.name in {"00_Admin", "90_Sandbox"}:
            raise ValueError("domain anchor cannot be 00_Admin or 90_Sandbox")
        domain_path.mkdir(parents=True, exist_ok=True)

    (repo_root / "00_Admin").mkdir(exist_ok=True)
    (repo_root / "90_Sandbox").mkdir(exist_ok=True)
    _write_new(
        repo_root / "AGENTS.md",
        "# Agent Instructions\n\n"
        "This repository is governed by ai_ops. Read this file, README.md, "
        "and the applicable 00_Admin guidance before execution.\n",
    )
    readme_lines = [
        f"# {repo_root.name}",
        "",
        "This repository uses the ai_ops governed-repository bootstrap contract.",
        "",
    ]
    if exception_id:
        readme_lines.extend(
            [
                "## Governed Bootstrap Exception",
                "",
                f"exception_id: {exception_id}",
                "",
                "This repository currently has no domain anchor; add one when "
                "domain assets are introduced.",
                "",
            ]
        )
    _write_new(repo_root / "README.md", "\n".join(readme_lines))

    local_root = repo_root / ".ai_ops/local"
    work_state = local_root / "work_state.yaml"
    receipt = local_root / "setup/state.yaml"
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    state = {
        "schema_version": "1.0.0",
        "bootstrap": {
            "governed_repo_shape": "minimum",
            "exception_id": exception_id,
            "completed_at": timestamp,
        },
    }
    if not work_state.exists():
        local_root.mkdir(parents=True, exist_ok=True)
        work_state.write_text(
            "# Machine-local governed-repository bootstrap state.\n"
            + yaml.safe_dump(state, sort_keys=False, allow_unicode=False),
            encoding="utf-8",
            newline="\n",
        )
    if not receipt.exists():
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text(
            "# Machine-local ai_ops setup receipt.\n"
            + yaml.safe_dump(
                {
                    "schema_version": "1.0.0",
                    "setup_contract_version": _setup_contract_version(ai_ops_root),
                    "completed_at": timestamp,
                    "install_summary": {
                        "bootstrap": "minimum_governed_repo_shape",
                        "repo_root": repo_root.as_posix(),
                    },
                    "exception_id": exception_id,
                },
                sort_keys=False,
                allow_unicode=False,
            ),
            encoding="utf-8",
            newline="\n",
        )

    registration_file = ai_ops_root / ".ai_ops/local/config.yaml"
    _ensure_registration(registration_file, repo_root, workspace_root)
    findings = validate_repo_shape(
        repo_root,
        registration_file,
        workspace_root,
        exception_id,
        work_state,
        receipt,
    )
    return findings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--ai-ops-root", type=Path, required=True)
    parser.add_argument("--workspace-root", type=Path, required=True)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--domain-dir")
    choice.add_argument("--exception-id")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        findings = bootstrap(
            args.repo_root,
            args.ai_ops_root,
            args.workspace_root,
            args.domain_dir,
            args.exception_id,
        )
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    if findings:
        for finding in findings:
            print(f"FAIL: {finding}", file=sys.stderr)
        return 1
    print(f"PASS: governed repository bootstrapped: {args.repo_root.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
