"""Contract tests for safe workspace-root derivation."""

from __future__ import annotations

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "target_paths", ROOT / "00_Admin/scripts/target_paths.py"
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class TargetPathsTests(unittest.TestCase):
    def test_absolute_repo_root_does_not_require_workspace_inference(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            (repo / ".git").mkdir()
            with mock.patch.object(MODULE, "default_workspace_root", side_effect=AssertionError):
                self.assertEqual(repo.resolve(), MODULE.resolve_repo_root(repo))

    def test_absolute_input_paths_do_not_require_workspace_inference(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            existing = root / "input.yaml"
            existing.write_text("value: true\n", encoding="utf-8")
            missing = root / "future.yaml"
            with mock.patch.object(MODULE, "default_workspace_root", side_effect=AssertionError):
                self.assertEqual(existing.resolve(), MODULE.resolve_input_path(existing))
                self.assertEqual(missing.resolve(), MODULE.resolve_input_path(missing, must_exist=False))

    def test_shallow_script_path_fails_closed_with_context(self) -> None:
        with self.assertRaisesRegex(ValueError, "cannot derive workspace root"):
            shallow = Path("/") / "script.py"
            if os.name == "nt":
                shallow = Path("C:/script.py")
            MODULE.default_workspace_root(shallow)


if __name__ == "__main__":
    unittest.main()
