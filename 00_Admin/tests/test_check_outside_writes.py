"""Policy-parsing and stable-root tests for the outside-write report."""

from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "00_Admin/scripts"))
SPEC = importlib.util.spec_from_file_location("check_outside_writes", ROOT / "00_Admin/scripts/check_outside_writes.py")
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class OutsideWritePolicyTests(unittest.TestCase):
    def test_os_temp_signature_keeps_stable_host_roots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "policy.yaml"
            config.write_text("escape_root_signatures:\n  - '<os-temp>/ai_ops'\n", encoding="utf-8")
            roots = MODULE.load_report_signatures(config, ROOT)
        expected = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "AppData/Local/Temp/ai_ops"
        self.assertIn(expected.resolve(), roots)

    def test_malformed_policy_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "policy.yaml"
            config.write_text("escape_root_signatures: {bad: value}\n", encoding="utf-8")
            with self.assertRaises(SystemExit):
                MODULE.load_report_signatures(config, ROOT)


if __name__ == "__main__":
    unittest.main()
