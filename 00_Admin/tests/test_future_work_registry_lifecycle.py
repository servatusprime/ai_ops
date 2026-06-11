"""Regression tests for future-work provenance and completion lifecycle."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "validate_repo_rules.py"
SPEC = importlib.util.spec_from_file_location("validate_repo_rules", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class FutureWorkRegistryLifecycleTests(unittest.TestCase):
    def _run_check(self, registry_entry: str, log_text: str) -> list[str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            backlog = root / "backlog"
            logs = root / "logs"
            backlog.mkdir()
            logs.mkdir()
            registry = backlog / "future_work_registry.yaml"
            registry.write_text(
                "entries:\n" + registry_entry,
                encoding="utf-8",
                newline="\n",
            )
            (logs / "log_workbook_run.md").write_text(
                log_text,
                encoding="utf-8",
                newline="\n",
            )
            warnings: list[str] = []
            VALIDATOR.check_future_work_registry(str(registry), warnings)
            return warnings

    def test_source_workbook_in_log_is_provenance_only(self) -> None:
        warnings = self._run_check(
            "  - id: fw_test_01\n"
            "    source_workbook: source.md\n"
            "    completion_workbook: null\n"
            "    scope: Test scope\n"
            "    priority: low\n"
            "    created: 2026-06-11\n",
            "Completed source.md\n",
        )
        self.assertEqual([], warnings)

    def test_completion_workbook_in_log_is_stale(self) -> None:
        warnings = self._run_check(
            "  - id: fw_test_02\n"
            "    source_workbook: source.md\n"
            "    completion_workbook: implementation.md\n"
            "    scope: Test scope\n"
            "    priority: low\n"
            "    created: 2026-06-11\n",
            "Completed implementation.md\n",
        )
        self.assertEqual(
            [
                "VS012: completion_workbook completed in run log: "
                "implementation.md"
            ],
            warnings,
        )

    def test_completion_workbook_field_is_required(self) -> None:
        warnings = self._run_check(
            "  - id: fw_test_03\n"
            "    source_workbook: source.md\n"
            "    scope: Test scope\n"
            "    priority: low\n"
            "    created: 2026-06-11\n",
            "",
        )
        self.assertEqual(
            ["VS012: entry missing 'completion_workbook'"],
            warnings,
        )


if __name__ == "__main__":
    unittest.main()
