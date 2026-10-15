"""Regression tests for the shell-free governed validator command contract."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "00_Admin" / "scripts" / "op_validate_config.py"
SPEC = importlib.util.spec_from_file_location("op_validate_config", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ValidationCommandPolicyTests(unittest.TestCase):
    def test_accepts_contained_python_argv(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "workspace"
            repo = workspace / "repo"
            (workspace / "ai_ops" / "00_Admin" / "scripts").mkdir(parents=True)
            (repo / "scripts").mkdir(parents=True)
            script = repo / "scripts" / "validate.py"
            script.write_text("", encoding="utf-8")

            errors = MODULE.validate_command_argv(
                ["python", "scripts/validate.py", "--repo-root", "."],
                label="command",
                repo_root=repo,
                workspace_root=workspace,
            )
            self.assertEqual([], errors)

    def test_rejects_shell_strings_shell_metacharacters_and_escape_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "workspace"
            repo = workspace / "repo"
            (workspace / "ai_ops" / "00_Admin" / "scripts").mkdir(parents=True)
            (repo / "scripts").mkdir(parents=True)
            (repo / "scripts" / "validate.py").write_text("", encoding="utf-8")

            self.assertTrue(
                MODULE.validate_command_argv(
                    "python scripts/validate.py",
                    label="command",
                    repo_root=repo,
                    workspace_root=workspace,
                )
            )
            self.assertTrue(
                MODULE.validate_command_argv(
                    ["python", "scripts/validate.py", "&&", "whoami"],
                    label="command",
                    repo_root=repo,
                    workspace_root=workspace,
                )
            )
            self.assertTrue(
                MODULE.validate_command_argv(
                    ["python", "../outside.py"],
                    label="command",
                    repo_root=repo,
                    workspace_root=workspace,
                )
            )
            self.assertTrue(
                MODULE.validate_command_argv(
                    ["./python", "scripts/validate.py"],
                    label="command",
                    repo_root=repo,
                    workspace_root=workspace,
                )
            )
            self.assertTrue(
                MODULE.validate_command_argv(
                    ["python", "scripts/validate.py", "--repo-root=C:\\outside"],
                    label="command",
                    repo_root=repo,
                    workspace_root=workspace,
                )
            )
            self.assertTrue(
                MODULE.validate_command_argv(
                    ["python", "scripts/validate.py", "--output-dir=C:\\outside"],
                    label="command",
                    repo_root=repo,
                    workspace_root=workspace,
                )
            )
            self.assertTrue(
                MODULE.validate_command_argv(
                    ["python", "scripts/validate.py", "C:\\outside"],
                    label="command",
                    repo_root=repo,
                    workspace_root=workspace,
                )
            )
            self.assertTrue(
                MODULE.validate_command_argv(
                    ["python", "scripts/validate.py", "C:outside"],
                    label="command",
                    repo_root=repo,
                    workspace_root=workspace,
                )
            )


if __name__ == "__main__":
    unittest.main()
