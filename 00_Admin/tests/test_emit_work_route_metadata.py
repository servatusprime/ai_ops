"""Contract tests for the side-effect-free /work route metadata emitter."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "00_Admin/scripts/emit_work_route_metadata.py"
SPEC = importlib.util.spec_from_file_location("emit_work_route_metadata", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class WorkRouteMetadataEmitterTests(unittest.TestCase):
    def test_emits_required_work_fields(self) -> None:
        result = MODULE.build_metadata(
            bootstrap_path="fresh_bootstrap",
            resume_basis="unknown state; direct ai_ops target",
            reads_applied=["ai_ops/AGENTS.md", "ai_ops/.ai_ops/workflows/work.md"],
            context_reset_applied="true",
            scope_echo="ai_ops /work remediation in the active workbundle",
        )
        self.assertEqual(
            {
                "bootstrap_path",
                "resume_basis",
                "reads_applied",
                "context_reset_applied",
                "scope_echo",
            },
            set(result["work_route_metadata"]),
        )
        self.assertTrue(result["work_route_metadata"]["context_reset_applied"])

    def test_output_is_json_serializable(self) -> None:
        result = MODULE.build_metadata(
            bootstrap_path="recenter",
            resume_basis="scope changed",
            reads_applied=["ai_ops/AGENTS.md"],
            context_reset_applied="false",
            scope_echo="recenter before a policy edit",
        )
        encoded = json.dumps(result)
        self.assertEqual(result, json.loads(encoded))

    def test_invalid_metadata_is_rejected(self) -> None:
        cases = (
            {"bootstrap_path": "unknown"},
            {"bootstrap_path": "resume_same_scope"},
            {"resume_basis": ""},
            {"reads_applied": []},
            {"context_reset_applied": "maybe"},
            {"scope_echo": "line\nbreak"},
        )
        base = {
            "bootstrap_path": "fresh_bootstrap",
            "resume_basis": "unknown",
            "reads_applied": ["ai_ops/AGENTS.md"],
            "context_reset_applied": "true",
            "scope_echo": "scope",
        }
        for override in cases:
            with self.subTest(override=override):
                values = {**base, **override}
                with self.assertRaises(ValueError):
                    MODULE.build_metadata(**values)

    def test_cli_emits_json(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--bootstrap-path",
                "fresh_bootstrap",
                "--resume-basis",
                "unknown state",
                "--reads-applied",
                "ai_ops/AGENTS.md",
                "--context-reset-applied",
                "true",
                "--scope-echo",
                "ai_ops /work",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual("fresh_bootstrap", payload["work_route_metadata"]["bootstrap_path"])


if __name__ == "__main__":
    unittest.main()
