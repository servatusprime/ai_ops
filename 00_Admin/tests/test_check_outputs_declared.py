"""Tests for check_outputs_declared.py: a workbook's Outputs table against `git status`."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_outputs_declared.py"
spec = importlib.util.spec_from_file_location("check_outputs_declared", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

WORKBOOK = """# W

## Scope

- `not_a_path_in_scope.md` is prose, not an output.

## Outputs and Target Files

| Path | Change | Proven by |
| --- | --- | --- |
| `a.txt`, `docs/` | edit | `python -m unittest` |
| `*.cfg` | edit | n/a |

## Validation Commands
"""


def make_repo(root: Path, files: dict[str, str]) -> Path:
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    (root / "wb_test.md").write_text(WORKBOOK, encoding="utf-8")
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root / "wb_test.md"


def run_check(workbook: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--workbook", str(workbook), *extra],
        capture_output=True,
        text=True,
    )


class OutputsDeclaredTests(unittest.TestCase):
    def test_declared_paths_come_only_from_the_outputs_table_first_column(self) -> None:
        self.assertEqual(mod.declared_paths(WORKBOOK), ["a.txt", "docs/", "*.cfg"])
        self.assertIsNone(mod.declared_paths("# no outputs section\n"))

    def test_covers_files_folders_and_globs(self) -> None:
        self.assertTrue(mod.covers("a.txt", "a.txt"))
        self.assertTrue(mod.covers("docs/", "docs/x/y.md"))
        self.assertTrue(mod.covers("docs", "docs/x.md"))
        self.assertTrue(mod.covers("*.cfg", "app.cfg"))
        self.assertFalse(mod.covers("a.txt", "b.txt"))
        self.assertTrue(mod.covers("./.hidden.yaml", ".hidden.yaml"))
        self.assertFalse(mod.covers("00_Admin/*.py", "00_Admin/x/y.py"))  # `*` does not cross a folder
        self.assertTrue(mod.covers("00_Admin/**/*.py", "00_Admin/x/y.py"))
        self.assertTrue(mod.covers("my notes/a b.md", "my notes/a b.md"))

    def test_a_bare_wildcard_declares_nothing(self) -> None:
        text = "## Outputs and Target Files\n\n| Path |\n| --- |\n| `*` |\n| `**/` |\n| `a b.txt` |\n"
        self.assertEqual(mod.declared_paths(text), ["a b.txt"])

    def test_porcelain_parsing_handles_renames_spaces_and_deletions(self) -> None:
        raw = b"R  new.txt\0old.txt\0 M a b.txt\0?? c.txt\0 D gone.txt\0 R moved2.txt\0old2.txt\0"
        self.assertEqual(
            mod.parse_porcelain(raw), ["new.txt", "a b.txt", "c.txt", "gone.txt", "moved2.txt"]
        )

    def test_an_undeclared_change_is_flagged_and_declared_ones_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workbook = make_repo(Path(tmp), {"a.txt": "x", "docs/n.md": "x", "app.cfg": "x", "b.txt": "x"})
            run = run_check(workbook)
            self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
            self.assertIn("undeclared: b.txt", run.stdout)
            self.assertNotIn("undeclared: a.txt", run.stdout)
            self.assertNotIn("undeclared: docs/n.md", run.stdout)

    def test_all_changes_declared_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workbook = make_repo(Path(tmp), {"a.txt": "x", "docs/n.md": "x"})
            run = run_check(workbook)  # the workbook file itself is declared automatically
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def test_the_bundle_folder_holding_the_workbook_is_declared(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            bundle = root / "90_Sandbox" / "wb_bundle"
            bundle.mkdir(parents=True)
            workbook = bundle / "wb_one.md"
            workbook.write_text(WORKBOOK, encoding="utf-8")
            (bundle / "README.md").write_text("x", encoding="utf-8")
            (bundle / "review_note.md").write_text("x", encoding="utf-8")
            (root / "stray.txt").write_text("x", encoding="utf-8")
            run = run_check(workbook)
            self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
            self.assertIn("undeclared: stray.txt", run.stdout)
            self.assertNotIn("review_note.md", run.stdout.split("information only")[0])

    def test_a_workbook_without_an_outputs_table_exits_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["git", "init", "-q", tmp], check=True)
            bare = Path(tmp) / "wb_bare.md"
            bare.write_text("# W\n", encoding="utf-8")
            self.assertEqual(run_check(bare).returncode, 2)


if __name__ == "__main__":
    unittest.main()
