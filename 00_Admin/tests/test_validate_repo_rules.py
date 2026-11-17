"""Focused tests for VS024 workbook frontmatter topology validation."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
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


class WorkbookPresenceTests(unittest.TestCase):
    """VS040: every bundle or program folder has a README and, at authority_level 3 or higher, a workbook."""

    BUNDLE = "90_Sandbox/ai_workbooks/wb_a"

    def run_check(self, files: dict[str, str], baseline: list[str] | None = None) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            for name, text in files.items():
                path = Path(tmp, name)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
            errors: list[str] = []
            warnings: list[str] = []
            mod.check_workbook_presence(
                tmp,
                list(mod._DEFAULT_CONTAINER_GLOBS),
                3,
                "wb_*.md",
                baseline or [],
                errors,
                warnings,
                "error",
                "VS040",
            )
            return errors

    def readme(self, level_line: str) -> dict[str, str]:
        return {f"{self.BUNDLE}/README.md": f"---\n{level_line}\n---\n# A\n"}

    def test_level_3_readme_without_workbook_is_flagged(self) -> None:
        errors = self.run_check(self.readme("authority_level: 3"))
        self.assertEqual(len(errors), 1)
        self.assertIn("VS040", errors[0])

    def test_a_workbook_satisfies_the_folder(self) -> None:
        files = self.readme("authority_level: 3")
        files[f"{self.BUNDLE}/wb_x.md"] = "x"
        self.assertEqual(self.run_check(files), [])

    def test_nested_workbook_satisfies_a_program(self) -> None:
        files = {
            "90_Sandbox/ai_workbooks/work_program_p/README.md": "---\nauthority_level: 4\n---\n",
            "90_Sandbox/ai_workbooks/work_program_p/work_packets/b/wb_x.md": "x",
        }
        self.assertEqual(self.run_check(files), [])

    def test_level_below_3_needs_no_workbook(self) -> None:
        self.assertEqual(self.run_check(self.readme("authority_level: 2")), [])

    def test_missing_readme_is_flagged(self) -> None:
        errors = self.run_check({f"{self.BUNDLE}/notes.md": "x"})
        self.assertEqual(len(errors), 1)
        self.assertIn("no README.md", errors[0])

    def test_missing_or_unreadable_level_counts_as_level_3(self) -> None:
        for readme in (
            "---\nstatus: active\n---\n",
            "---\nauthority_level: TBD\n---\n",
            "---\nauthority_level: # 0-4\n---\n",
            "# no frontmatter\n",
        ):
            errors = self.run_check({f"{self.BUNDLE}/README.md": readme})
            self.assertEqual(len(errors), 1, readme)
            self.assertIn("needs at least one", errors[0])
            with_workbook = {f"{self.BUNDLE}/README.md": readme, f"{self.BUNDLE}/wb_x.md": "x"}
            self.assertEqual(self.run_check(with_workbook), [], readme)

    def test_level_forms_that_carry_a_number_are_read(self) -> None:
        for value in ("3", '"3"', "Level 3", "3  # note", "L3"):
            errors = self.run_check(self.readme(f"authority_level: {value}"))
            self.assertEqual(len(errors), 1, value)
        self.assertEqual(self.run_check(self.readme("authority_level: Level 2")), [])

    def test_bom_is_skipped_and_nested_keys_do_not_override(self) -> None:
        bom = self.run_check({f"{self.BUNDLE}/README.md": "\ufeff---\nauthority_level: 3\n---\n"})
        self.assertEqual(len(bom), 1)
        nested = self.run_check(
            {f"{self.BUNDLE}/README.md": "---\nauthority_level: 3\nother:\n  authority_level: 2\n---\n"}
        )
        self.assertEqual(len(nested), 1)

    def test_workbook_in_a_sibling_folder_does_not_count(self) -> None:
        files = self.readme("authority_level: 3")
        files["90_Sandbox/ai_workbooks/wb_b/wb_x.md"] = "x"
        self.assertEqual(len(self.run_check(files)), 2)  # wb_a lacks a workbook; wb_b lacks a README

    def test_loose_files_and_unrelated_folders_are_ignored(self) -> None:
        files = {"90_Sandbox/ai_workbooks/wb_loose.md": "x", "90_Sandbox/ai_workbooks/notes/README.md": "x"}
        self.assertEqual(self.run_check(files), [])

    def test_baseline_exclude_skips_a_listed_folder(self) -> None:
        files = {f"{self.BUNDLE}/notes.md": "x"}
        self.assertEqual(self.run_check(files, baseline=[self.BUNDLE]), [])

    def test_nested_and_differently_named_readmes_at_level_3_need_their_own_workbook(self) -> None:
        files = self.readme("authority_level: 3")
        files[f"{self.BUNDLE}/wb_x.md"] = "x"
        files[f"{self.BUNDLE}/sub/README.md"] = "---\nauthority_level: 3\n---\n"
        files["90_Sandbox/ai_workbooks/audit_x/README.md"] = "---\nauthority_level: 3\n---\n"
        files["90_Sandbox/ai_workbooks/audit_y/README.md"] = "---\nauthority_level: 2\n---\n"
        self.assertEqual(len(self.run_check(files)), 2)


class RunbundleCompletenessTests(unittest.TestCase):
    """VS019: a runbundle folder carries the files the guides list."""

    def test_runbundle_missing_manifest_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp, "00_Admin/runbooks/rnb_x")
            bundle.mkdir(parents=True)
            (bundle / "README.md").write_text("x", encoding="utf-8")
            errors: list[str] = []
            warnings: list[str] = []
            mod.check_program_completeness(
                "",
                [],
                [],
                [],
                errors,
                warnings,
                "error",
                tmp,
                runbundle_globs=["00_Admin/runbooks/rnb_*"],
                required_runbundle_files=["README.md", "manifest.yaml"],
            )
            self.assertEqual(len(errors), 1)
            self.assertIn("manifest.yaml", errors[0])

    def test_a_loose_runbook_file_is_not_a_runbundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "00_Admin/runbooks").mkdir(parents=True)
            Path(tmp, "00_Admin/runbooks/rnb_loose.md").write_text("x", encoding="utf-8")
            errors: list[str] = []
            warnings: list[str] = []
            mod.check_program_completeness(
                "", [], [], [], errors, warnings, "error", tmp,
                runbundle_globs=["00_Admin/runbooks/rnb_*"],
                required_runbundle_files=["README.md", "manifest.yaml"],
            )
            self.assertEqual(errors, [])


class BundleFileBudgetTests(unittest.TestCase):
    """VS041: a bundle folder holds at most file_budget files."""

    BUNDLE = "90_Sandbox/ai_workbooks/wb_a"

    def run_check(self, files: dict[str, str], budget: int = 3) -> tuple[list[str], list[str]]:
        with tempfile.TemporaryDirectory() as tmp:
            for name, text in files.items():
                path = Path(tmp, name)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
            errors: list[str] = []
            warnings: list[str] = []
            mod.check_bundle_file_budget(
                tmp, list(mod._DEFAULT_BUNDLE_GLOBS), budget, [], errors, warnings, "warning", "VS041"
            )
            return errors, warnings

    def many(self, count: int) -> dict[str, str]:
        return {f"{self.BUNDLE}/n{i}.md": "x" for i in range(count)}

    def test_over_budget_bundle_warns_without_failing(self) -> None:
        errors, warnings = self.run_check(self.many(4))
        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 1)
        self.assertIn("VS041", warnings[0])

    def test_within_budget_passes(self) -> None:
        self.assertEqual(self.run_check(self.many(3)), ([], []))

    def test_readme_file_budget_raises_the_limit(self) -> None:
        files = self.many(4)
        files[f"{self.BUNDLE}/README.md"] = "---\nfile_budget: 6  # reason: four workbooks\n---\n"
        self.assertEqual(self.run_check(files), ([], []))

    def test_nested_files_count(self) -> None:
        files = {f"{self.BUNDLE}/sub/n{i}.md": "x" for i in range(4)}
        self.assertEqual(len(self.run_check(files)[1]), 1)


class WorkbookPresenceWiringTests(unittest.TestCase):
    """The rule is enabled in the live config and reaches the engine's main()."""

    def test_rule_is_enabled_in_the_live_config(self) -> None:
        config = SCRIPT.parents[1] / "configs" / "validator" / "validator_config.yaml"
        rules = mod.parse_config(str(config))["rules"]
        self.assertTrue(any(rule.get("id") == "VS040" and rule.get("enabled") for rule in rules))
        self.assertTrue(any(rule.get("id") == "VS041" and rule.get("enabled") for rule in rules))

    def test_engine_run_from_another_directory_flags_a_bundle_without_a_workbook(self) -> None:
        config_text = (
            "version: 0.1.1\nvalidator_id: validator_v1\nrules:\n  - id: VS040\n    enabled: true\n"
            "    paths:\n      - 90_Sandbox/ai_workbooks/**/README.md\n    params:\n      severity: error\n"
        )
        config_rel = "00_Admin/configs/validator/validator_config.yaml"
        for with_workbook, expected in ((True, 0), (False, 1)):
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root / "00_Admin/configs/validator").mkdir(parents=True)
                (root / config_rel).write_text(config_text, encoding="utf-8")
                bundle = root / "90_Sandbox/ai_workbooks/wb_b"
                bundle.mkdir(parents=True)
                (bundle / "README.md").write_text("---\nauthority_level: 3\n---\n", encoding="utf-8")
                if with_workbook:
                    (bundle / "wb_x.md").write_text("x\n", encoding="utf-8")
                run = subprocess.run(
                    [
                        sys.executable, str(SCRIPT), "--repo-root", ".", "--structure-root", str(root),
                        "--config", config_rel,
                    ],
                    cwd=root,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(run.returncode, expected, run.stdout + run.stderr)


class EngineSharingTests(unittest.TestCase):
    """The engine runs from ai_ops against a governed repo's own root and config."""

    def test_config_version_used_by_governed_repos_is_accepted(self) -> None:
        self.assertIn("0.1.1", mod.SUPPORTED_CONFIG_VERSIONS)
        self.assertNotIn("0.2.0", mod.SUPPORTED_CONFIG_VERSIONS)

    def test_envelope_rejects_a_bare_wildcard_baseline_and_a_bad_level(self) -> None:
        def problems(rule: dict) -> list[str]:
            config = {"validator_id": "validator_v1", "version": "0.1.1", "rules": [rule]}
            return mod.validate_config_envelope(config, "config.yaml", "C:/repo")

        def with_params(rule_id: str, **params: object) -> dict:
            return {"id": rule_id, "enabled": True, "params": params}

        self.assertTrue(problems(with_params("VS003", baseline_exclude=["*"])))
        self.assertTrue(problems(with_params("VS003", baseline_exclude=["../x"])))
        self.assertFalse(problems(with_params("VS003", baseline_exclude=["docs/a.md"])))
        self.assertTrue(problems(with_params("VS040", min_authority_level="high")))
        self.assertTrue(problems(with_params("VS041", default_file_budget="many")))

    def test_relative_repo_root_resolves_against_the_caller_directory(self) -> None:
        import os

        with tempfile.TemporaryDirectory() as tmp:
            previous = os.getcwd()
            os.chdir(tmp)
            try:
                resolved = mod.resolve_repo_root(".", "C:/somewhere/else")
            finally:
                os.chdir(previous)
            self.assertEqual(os.path.normcase(resolved), os.path.normcase(os.path.realpath(tmp)))

    def test_baseline_exclude_in_the_config_skips_listed_files(self) -> None:
        config_rel = "00_Admin/configs/validator/validator_config.yaml"
        base = (
            "version: 0.1.1\nvalidator_id: validator_v1\nrules:\n  - id: VS003\n    enabled: true\n"
            "    paths:\n      - docs/*.md\n"
        )
        for baseline, expected in (("    params:\n      baseline_exclude:\n        - docs/legacy.md\n", 0), ("", 1)):
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root / "00_Admin/configs/validator").mkdir(parents=True)
                (root / config_rel).write_text(base + baseline, encoding="utf-8")
                (root / "docs").mkdir()
                (root / "docs/legacy.md").write_text("---\ntitle: x\n---\n# x\n", encoding="utf-8")
                (root / "docs/ok.md").write_text("---\nstatus: active\n---\n# ok\n", encoding="utf-8")
                run = subprocess.run(
                    [
                        sys.executable, str(SCRIPT), "--repo-root", ".", "--structure-root", str(root),
                        "--config", config_rel,
                    ],
                    cwd=root,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(run.returncode, expected, run.stdout + run.stderr)


if __name__ == "__main__":
    unittest.main()
