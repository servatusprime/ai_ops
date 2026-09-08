#!/usr/bin/env python
"""Validate the minimum machine-checkable shape of an ai_ops-governed repo."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - the repo setup gate catches this
    raise SystemExit("PyYAML is required to validate governed-repo registration") from exc


REQUIRED_FILES = ("AGENTS.md", "README.md")
REQUIRED_DIRECTORIES = ("00_Admin", "90_Sandbox")
DOMAIN_CANDIDATES = (
    "01_Resources",
    "02_Modules",
    "03_Projects",
    "Projects",
    "src",
    "data",
    "tools",
    "modules",
    "domain",
)
EXCEPTION_HEADING = "## Governed Bootstrap Exception"


def _same_path(left: Path, right: Path) -> bool:
    return left.resolve(strict=False) == right.resolve(strict=False)


def _read_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError(f"cannot read YAML registration file {path}: {exc}") from exc


def _is_registered(repo_root: Path, registration_file: Path, workspace_root: Path) -> bool:
    data = _read_yaml(registration_file)
    entries = data.get("workspace", {}).get("work_repos", [])
    if not isinstance(entries, list):
        return False
    for entry in entries:
        if not isinstance(entry, dict) or not entry.get("path"):
            continue
        candidate = Path(str(entry["path"]))
        if not candidate.is_absolute():
            candidate = workspace_root / candidate
        if _same_path(candidate, repo_root):
            return True
    return False


def _misplaced_workbundles(repo_root: Path) -> list[Path]:
    locations = [repo_root, repo_root / "00_Admin" / "backlog"]
    matches: list[Path] = []
    for location in locations:
        if not location.is_dir():
            continue
        for pattern in ("wb_*.md", "work_proposal_*.md"):
            matches.extend(sorted(location.glob(pattern)))
    return matches


def validate_repo_shape(
    repo_root: Path,
    registration_file: Path | None,
    workspace_root: Path | None = None,
    exception_id: str | None = None,
    work_state_file: Path | None = None,
    setup_receipt: Path | None = None,
) -> list[str]:
    """Return fail-closed findings for a governed repository shape."""

    root = repo_root.resolve(strict=False)
    findings: list[str] = []

    for name in REQUIRED_FILES:
        if not (root / name).is_file():
            findings.append(f"missing required root instruction file: {name}")
    for name in REQUIRED_DIRECTORIES:
        if not (root / name).is_dir():
            findings.append(f"missing required governed directory: {name}/")

    domain_present = any((root / name).is_dir() for name in DOMAIN_CANDIDATES)
    readme = root / "README.md"
    readme_text = readme.read_text(encoding="utf-8") if readme.is_file() else ""
    if not domain_present:
        if not exception_id:
            findings.append(
                "no domain anchor found; provide one or declare --exception-id"
            )
        else:
            marker = f"exception_id: {exception_id}"
            if EXCEPTION_HEADING not in readme_text or marker not in readme_text:
                findings.append(
                    f"undocumented governed bootstrap exception: {exception_id}"
                )
            for label, path in (
                ("work-state", work_state_file),
                ("setup receipt", setup_receipt),
            ):
                if path is None or not path.is_file():
                    findings.append(
                        f"exception {exception_id} is missing generated {label} evidence"
                    )
                elif exception_id not in path.read_text(encoding="utf-8"):
                    findings.append(
                        f"exception {exception_id} is absent from {label} evidence"
                    )

    if registration_file is None or not registration_file.is_file():
        findings.append("missing ai_ops registration file")
    else:
        try:
            if not _is_registered(
                root,
                registration_file,
                (workspace_root or registration_file.parent).resolve(strict=False),
            ):
                findings.append(
                    f"repository is not registered in {registration_file}"
                )
        except ValueError as exc:
            findings.append(str(exc))

    for path in _misplaced_workbundles(root):
        findings.append(f"misplaced workbundle/proposal outside 90_Sandbox: {path}")

    return findings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--registration-file", type=Path, required=True)
    parser.add_argument(
        "--workspace-root",
        type=Path,
        required=True,
        help="root used to resolve relative workspace.work_repos paths",
    )
    parser.add_argument("--exception-id")
    parser.add_argument("--work-state-file", type=Path)
    parser.add_argument("--setup-receipt", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    findings = validate_repo_shape(
        args.repo_root,
        args.registration_file,
        args.workspace_root,
        args.exception_id,
        args.work_state_file,
        args.setup_receipt,
    )
    if findings:
        for finding in findings:
            print(f"FAIL: {finding}", file=sys.stderr)
        return 1
    print(f"PASS: governed repository shape is valid: {args.repo_root.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
