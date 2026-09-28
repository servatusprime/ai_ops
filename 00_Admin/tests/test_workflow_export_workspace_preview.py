from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATOR = REPO_ROOT / "00_Admin" / "scripts" / "generate_workflow_exports.py"


class WorkspaceInstallPreviewTests(unittest.TestCase):
    def run_generator(self, install_root: Path, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                "-B",
                str(GENERATOR),
                "--targets",
                "codex",
                "--scope",
                "workspace",
                "--install-root",
                str(install_root),
                *extra,
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    @staticmethod
    def preview_token(result: subprocess.CompletedProcess[str]) -> str:
        match = re.search(r"^Preview token: ([A-F0-9]{16})$", result.stdout, re.MULTILINE)
        if not match:
            raise AssertionError(f"preview token missing from output:\n{result.stdout}")
        return match.group(1)

    def test_workspace_install_blocks_before_any_write_and_lists_complete_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            install_root = Path(temp_dir)
            result = self.run_generator(install_root)

            self.assertEqual(result.returncode, 2)
            self.assertIn("[Workspace install preview]", result.stdout)
            self.assertIn("[BLOCKED] Workspace install requires the matching preview token.", result.stdout)
            self.assertIn(r".agents\skills\bootstrap\SKILL.md", result.stdout)
            self.assertIn(r".agents\skills\work_savepoint\SKILL.md", result.stdout)
            self.assertFalse((install_root / ".agents").exists())

    def test_matching_preview_token_allows_exact_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            install_root = Path(temp_dir)
            preview = self.run_generator(install_root, "--dry-run")
            token = self.preview_token(preview)

            self.assertEqual(preview.returncode, 0)
            self.assertIn("Dry run: no files written.", preview.stdout)
            self.assertFalse((install_root / ".agents").exists())

            apply_result = self.run_generator(install_root, "--approve-preview", token)
            self.assertEqual(apply_result.returncode, 0, apply_result.stdout + apply_result.stderr)
            self.assertTrue(
                (install_root / ".agents" / "skills" / "work_savepoint" / "SKILL.md").is_file()
            )

    def test_destination_change_invalidates_prior_token(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            install_root = Path(temp_dir)
            preview = self.run_generator(install_root, "--dry-run")
            token = self.preview_token(preview)

            changed_path = install_root / ".agents" / "skills" / "bootstrap" / "SKILL.md"
            changed_path.parent.mkdir(parents=True)
            changed_path.write_text("preexisting owner content\n", encoding="utf-8")

            apply_result = self.run_generator(install_root, "--approve-preview", token)
            self.assertEqual(apply_result.returncode, 2)
            self.assertIn("[BLOCKED]", apply_result.stdout)
            self.assertEqual(changed_path.read_text(encoding="utf-8"), "preexisting owner content\n")


if __name__ == "__main__":
    unittest.main()
