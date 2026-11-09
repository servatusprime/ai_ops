import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".ai_ops" / "workflows" / "work_savepoint.md"
CLOSEOUT_WORKFLOW = REPO_ROOT / ".ai_ops" / "workflows" / "closeout.md"
CROSSCHECK_WORKFLOW = REPO_ROOT / ".ai_ops" / "workflows" / "crosscheck.md"
GOVERNANCE_GRAPH = (
    REPO_ROOT
    / "00_Admin"
    / "reports"
    / "generated"
    / "graphs"
    / "governance_routing_graph.yaml"
)


class WorkSavepointContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.savepoint = " ".join(cls.workflow.split())
        cls.closeout = " ".join(
            CLOSEOUT_WORKFLOW.read_text(encoding="utf-8").split()
        )
        cls.crosscheck = " ".join(
            CROSSCHECK_WORKFLOW.read_text(encoding="utf-8").split()
        )

    def test_publication_requires_preview_and_combined_approval(self) -> None:
        required = (
            "## Purpose",
            "default invocation is a read-only checkpoint",
            "Publication Preview and Approval Gates",
            "exact repo-relative `include`",
            "proposed `savepoint: <brief description>` message",
            "Stop and ask once for approval",
            "Re-run status and the safety preflight after approval",
            "git -C <repo_root> add --",
            "git diff --cached --name-only",
            "push <approved_remote> <approved_branch>",
        )
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, self.savepoint)

    def test_flags_cannot_bypass_approval(self) -> None:
        self.assertIn(
            "Pass `--no-commit` to state the read-only intent explicitly",
            self.workflow,
        )
        self.assertIn("`--commit` to request publication", self.savepoint)
        self.assertIn(
            "initial invocation cannot substitute for this combined approval",
            self.savepoint,
        )

    def test_scope_and_failure_guards_are_explicit(self) -> None:
        required = (
            "`related_scope_requires_confirmation`",
            "`ignored_unpublished`",
            "Never use `git add -f`",
            "Never silently widen or substitute the approved set",
            "git diff --cached --name-only",
            "push_escalation: pr_required",
            "push_escalation: auth_failure",
            "Do not force, change the remote",
            "Create or update the PR through the GitHub provider",
            "artifacts remain `in_progress`",
        )
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, self.savepoint)

    def test_applicability_and_projected_tree_contracts_are_explicit(self) -> None:
        for marker in (
            "Future-Work Applicability Gate",
            "not_applicable",
            "linked_only",
            "completion_handoff",
            "registry_sync",
            "closeout_applicability.py",
            "projected_include_tree",
            "excluded_scope_conflict",
            "ignored_unpublished",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.savepoint)
                self.assertIn(marker, self.closeout)
        self.assertIn("## Workflow graph", self.workflow)
        self.assertIn("## Workflow graph", self.closeout)
        self.assertIn("without invoking a classifier", self.closeout)

    def test_fresh_reader_terms_and_rebinding_rules_are_explicit(self) -> None:
        for marker in (
            "Selection terms are explicit",
            "active artifact",
            "target_repo",
            "Classify `include`",
            "A validator qualifies for projected-tree execution",
            "scope_pending_confirmation",
            "projected_tree_ready",
            "The policy file is the target's",
            "git config --get core.hooksPath",
            "new approval binding whenever the rerun changes",
            "A `preparation record` is the records-only closeout output",
            "`linked_only` carries one or more linked IDs as",
        ):
            with self.subTest(closeout_marker=marker):
                self.assertIn(marker, self.closeout)
        for marker in (
            "An `active artifact` is an entry",
            "Classify `include` as exact approved paths",
            "scope_pending_confirmation",
            "projected_tree_ready",
            "The policy file is the target's",
            "The fallback requires a new approval",
            "Read them in that order as applicable",
            "A `checkpoint record` is the records-only savepoint output",
            "`linked_only` carries one or more linked IDs as",
            "Its read-only leg may write only the checkpoint record",
            "Any Git error or empty returned path is",
            "dispatcher configuration also yields",
            "Resources: `00_Admin/configs/context_routing.yaml`, the selected",
        ):
            with self.subTest(savepoint_marker=marker):
                self.assertIn(marker, self.savepoint)

    def test_savepoint_has_no_archive_step(self) -> None:
        for marker in (
            "Savepoint is an active-work checkpoint and has no archive step",
            "route the work through `/closeout`",
            "active-work paths that do not require archival",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.savepoint)
        self.assertNotIn("archive_gate", self.savepoint)
        self.assertIn("Archive and Completion Boundary", self.closeout)

    def test_validation_scope_matches_workflow_lifecycle(self) -> None:
        for marker in (
            "Validation Scope",
            "focused contract tests",
            "Do not require the full ai_ops test suite for each savepoint iteration",
            "the full repository regression suite belongs to the final `/closeout` publication gate",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.savepoint)
        for marker in (
            "the full repository regression suite once after final edits and before publication",
            "Do not repeat the full suite for every intermediate edit",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.closeout)

    def test_packet_capacity_does_not_create_commit_churn(self) -> None:
        self.assertIn("Review Capacity Boundary", self.savepoint)
        self.assertIn("Review Capacity Boundary", self.closeout)
        for marker in (
            "Tier 1 is a self-crosscheck",
            "tier 2 runs once",
            "at most 2 separate-session delta passes",
            "consumes the same counter",
            "no aggregate review-token ceiling",
            "emit `PARK`",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.crosscheck)
        for marker in ("200,000", "token ledger", "parked ceiling"):
            with self.subTest(no_duplicate_marker=marker):
                self.assertNotIn(marker, self.savepoint)
                self.assertNotIn(marker, self.closeout)
        self.assertIn("A savepoint remains a records-only checkpoint", self.savepoint)
        self.assertIn("Closeout uses one final commit", self.closeout)

    def test_governed_security_admission_is_shared_and_fail_closed(self) -> None:
        shared = (
            "policy_source=missing_target_policy",
            "security_admission: unavailable",
            "fw_20261026_01",
            "manual waiver",
        )
        for marker in shared:
            with self.subTest(marker=marker):
                self.assertIn(marker, self.savepoint)
                self.assertIn(marker, self.closeout)
        self.assertIn("Governed-Repository Security Admission", self.workflow)
        self.assertIn(
            "same target-repository security admission decision as `/closeout`",
            self.savepoint,
        )
        self.assertIn("rb_closeout_security_review_01.md", self.savepoint)
        self.assertIn("rb_closeout_security_review_01.md", self.closeout)

    def test_generated_governance_graph_keeps_closeout_membership(self) -> None:
        graph = GOVERNANCE_GRAPH.read_text(encoding="utf-8")
        for marker in (
            "id: command:closeout",
            "id: workflow:.ai_ops/workflows/closeout.md",
            "source: command:closeout",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, graph)

    def test_closeout_archive_precedes_publication(self) -> None:
        archive = self.closeout.index("Archive and Completion Boundary")
        archive_rows = self.closeout.index("Prepare exact source/destination rows")
        archive_approval = self.closeout.index(
            "Present those rows in the existing container-completion decision"
        )
        archive_move = self.closeout.index("execute the exact move")
        stale_reference = self.closeout.index("After a move, run stale-reference checks")
        packet = self.closeout.index("build one packet")
        security = self.closeout.index("## Security Admission")
        commit = self.closeout.index("Commit only after required checks pass")
        push = self.closeout.index("Push only after the push row is approved")
        merge = self.closeout.index("Create/update and merge only after the merge row is approved")
        self.assertLess(archive, archive_rows)
        self.assertLess(archive_rows, archive_approval)
        self.assertLess(archive_approval, archive_move)
        self.assertLess(archive_move, stale_reference)
        self.assertLess(stale_reference, packet)
        self.assertLess(archive, security)
        self.assertLess(security, commit)
        self.assertLess(security, packet)
        self.assertLess(packet, commit)
        self.assertLess(commit, push)
        self.assertLess(push, merge)
        self.assertNotIn("container completion/archive decision", self.closeout)
        for marker in (
            "archive_gate: passed",
            "archive_gate: unavailable",
            "selected source remains",
            "do not stage, commit, push, create/update a PR, or merge",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.closeout)

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
