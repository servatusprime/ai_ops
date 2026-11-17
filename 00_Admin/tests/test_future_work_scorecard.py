"""Contract tests for visible future-work timing state."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "generate_future_work_scorecard", ROOT / "00_Admin/scripts/generate_future_work_scorecard.py"
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class FutureWorkScorecardTests(unittest.TestCase):
    def test_overdue_next_review_is_visible_without_becoming_a_gate(self) -> None:
        rows = MODULE._build_rows([{"id": "fw_20260101_01", "next_review": "2020-01-01"}])
        with tempfile.TemporaryDirectory() as temp_dir:
            rendered = MODULE._render_markdown(Path(temp_dir) / "registry.yaml", rows, Path(temp_dir))
        self.assertIn("OVERDUE (2020-01-01)", rendered)


if __name__ == "__main__":
    unittest.main()
