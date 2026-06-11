"""Regression tests for actualized governance-seed contracts."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[2]
SCRIPT_PATH = ROOT / "00_Admin" / "scripts" / "validate_repo_rules.py"
CONFIG_PATH = ROOT / "00_Admin" / "configs" / "validator" / "validator_config.yaml"
SPEC = importlib.util.spec_from_file_location("validate_repo_rules", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class GovernanceSeedContractTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
