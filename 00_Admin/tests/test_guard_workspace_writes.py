"""Fail-closed tests for the vendor-neutral workspace write adapter."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "00_Admin/scripts/hooks/guard_workspace_writes.py"


POLICY = """version: 0.1.0
workspace:
  temp_root: "<workspace-root>/tmp"
harness_exceptions:
  - id: temp
    path: "<os-temp>/ai_ops"
escape_root_signatures:
  - "<os-temp>/ai_ops"
"""


class GuardWorkspaceWritesTests(unittest.TestCase):
    def run_hook(self, root: Path, payload: object, config: Path | None = None, digest: str | None = None) -> dict:
        command = [sys.executable, str(SCRIPT), "--workspace-root", str(root)]
        if config:
            command += ["--config", str(config)]
        if digest:
            command += ["--config-sha256", digest]
        completed = subprocess.run(command, input=json.dumps(payload), text=True, capture_output=True, check=True)
        return json.loads(completed.stdout) if completed.stdout.strip() else {}

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "workspace"
        self.root.mkdir()
        self.config = self.root / "workspace_containment.yaml"
        self.config.write_text(POLICY, encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_in_workspace_write_is_allowed(self) -> None:
        self.assertEqual({}, self.run_hook(self.root, {"tool_input": {"file_path": "ok.txt"}}, self.config))

    def test_outside_absolute_write_is_denied(self) -> None:
        result = self.run_hook(
            self.root,
            {"tool_input": {"file_path": str(Path(self.temp.name).parent / "outside.txt")}},
            self.config,
        )
        self.assertIn("deny", json.dumps(result))
        self.assertIn("cause=", json.dumps(result))

    def test_traversal_and_self_protect_are_denied(self) -> None:
        traversal = self.run_hook(self.root, {"tool_input": {"file_path": "..\\outside.txt"}}, self.config)
        protected = self.run_hook(self.root, {"tool_input": {"file_path": ".git/hooks/pre-commit"}}, self.config)
        self.assertIn("deny", json.dumps(traversal))
        self.assertIn("deny", json.dumps(protected))

    def test_malformed_input_and_missing_target_fail_closed(self) -> None:
        command = [sys.executable, str(SCRIPT), "--workspace-root", str(self.root), "--config", str(self.config)]
        completed = subprocess.run(command, input="not-json", text=True, capture_output=True, check=True)
        self.assertIn("deny", completed.stdout)
        result = self.run_hook(self.root, {"tool_input": {}}, self.config)
        self.assertIn("deny", json.dumps(result))

    def test_digest_mismatch_is_denied(self) -> None:
        result = self.run_hook(self.root, {"tool_input": {"file_path": "ok.txt"}}, self.config, "0" * 64)
        self.assertIn("deny", json.dumps(result))

    def test_policy_files_are_self_protected_by_exact_path(self) -> None:
        result = self.run_hook(
            self.root,
            {"tool_input": {"file_path": str(self.root / "workspace_containment.yaml")}},
            self.config,
        )
        self.assertIn("deny", json.dumps(result))

    def test_workspace_agent_settings_boundary_is_self_protected(self) -> None:
        result = self.run_hook(
            self.root,
            {"tool_input": {"file_path": str(self.root / "ai_ops" / ".claude" / "settings.local.json")}},
            self.config,
        )
        self.assertIn("deny", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
