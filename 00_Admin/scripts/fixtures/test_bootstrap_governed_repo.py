#!/usr/bin/env python
"""Fixture tests for the governed-repository bootstrap command."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from bootstrap_governed_repo import bootstrap  # noqa: E402


class BootstrapFixtures(unittest.TestCase):
    def _roots(self) -> tuple[Path, Path, Path]:
        base = Path(self.tmp.name)
        workspace = base / "workspace"
        ai_ops = workspace / "ai_ops"
        target = workspace / "new_repo"
        (ai_ops / ".ai_ops/local").mkdir(parents=True)
        (ai_ops / "00_Admin/configs").mkdir(parents=True)
        (ai_ops / "00_Admin/configs/setup_contract.yaml").write_text(
            "setup_contract:\n  required_version: '1.0.0'\n",
            encoding="utf-8",
        )
        return workspace, ai_ops, target

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_domain_bootstrap_registers_and_validates(self) -> None:
        workspace, ai_ops, target = self._roots()
        self.assertEqual(bootstrap(target, ai_ops, workspace, "src", None), [])
        self.assertTrue((target / "src").is_dir())
        self.assertIn("new_repo/", (ai_ops / ".ai_ops/local/config.yaml").read_text())

    def test_exception_bootstrap_writes_evidence_and_validates(self) -> None:
        workspace, ai_ops, target = self._roots()
        self.assertEqual(
            bootstrap(target, ai_ops, workspace, None, "empty-domain-01"), []
        )
        self.assertIn(
            "exception_id: empty-domain-01",
            (target / "README.md").read_text(encoding="utf-8"),
        )

    def test_existing_registration_preserves_comments_and_formatting(self) -> None:
        workspace, ai_ops, target = self._roots()
        registration = ai_ops / ".ai_ops/local/config.yaml"
        registration.write_text(
            "version: 0.2.0\n"
            "workspace:\n"
            "  # operator note stays in place\n"
            "  work_repos:\n"
            "    - path: existing_repo/\n"
            "      sandbox_dir: 90_Sandbox\n"
            "  resource_repos: []\n",
            encoding="utf-8",
        )

        self.assertEqual(bootstrap(target, ai_ops, workspace, "src", None), [])
        updated = registration.read_text(encoding="utf-8")
        self.assertIn("# operator note stays in place", updated)
        self.assertIn("    - path: existing_repo/\n", updated)
        self.assertIn("  resource_repos: []\n", updated)
        self.assertIn("    - path: new_repo/\n", updated)

    def test_domain_path_cannot_escape_repo(self) -> None:
        workspace, ai_ops, target = self._roots()
        with self.assertRaisesRegex(ValueError, "escapes repository root"):
            bootstrap(target, ai_ops, workspace, "../outside", None)


if __name__ == "__main__":
    unittest.main()
