#!/usr/bin/env python
"""Positive and negative fixtures for validate_governed_repo_shape.py."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from validate_governed_repo_shape import validate_repo_shape  # noqa: E402


def _write(path: Path, text: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _repo(workspace: Path, name: str = "repo", domain: bool = True) -> Path:
    root = workspace / name
    _write(root / "AGENTS.md", "# Agents\n")
    _write(root / "README.md", "# Repo\n")
    (root / "00_Admin").mkdir(parents=True)
    (root / "90_Sandbox").mkdir(parents=True)
    if domain:
        (root / "src").mkdir(parents=True)
    return root


def _registration(workspace: Path, repo_name: str = "repo") -> Path:
    path = workspace / "registration.yaml"
    _write(
        path,
        "workspace:\n  work_repos:\n    - path: " + repo_name + "/\n",
    )
    return path


def _assert_fail(findings: list[str], fragment: str) -> None:
    assert any(fragment in finding for finding in findings), findings


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="governed-shape-") as raw:
        workspace = Path(raw)

        root = _repo(workspace)
        assert validate_repo_shape(root, _registration(workspace), workspace) == []

        missing_registration = validate_repo_shape(root, None, workspace)
        _assert_fail(missing_registration, "registration")

        missing_directory = _repo(workspace, "missing-directory")
        (missing_directory / "90_Sandbox").rmdir()
        _assert_fail(
            validate_repo_shape(
                missing_directory,
                _registration(workspace, "missing-directory"),
                workspace,
            ),
            "governed directory",
        )

        missing_instructions = _repo(workspace, "missing-instructions")
        (missing_instructions / "AGENTS.md").unlink()
        _assert_fail(
            validate_repo_shape(
                missing_instructions,
                _registration(workspace, "missing-instructions"),
                workspace,
            ),
            "root instruction",
        )

        misplaced = _repo(workspace, "misplaced")
        _write(misplaced / "wb_bad.md", "# misplaced\n")
        _assert_fail(
            validate_repo_shape(
                misplaced, _registration(workspace, "misplaced"), workspace
            ),
            "misplaced workbundle",
        )

        exception = _repo(workspace, "exception", domain=False)
        registration = _registration(workspace, "exception")
        _assert_fail(
            validate_repo_shape(exception, registration, workspace, "EX-1"),
            "undocumented",
        )

        exception_text = (
            "# Repo\n\n## Governed Bootstrap Exception\n\n"
            "exception_id: EX-1\nreason: no domain assets yet\n"
        )
        _write(exception / "README.md", exception_text)
        work_state = workspace / "work_state.yaml"
        receipt = workspace / "setup_receipt.yaml"
        _write(work_state, "governed_bootstrap_exception: EX-1\n")
        _write(receipt, "governed_bootstrap_exception: EX-1\n")
        assert (
            validate_repo_shape(
                exception,
                registration,
                workspace,
                "EX-1",
                work_state,
                receipt,
            )
            == []
        )

    print("governed repository shape fixtures: 6 passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
