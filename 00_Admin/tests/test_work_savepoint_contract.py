import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".ai_ops" / "workflows" / "work_savepoint.md"


class WorkSavepointContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.normalized = " ".join(cls.workflow.split())

    def test_publication_requires_preview_and_final_approval(self) -> None:
        required = (
            "## Purpose",
            "Invocation expresses",
            "Publication Preview and Final Approval Gate",
            "exact repo-relative `include`",
            "proposed `savepoint: <brief description>` commit message",
            "Stop and ask for explicit approval",
            "Revalidation After Approval",
            "git -C <repo_root> add --",
            "git diff --cached --name-only",
            "push <approved_remote> <approved_branch>",
        )
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, self.normalized)

    def test_flags_cannot_bypass_approval(self) -> None:
        self.assertIn(
            "Pass `--no-commit` to create a read-only checkpoint",
            self.workflow,
        )
        self.assertIn(
            "an explicit spelling of the default save intent",
            self.normalized,
        )
        self.assertIn(
            "initial invocation cannot substitute for this final approval",
            self.normalized,
        )
        self.assertNotIn("Any compatibility `--commit` flag remains inert", self.workflow)

    def test_scope_and_failure_guards_are_explicit(self) -> None:
        required = (
            "`related_scope_requires_confirmation`",
            "`ignored_unpublished`",
            "Never use `git add -f`",
            "Never silently widen or substitute the approved set",
            "Do not force, create a PR, change the remote",
            "artifacts remain `in_progress`",
        )
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, self.normalized)

    def test_declared_documentation_and_smoke_contract_match(self) -> None:
        surfaces = {
            "setup": REPO_ROOT / ".ai_ops" / "setup" / "README.md",
            "command-guide": (
                REPO_ROOT
                / "00_Admin"
                / "guides"
                / "ai_operations"
                / "guide_command_workflows.md"
            ),
            "classification": (
                REPO_ROOT
                / "00_Admin"
                / "guides"
                / "ai_operations"
                / "guide_skills_commands_classification.md"
            ),
            "smoke": REPO_ROOT / "00_Admin" / "tests" / "workflow_smoke_tests.yaml",
        }
        for name, path in surfaces.items():
            text = path.read_text(encoding="utf-8")
            lowered = text.lower()
            with self.subTest(surface=name):
                self.assertIn("work_savepoint", text)
                self.assertTrue(
                    "final approval" in lowered or "approval-gated" in lowered,
                    f"{name} does not describe the approval-gated save contract",
                )


if __name__ == "__main__":
    unittest.main()
