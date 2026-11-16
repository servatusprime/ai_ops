"""Tests for workbook_progress.py: tasks ticked per phase, computed from the queue checkboxes."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "workbook_progress.py"
spec = importlib.util.spec_from_file_location("workbook_progress", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

WORKBOOK = """---
id: wb_demo_01
---
# Demo

## Status Checklist

- [x] **Ph 0:** this box is not a queue task and must not be counted

## Ordered Execution Queue

### Phase 0: Start (Agent -- Level 0)

- [x] 0.1 read
- [x] 0.2 check

### Phase 1: Build (Agent -- Level 3; approved)

- [x] 1.1 write
  - [ ] nested detail is not a task
- [ ] 1.2 test
- [ ] 1.3 review

### Completion

- [ ] C.1 selfcheck

## Verification Checklist

- [x] outside the queue
"""


class ProgressTests(unittest.TestCase):
    def test_phases_count_top_level_task_boxes_only(self) -> None:
        self.assertEqual(
            mod.phases(WORKBOOK),
            [("Phase 0: Start", 2, 2), ("Phase 1: Build", 1, 3), ("Completion", 0, 1)],
        )

    def test_other_box_marks_count_in_the_total_and_only_x_is_ticked(self) -> None:
        text = "## Ordered Execution Queue\n\n### P\n\n- [x] a\n- [~] b\n- [-] c\n* [ ] d\n* [X] e\n- [!] f\n"
        self.assertEqual(mod.phases(text), [("P", 2, 6)])

    def test_heading_is_anchored_and_fenced_blocks_are_ignored(self) -> None:
        text = (
            "Prose naming `## Ordered Execution Queue` inline.\n\n"
            "### Not the queue\n\n- [x] outside\n\n"
            "## Ordered Execution Queue\n\n### P\n\n- [x] a\n```\n## Verification\n- [x] fenced\n```\n- [ ] b\n\n"
            "## After\n\n- [x] outside again\n"
        )
        self.assertEqual(mod.phases(text), [("P", 1, 2)])
        self.assertIsNone(mod.phases("Mention of ## Ordered Execution Queue only\n- [x] a\n"))

    def test_percent_rounds_down_so_100_means_all_ticked(self) -> None:
        self.assertEqual(mod.percent(199, 200), 99)
        self.assertEqual(mod.percent(200, 200), 100)
        self.assertEqual(mod.percent(0, 0), 0)
        self.assertEqual(mod.percent(2, 3), 66)

    def test_a_workbook_without_a_queue_returns_none(self) -> None:
        self.assertIsNone(mod.phases("# no queue\n"))

    def test_render_shows_percent_bar_and_total(self) -> None:
        out = mod.render("wb_demo_01", mod.phases(WORKBOOK))
        self.assertIn("100%  ##########", out)
        self.assertIn("33%  ###.......", out)
        self.assertIn("All phases", out)
        self.assertIn("3/6", out)
        self.assertIn("50%", out)

    def test_a_bundle_prints_one_block_per_workbook_and_no_combined_figure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first, second = Path(tmp, "wb_one.md"), Path(tmp, "wb_two.md")
            first.write_text(WORKBOOK, encoding="utf-8")
            second.write_text(WORKBOOK.replace("wb_demo_01", "wb_demo_02"), encoding="utf-8")
            run = subprocess.run([sys.executable, str(SCRIPT), str(first), str(second)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(run.stdout.count("All phases"), 2)
            self.assertIn("wb_demo_01", run.stdout)
            self.assertIn("wb_demo_02", run.stdout)

    def test_missing_queue_or_file_exits_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bare = Path(tmp, "wb_bare.md")
            bare.write_text("# nothing\n", encoding="utf-8")
            run_bare = subprocess.run([sys.executable, str(SCRIPT), str(bare)], capture_output=True)
            self.assertEqual(run_bare.returncode, 2)
            missing = Path(tmp, "missing.md")
            run_missing = subprocess.run([sys.executable, str(SCRIPT), str(missing)], capture_output=True)
            self.assertEqual(run_missing.returncode, 2)


if __name__ == "__main__":
    unittest.main()
