"""Contract parity tests for workbook ai_role validation."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_CONFIG = ROOT / "00_Admin" / "configs" / "validator" / "validator_config.yaml"
VALIDATOR_SCRIPT = ROOT / "00_Admin" / "scripts" / "validate_repo_rules.py"


def _load_validator():
    spec = importlib.util.spec_from_file_location("ai_ops_validate_repo_rules", VALIDATOR_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class AiRoleValidatorContractTests(unittest.TestCase):
    def test_vs006_requires_ai_role_and_description(self) -> None:
        config = yaml.safe_load(VALIDATOR_CONFIG.read_text(encoding="utf-8"))
        rules = [rule for rule in config["rules"] if rule.get("id") == "VS006"]
        self.assertEqual(len(rules), 1)
        required = set(rules[0]["params"]["required_fields"])
        self.assertTrue({"title", "id", "status", "version", "created", "ai_role", "description"} <= required)

    def test_vs006_covers_nested_workbooks_in_both_repositories(self) -> None:
        config = yaml.safe_load(VALIDATOR_CONFIG.read_text(encoding="utf-8"))
        rules = [rule for rule in config["rules"] if rule.get("id") == "VS006"]
        self.assertEqual(len(rules), 1)
        self.assertIn("90_Sandbox/ai_workbooks/**/wb_*.md", rules[0]["paths"])

    def test_vs006_rejects_missing_ai_role(self) -> None:
        validator = _load_validator()
        text = (
            "---\ntitle: Test\nid: wb_test\nstatus: planned\nversion: 0.1.0\n"
            "created: 2026-11-09\ndescription: Test\n---\n# Test\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "wb_test.md"
            path.write_text(text, encoding="utf-8")
            errors: list[str] = []
            validator.check_required_fields(
                [str(path)],
                ["title", "id", "status", "version", "created", "ai_role", "description"],
                errors,
                "VS006",
            )
        self.assertTrue(any("ai_role" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
