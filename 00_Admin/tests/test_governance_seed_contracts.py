"""Regression tests for actualized governance-seed contracts."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

ROOT = Path(__file__).parents[2]
SCRIPT_PATH = ROOT / "00_Admin" / "scripts" / "validate_repo_rules.py"
CONFIG_PATH = ROOT / "00_Admin" / "configs" / "validator" / "validator_config.yaml"
SPEC = importlib.util.spec_from_file_location("validate_repo_rules", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class GovernanceSeedContractTests(unittest.TestCase):
    def test_validator_missing_config_output_omits_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            repo_root.mkdir()
            missing_config = repo_root / "missing-validator.yaml"
            output = io.StringIO()
            with patch.object(
                VALIDATOR.sys,
                "argv",
                [
                    "validate_repo_rules.py",
                    "--repo-root",
                    str(repo_root),
                    "--config",
                    str(missing_config),
                ],
            ):
                with contextlib.redirect_stdout(output):
                    result = VALIDATOR.main()

            self.assertEqual(1, result)
            rendered = output.getvalue()
            self.assertIn("Config trust failure", rendered)
            self.assertNotIn(str(missing_config), rendered)

    def test_validator_diagnostics_keep_rule_and_relative_path_without_machine_root(self) -> None:
        output = VALIDATOR._sanitize_issue(
            f"VS001: {ROOT / '00_Admin' / 'README.md'} missing front matter",
            str(ROOT),
        )
        self.assertEqual("VS001: <repo-root>/00_Admin/README.md missing front matter", output)
        self.assertNotIn(str(ROOT), output)

    def test_validator_log_code_does_not_emit_untrusted_issue_detail(self) -> None:
        issue = "VS001: password=secret-value in /outside/private.txt"

        self.assertEqual("VS001", VALIDATOR._safe_issue_code(issue))
        rendered = VALIDATOR._safe_issue_summary(issue, "validation failure")
        self.assertIn("VS001 validation failure [ref:", rendered)
        self.assertNotIn("secret-value", rendered)
        self.assertEqual("VALIDATOR", VALIDATOR._safe_issue_code("unclassified secret-value"))

    def test_validator_cli_does_not_emit_untrusted_config_error_detail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            repo_root.mkdir()
            config_path = repo_root / "validator.yaml"
            config_path.write_text("validator_id: validator_v1\n", encoding="utf-8")
            output = io.StringIO()
            with patch.object(
                VALIDATOR.sys,
                "argv",
                [
                    "validate_repo_rules.py",
                    "--repo-root",
                    str(repo_root),
                    "--config",
                    str(config_path),
                ],
            ), patch.object(
                VALIDATOR,
                "parse_config",
                return_value={"rules": [{"id": "VS001", "enabled": True, "paths": []}]},
            ), patch.object(
                VALIDATOR,
                "validate_config_envelope",
                return_value=["VS-CONFIG: password=secret-value in /outside/private.txt"],
            ), contextlib.redirect_stdout(output):
                result = VALIDATOR.main()

            self.assertEqual(1, result)
            rendered = output.getvalue()
            self.assertIn("VS-CONFIG validation failure [ref:", rendered)
            self.assertNotIn("secret-value", rendered)
            self.assertNotIn("outside/private.txt", rendered)

    def test_real_path_preserves_display_casing(self) -> None:
        rendered = VALIDATOR._real_path(str(ROOT / "00_Admin"))
        self.assertIn("00_Admin", rendered)

    def test_vs034_contracts_are_present(self) -> None:
        config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
        rule = next(item for item in config["rules"] if item["id"] == "VS034")
        errors: list[str] = []
        warnings: list[str] = []
        VALIDATOR.check_required_contract_content(
            rule["params"]["contract_markers"],
            errors,
            warnings,
            rule["params"]["severity"],
            rule["id"],
            str(ROOT),
        )
        self.assertEqual([], errors)
        self.assertEqual([], warnings)

    def test_templates_are_cataloged(self) -> None:
        catalog = (ROOT / "01_Resources" / "templates" / "README.md").read_text(
            encoding="utf-8"
        )
        for name in (
            "artifact_cleanup_manifest_template.md",
            "canonical_promotion_manifest_template.md",
            "quality_loop_convergence_template.md",
        ):
            self.assertIn(name, catalog)

    def test_vs034_promote_forward_contract_fails_closed(self) -> None:
        """Negative fixture: VS034 fails when promote_forward_contract: is missing."""
        import os

        with tempfile.TemporaryDirectory() as temp_dir:
            os.makedirs(os.path.join(temp_dir, ".ai_ops", "workflows"), exist_ok=True)
            os.makedirs(
                os.path.join(temp_dir, "01_Resources", "templates", "workflows"),
                exist_ok=True,
            )
            Path(
                os.path.join(temp_dir, ".ai_ops", "workflows", "closeout.md")
            ).write_text("# closeout\nNo promote-forward contract here.\n", encoding="utf-8")
            Path(
                os.path.join(
                    temp_dir,
                    "01_Resources",
                    "templates",
                    "workflows",
                    "canonical_promotion_manifest_template.md",
                )
            ).write_text("# Template\nNo promote_forward_contract block.\n", encoding="utf-8")

            errors: list[str] = []
            warnings: list[str] = []
            VALIDATOR.check_required_contract_content(
                [
                    ".ai_ops/workflows/closeout.md::promote_forward_contract:",
                    "01_Resources/templates/workflows/canonical_promotion_manifest_template.md::promote_forward_contract:",
                ],
                errors,
                warnings,
                "error",
                "VS034",
                temp_dir,
            )
            self.assertEqual(2, len(errors))
            self.assertIn("promote_forward_contract:", errors[0])
            self.assertIn("promote_forward_contract:", errors[1])

    def test_vs034_rejects_empty_or_invalid_contracts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            errors: list[str] = []
            warnings: list[str] = []
            VALIDATOR.check_required_contract_content(
                [], errors, warnings, "error", "VS034", temp_dir
            )
            self.assertEqual(["VS034: no contract markers configured"], errors)

            errors.clear()
            VALIDATOR.check_required_contract_content(
                ["invalid-contract"], errors, warnings, "error", "VS034", temp_dir
            )
            self.assertIn("expected path::marker", errors[0])

    def test_warning_rules_honor_configured_error_severity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "active.md"
            path.write_text(
                "---\nstatus: active\n---\n# Active artifact\n",
                encoding="utf-8",
            )
            errors: list[str] = []
            warnings: list[str] = []
            VALIDATOR.check_active_status_has_purpose(
                [str(path)], errors, warnings, "error", "VS032"
            )
            self.assertEqual([], warnings)
            self.assertEqual(
                [
                    f"VS032: {path} has status:active but is missing a '## Purpose' heading"
                ],
                errors,
            )

    def test_validator_config_rejects_unknown_rules_and_non_boolean_enabled(self) -> None:
        config = {
            "validator_id": "validator_v1",
            "version": "0.1.0",
            "rules": [
                {"id": "VS999", "enabled": True, "paths": []},
                {"id": "VS001", "enabled": "maybe", "paths": []},
            ],
        }
        errors = VALIDATOR.validate_config_envelope(config, "fixture.yaml", str(ROOT))
        self.assertIn("VS-CONFIG: VS999 is not an implemented validator rule", errors)
        self.assertIn("VS-CONFIG: VS001 enabled must be boolean", errors)

    def test_parser_preserves_invalid_enabled_value_for_fail_closed_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "validator.yaml"
            config_path.write_text(
                "version: 0.1.0\n"
                "validator_id: validator_v1\n"
                "rules:\n"
                "  - id: VS001\n"
                "    enabled: maybe\n"
                "    paths: []\n",
                encoding="utf-8",
            )
            parsed = VALIDATOR.parse_config(str(config_path))
            self.assertEqual("maybe", parsed["rules"][0]["enabled"])

    def test_vs036_rejects_configured_input_path_escape(self) -> None:
        for configured_path in ("../outside.yaml", r"..\outside.yaml"):
            with self.subTest(configured_path=configured_path):
                errors: list[str] = []
                VALIDATOR.check_run_family_graph_contract(
                    {"registry": configured_path}, str(ROOT), errors
                )
                self.assertTrue(any("configured input path" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
