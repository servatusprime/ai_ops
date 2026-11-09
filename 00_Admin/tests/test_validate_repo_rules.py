"""Focused tests for VS024 workbook frontmatter topology validation."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_repo_rules.py"
spec = importlib.util.spec_from_file_location("validate_repo_rules", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


VALID_FRONTMATTER = """---
title: Test workbook
model_profile: reasoning:high | standard:medium
ai_role: executor
execution_topology: hybrid
activated_lanes:
  - Coordinator
  - Executor
  - Reviewer
delegation_policy: explicit_only
convergence_profile: iterative_convergence_standard
---

# Test workbook
"""


class WorkbookTopologyContractTests(unittest.TestCase):
    def run_check(self, frontmatter: str) -> tuple[list[str], list[str]]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "wb_test.md"
            path.write_text(frontmatter, encoding="utf-8")
            errors: list[str] = []
            warnings: list[str] = []
            mod.check_workbook_topology_contract(
                [str(path)], errors, warnings, "error", "VS024"
            )
            return errors, warnings

    def test_valid_frontmatter_passes(self) -> None:
        errors, warnings = self.run_check(VALID_FRONTMATTER)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_invalid_topology_vocabulary_is_rejected(self) -> None:
        invalid = VALID_FRONTMATTER.replace(
            "execution_topology: hybrid", "execution_topology: distributed"
        ).replace("  - Reviewer", "  - Reviewer\n  - Reviewer")
        invalid = invalid.replace(
            "delegation_policy: explicit_only", "delegation_policy: guess"
        ).replace(
            "convergence_profile: iterative_convergence_standard",
            "convergence_profile: custom",
        )
        errors, _ = self.run_check(invalid)
        self.assertGreaterEqual(len(errors), 4)
        self.assertTrue(any("execution_topology" in error for error in errors))
        self.assertTrue(any("duplicates" in error for error in errors))
        self.assertTrue(any("delegation_policy" in error for error in errors))
        self.assertTrue(any("convergence_profile" in error for error in errors))

    def test_unknown_model_profile_is_rejected(self) -> None:
        invalid = VALID_FRONTMATTER.replace(
            "model_profile: reasoning:high | standard:medium", "model_profile: banana"
        )
        errors, _ = self.run_check(invalid)
        self.assertTrue(any("model_profile" in error for error in errors))

    def test_optional_role_assignments_must_use_model_levels(self) -> None:
        invalid = VALID_FRONTMATTER.replace(
            "---\n\n# Test workbook",
            "role_assignments:\n  reviewer: maximum\n---\n\n# Test workbook",
        )
        errors, _ = self.run_check(invalid)
        self.assertTrue(any("role_assignments" in error for error in errors))

    def test_required_routing_fields_cannot_be_empty(self) -> None:
        invalid = VALID_FRONTMATTER.replace(
            "model_profile: reasoning:high | standard:medium", "model_profile: ''"
        ).replace(
            "activated_lanes:\n  - Coordinator\n  - Executor\n  - Reviewer",
            "activated_lanes: []",
        )
        errors, _ = self.run_check(invalid)
        self.assertTrue(any("model_profile" in error for error in errors))
        self.assertTrue(any("activated_lanes" in error for error in errors))

    def test_missing_ai_role_is_rejected(self) -> None:
        invalid = VALID_FRONTMATTER.replace("ai_role: executor\n", "")
        errors, _ = self.run_check(invalid)
        self.assertTrue(any("ai_role" in error for error in errors))

    def test_template_passes_vs024(self) -> None:
        template = (
            Path(__file__).resolve().parents[2]
            / "01_Resources"
            / "templates"
            / "workflows"
            / "wb_template_generic.md"
        )
        errors: list[str] = []
        warnings: list[str] = []
        mod.check_required_sections(
            [str(template)],
            [
                "## Cold-Start Execution Contract",
                "## Pre-Execution Readiness Gate",
                "## Ordered Execution Queue",
                "## Verification Checklist",
                "## Selfcheck Results",
            ],
            errors,
            warnings,
            "error",
            "VS024",
        )
        mod.check_workbook_topology_contract([str(template)], errors, warnings, "error", "VS024")
        self.assertEqual(errors, [])

    def test_malformed_non_scalar_values_report_errors_without_crashing(self) -> None:
        invalid = VALID_FRONTMATTER.replace(
            "execution_topology: hybrid", "execution_topology: {kind: hybrid}"
        ).replace(
            "  - Reviewer", "  - {name: Reviewer}"
        ).replace(
            "delegation_policy: explicit_only", "delegation_policy: [explicit_only]"
        ).replace(
            "convergence_profile: iterative_convergence_standard",
            "convergence_profile: {name: standard}",
        )
        errors, _ = self.run_check(invalid)
        self.assertGreaterEqual(len(errors), 4)


if __name__ == "__main__":
    unittest.main()
