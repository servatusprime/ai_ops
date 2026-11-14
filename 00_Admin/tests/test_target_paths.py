"""Contract tests for safe workspace-root derivation."""

from __future__ import annotations

import importlib.util
import os
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "target_paths", ROOT / "00_Admin/scripts/target_paths.py"
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class TargetPathsTests(unittest.TestCase):
    def test_shallow_script_path_fails_closed_with_context(self) -> None:
        with self.assertRaisesRegex(ValueError, "cannot derive workspace root"):
            shallow = Path("/") / "script.py"
            if os.name == "nt":
                shallow = Path("C:/script.py")
            MODULE.default_workspace_root(shallow)


if __name__ == "__main__":
    unittest.main()
