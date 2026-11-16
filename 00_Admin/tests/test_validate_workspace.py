"""Tests for validate_workspace.py: one engine, each registered repo's own config."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_workspace.py"
spec = importlib.util.spec_from_file_location("validate_workspace", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

CONFIG = "00_Admin/configs/validator/validator_config.yaml"
CONFIG_TEXT = "version: 0.1.1\nvalidator_id: validator_v1\nrules:\n  - id: VS040\n    enabled: true\n"


def make_repo(root: Path, name: str, with_workbook: bool, with_config: bool = True) -> None:
    repo = root / name
    bundle = repo / "90_Sandbox/ai_workbooks/wb_a"
    bundle.mkdir(parents=True)
    (bundle / "README.md").write_text("---\nauthority_level: 3\n---\n# A\n", encoding="utf-8")
    if with_workbook:
        (bundle / "wb_x.md").write_text("x\n", encoding="utf-8")
    if with_config:
        (repo / "00_Admin/configs/validator").mkdir(parents=True)
        (repo / CONFIG).write_text(CONFIG_TEXT, encoding="utf-8")


class WorkspaceRunnerTests(unittest.TestCase):
    def run_runner(
        self, root: Path, names: list[str], *extra: str, cwd: Path | None = None
    ) -> subprocess.CompletedProcess:
        local = root / "local_config.yaml"
        entries = "".join(f"    - path: {name}/\n" for name in names)
        local.write_text(f"workspace:\n  work_repos:\n{entries}", encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--local-config", str(local), "--workspace-root", str(root), *extra],
            capture_output=True,
            text=True,
            cwd=cwd,
        )

    def test_target_dot_works_from_inside_the_reviewed_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_repo(root, "good", with_workbook=True)
            make_repo(root, "bad", with_workbook=False)
            self.assertEqual(self.run_runner(root, ["good", "bad"], "--target", ".", cwd=root / "good").returncode, 0)
            self.assertEqual(self.run_runner(root, ["good", "bad"], "--target", ".", cwd=root / "bad").returncode, 1)

    def test_target_result_sets_the_exit_code_and_other_repos_only_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_repo(root, "good", with_workbook=True)
            make_repo(root, "bad", with_workbook=False)
            make_repo(root, "unconfigured", with_workbook=True, with_config=False)
            names = ["good", "bad", "unconfigured"]
            self.assertEqual(self.run_runner(root, names, "--target", "good").returncode, 0)
            blocked = self.run_runner(root, names, "--target", "bad")
            self.assertEqual(blocked.returncode, 1)
            self.assertIn("FAIL", blocked.stdout)
            self.assertIn("no validator config", blocked.stdout)
            self.assertEqual(self.run_runner(root, names).returncode, 1)

    def test_unregistered_target_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_repo(root, "good", with_workbook=True)
            self.assertEqual(self.run_runner(root, ["good"], "--target", "elsewhere").returncode, 2)

    def test_hook_state_reads_the_hook_stage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self.assertEqual(mod.hook_state(repo), "no commit hook found")
            hook = (
                "repos:\n  - repo: local\n    hooks:\n      - id: v\n"
                "        entry: python x/validate_repo_rules.py\n"
            )
            (repo / ".pre-commit-config.yaml").write_text(hook + "        stages: [manual]\n", encoding="utf-8")
            self.assertEqual(mod.hook_state(repo), "not at commit (stage: manual)")
            (repo / ".pre-commit-config.yaml").write_text(hook + "        stages: [pre-push]\n", encoding="utf-8")
            self.assertEqual(mod.hook_state(repo), "not at commit (stage: pre-push)")
            (repo / ".pre-commit-config.yaml").write_text(hook + "        stages: [pre-commit]\n", encoding="utf-8")
            self.assertEqual(mod.hook_state(repo), "runs at commit")

    def test_missing_local_config_exits_2_without_a_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run = subprocess.run(
                [sys.executable, str(SCRIPT), "--local-config", str(Path(tmp, "none.yaml")), "--workspace-root", tmp],
                capture_output=True,
                text=True,
            )
            self.assertEqual(run.returncode, 2)
            self.assertNotIn("Traceback", run.stderr)

    def test_require_hook_fails_a_repo_without_a_commit_hook(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_repo(root, "good", with_workbook=True)
            self.assertEqual(self.run_runner(root, ["good"], "--target", "good").returncode, 0)
            self.assertEqual(self.run_runner(root, ["good"], "--target", "good", "--require-hook").returncode, 1)


if __name__ == "__main__":
    unittest.main()
