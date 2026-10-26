"""Regression tests for the shell-free governed validator command contract."""

import contextlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "00_Admin" / "scripts" / "op_validate_config.py"
SPEC = importlib.util.spec_from_file_location("op_validate_config", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ValidationCommandPolicyTests(unittest.TestCase):
    def test_invalid_config_output_omits_config_path_and_error_details(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "invalid.yaml"
            config_path.write_text(
                "workspace:\n  work_repos:\n    - path: ../outside\n",
                encoding="utf-8",
            )
            output = io.StringIO()
            with patch.object(MODULE.sys, "argv", ["op_validate_config.py", str(config_path)]):
                with contextlib.redirect_stdout(output):
                    with self.assertRaises(SystemExit) as raised:
                        MODULE.main()

            self.assertEqual(1, raised.exception.code)
            rendered = output.getvalue()
            self.assertIn("[FAIL] Config invalid", rendered)
            self.assertNotIn(str(config_path), rendered)
            self.assertNotIn("../outside", rendered)

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

    def test_accepts_separated_and_equals_data_root_forms(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "workspace"
            repo = workspace / "repo"
            (workspace / "ai_ops" / "00_Admin" / "scripts").mkdir(parents=True)
            (repo / "scripts").mkdir(parents=True)
            (repo / "data").mkdir()
            script = repo / "scripts" / "validate.py"
            script.write_text("", encoding="utf-8")

            for command in (
                ["python", "scripts/validate.py", "--data-root", "data"],
                ["python", "scripts/validate.py", "--data-root=data"],
            ):
                with self.subTest(command=command):
                    self.assertEqual(
                        [],
                        MODULE.validate_command_argv(
                            command,
                            label="command",
                            repo_root=repo,
                            workspace_root=workspace,
                        ),
                    )

    def test_rejects_data_root_outside_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "workspace"
            repo = workspace / "repo"
            (workspace / "ai_ops" / "00_Admin" / "scripts").mkdir(parents=True)
            (repo / "scripts").mkdir(parents=True)
            (repo / "scripts" / "validate.py").write_text("", encoding="utf-8")

            for command in (
                ["python", "scripts/validate.py", "--data-root", "../../outside"],
                ["python", "scripts/validate.py", "--data-root=C:\\outside"],
            ):
                with self.subTest(command=command):
                    self.assertTrue(
                        MODULE.validate_command_argv(
                            command,
                            label="command",
                            repo_root=repo,
                            workspace_root=workspace,
                        )
                    )

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
