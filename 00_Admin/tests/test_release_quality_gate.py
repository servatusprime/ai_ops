"""Regression tests for release-gate diagnostic output."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "00_Admin" / "scripts" / "run_release_quality_gate.py"
SPEC = importlib.util.spec_from_file_location("run_release_quality_gate", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ReleaseQualityGateTests(unittest.TestCase):
    def test_safe_console_text_handles_legacy_windows_encoding(self) -> None:
        rendered = MODULE._safe_console_text("diagnostic: \u2014 \ufffd", "cp1252")

        self.assertEqual("diagnostic: — \\ufffd", rendered)

    def test_resolve_trusted_python_runtime_returns_concrete_executable(self) -> None:
        resolved = MODULE.resolve_trusted_python_runtime()

        self.assertIsNotNone(resolved)
        self.assertTrue(Path(resolved).is_file())

    def test_gate_collects_all_failures_before_reporting_result(self) -> None:
        observed = []

        def fake_run_check(name, cmd, cwd, dry_run):
            observed.append(name)
            return name, 1 if name == "governance-tests" else 0

        with patch.object(MODULE, "run_check", side_effect=fake_run_check), patch.object(
            MODULE.sys, "argv", ["run_release_quality_gate.py"]
        ), patch.object(MODULE, "detect_git_root", return_value=ROOT):
            result = MODULE.main()

        self.assertEqual(1, result)
        self.assertGreater(len(observed), 1)
        self.assertEqual("governance-tests", observed[0])

    def test_run_check_omits_command_paths_from_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            cwd = Path(temp_dir)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                name, result = MODULE.run_check(
                    "repo-validator",
                    [r"C:\secret\python.exe", "validator.py", "--structure-root", str(cwd)],
                    cwd=cwd,
                    dry_run=True,
                )

            self.assertEqual("repo-validator", name)
            self.assertEqual(0, result)
            rendered = output.getvalue()
            self.assertIn("arguments omitted from logs", rendered)
            self.assertNotIn(str(cwd), rendered)
            self.assertNotIn("C:\\secret", rendered)

    def test_run_check_does_not_inherit_child_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            cwd = Path(temp_dir)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                name, result = MODULE.run_check(
                    "repo-validator",
                    [sys.executable, "-c", "print('C:/secret/child-output.txt')"],
                    cwd=cwd,
                    dry_run=False,
                )

            self.assertEqual("repo-validator", name)
            self.assertEqual(0, result)
            self.assertNotIn("C:/secret/child-output.txt", output.getvalue())

    def test_run_check_summarizes_failure_without_child_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            cwd = Path(temp_dir)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                name, result = MODULE.run_check(
                    "repo-validator",
                    [
                        sys.executable,
                        "-c",
                        "import sys; print('C:/secret/failure.txt'); sys.exit(1)",
                    ],
                    cwd=cwd,
                    dry_run=False,
                )

            self.assertEqual("repo-validator", name)
            self.assertEqual(1, result)
            rendered = output.getvalue()
            self.assertNotIn("C:/secret/failure.txt", rendered)
            self.assertIn("<external-path>", rendered)
            self.assertIn("child diagnostics (sanitized)", rendered)


if __name__ == "__main__":
    unittest.main()
