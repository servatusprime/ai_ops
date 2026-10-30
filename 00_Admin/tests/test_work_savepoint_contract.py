import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".ai_ops" / "workflows" / "work_savepoint.md"
CLOSEOUT_WORKFLOW = REPO_ROOT / ".ai_ops" / "workflows" / "closeout.md"


class WorkSavepointContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.normalized = " ".join(cls.workflow.split())

    def test_publication_requires_preview_and_combined_approval(self) -> None:
        required = (
            "## Purpose",
            "default invocation is a read-only checkpoint",
            "Publication Preview and Approval Gates",
            "exact repo-relative `include`",
            "proposed `savepoint: <brief description>` commit message",
            "Stop and ask once for approval",
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
            "Pass `--no-commit` to state the read-only intent explicitly",
            self.workflow,
        )
        self.assertIn(
            "`--commit` to request publication",
            self.normalized,
        )
        self.assertIn(
            "initial invocation cannot substitute for the combined approval",
            self.normalized,
        )
        self.assertNotIn("an explicit spelling of the default save intent", self.workflow)

    def test_scope_and_failure_guards_are_explicit(self) -> None:
        required = (
            "`related_scope_requires_confirmation`",
            "`ignored_unpublished`",
            "Never use `git add -f`",
            "Never silently widen or substitute the approved set",
            "Do not force, change the remote",
            "Create or update the PR through the GitHub provider",
            "artifacts remain `in_progress`",
        )
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, self.normalized)

    def test_applicability_and_projected_tree_contracts_are_explicit(self) -> None:
        closeout = " ".join(CLOSEOUT_WORKFLOW.read_text(encoding="utf-8").split())
        required = (
            "Future-Work Applicability Gate",
            "not_applicable",
            "linked_only",
            "completion_handoff",
            "registry_sync",
            "closeout_applicability.py",
            "Projected-Tree Validation Boundary",
            "closeout_scope.py",
            "projected_include_tree",
            "excluded_scope_conflict",
            "ignored_unpublished",
        )
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, self.normalized)
                self.assertIn(marker, closeout)

    def test_savepoint_has_no_archive_step(self) -> None:
        closeout = " ".join(CLOSEOUT_WORKFLOW.read_text(encoding="utf-8").split())
        for marker in (
            "Savepoint is an active-work checkpoint and has no archive step",
            "route the work through `/closeout`",
            "active-work paths that do not require archival",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.normalized)
        self.assertNotIn("archive_gate", self.normalized)
        self.assertIn("Archive Applicability Boundary", closeout)

    def test_governed_security_admission_is_shared_and_fail_closed(self) -> None:
        closeout = " ".join(CLOSEOUT_WORKFLOW.read_text(encoding="utf-8").split())
        shared = (
            "policy_source=missing_target_policy",
            "security_admission: unavailable",
            "fw_20261026_01",
            "manual waiver",
        )
        for marker in shared:
            with self.subTest(marker=marker):
                self.assertIn(marker, self.normalized)
                self.assertIn(marker, closeout)
        self.assertIn("Governed-Repository Security Admission", self.workflow)
        self.assertIn(
            "same target-repository security admission decision as `/closeout`",
            self.normalized,
        )

    def test_closeout_archive_gate_precedes_publication(self) -> None:
        closeout = " ".join(CLOSEOUT_WORKFLOW.read_text(encoding="utf-8").split())
        archive = closeout.index("Archive completed work artifacts to `99_Trash/`")
        security = closeout.index(
            "Run the closeout security admission gate only after `archive_gate: passed`"
        )
        commit = closeout.index("Commit only after the commit gate passed, the archive result is")
        push = closeout.index(
            "Push only after the combined approval turn's push row is approved, "
            "the archive gate remains `passed` when applicable"
        )
        merge = closeout.index(
            "After the final push, execute the merge phase only when the combined "
            "approval turn's PR/merge row is approved and the archive gate remains `passed` when applicable"
        )
        self.assertLess(archive, security)
        self.assertLess(security, commit)
        self.assertLess(commit, push)
        self.assertLess(push, merge)
        for marker in (
            "archive_gate: passed",
            "archive_gate: unavailable",
            "source remains under `90_Sandbox/`",
            "do not stage, commit, push, create/update a PR, or merge",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, closeout)

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
