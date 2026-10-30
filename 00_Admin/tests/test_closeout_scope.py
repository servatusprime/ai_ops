"""Focused tests for projected-tree and excluded-scope reporting."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from closeout_scope import scope_report


class CloseoutScopeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp_dir.name)
        self._git("init", "-b", "main")
        self._git("config", "user.email", "scope@example.invalid")
        self._git("config", "user.name", "Scope Tests")
        (self.repo / ".gitignore").write_text("ignored.txt\n", encoding="utf-8")
        (self.repo / "included.py").write_text("before\n", encoding="utf-8")
        (self.repo / "runbook.md").write_text("before\n", encoding="utf-8")
        self._git("add", ".")
        self._git("commit", "-m", "baseline")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(self.repo), *args],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        return result.stdout.strip()

    def _dirty_scope(self) -> None:
        (self.repo / "included.py").write_text("included change\n", encoding="utf-8")
        (self.repo / "runbook.md").write_text("excluded runbook change\n", encoding="utf-8")
        (self.repo / "stray.txt").write_text("unrelated\n", encoding="utf-8")
        (self.repo / "ignored.txt").write_text("ignored\n", encoding="utf-8")

    def test_excluded_validator_input_is_reported_without_staging(self) -> None:
        self._dirty_scope()
        report = scope_report(self.repo, ["included.py"], validator_inputs=["runbook.md"])
        self.assertEqual("excluded_scope_conflict", report["status"])
        self.assertEqual(["runbook.md", "stray.txt"], report["dirty_worktree"]["exclude"])
        self.assertEqual(["ignored.txt"], report["dirty_worktree"]["ignored_unpublished"])
        self.assertEqual(["runbook.md"], report["excluded_scope_conflict"]["paths"])
        self.assertEqual([], self._git("diff", "--cached", "--name-only").splitlines())

    def test_validator_input_in_projected_include_tree_is_ready(self) -> None:
        self._dirty_scope()
        report = scope_report(self.repo, ["included.py"], validator_inputs=["included.py"])
        self.assertEqual("projected_tree_ready", report["status"])
        self.assertEqual("projected_include_tree", report["validation_tree"])
        self.assertIsNone(report["excluded_scope_conflict"])
        self.assertEqual(["included.py"], report["projected_include_tree"]["paths"])


if __name__ == "__main__":
    unittest.main()
