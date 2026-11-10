from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "00_Admin" / "scripts" / "check_workflow_exports_drift.py"
SPEC = importlib.util.spec_from_file_location("check_workflow_exports_drift", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class WorkflowExportDriftTests(unittest.TestCase):
    def test_missing_ignored_local_skill_is_allowed_only_with_explicit_metadata(self) -> None:
        output = {
            "path": ".agents/skills/not-installed/SKILL.md",
            "kind": "codex_skill_primary",
            "publication": "ignored_local",
        }
        self.assertTrue(MODULE._is_ignored_local_output(REPO_ROOT, output))

        output["publication"] = "tracked"
        self.assertFalse(MODULE._is_ignored_local_output(REPO_ROOT, output))

    def test_tracked_plugin_output_is_never_treated_as_local(self) -> None:
        output = {
            "path": "plugins/ai-ops-governance/skills/work/SKILL.md",
            "kind": "plugin_skill",
            "publication": "ignored_local",
        }
        self.assertFalse(MODULE._is_ignored_local_output(REPO_ROOT, output))

    def test_repo_manifest_must_keep_the_canonical_surface(self) -> None:
        findings = MODULE._target_drift("repo", {"plugin"})
        self.assertIn("manifest missing canonical target: claude", findings)
        self.assertIn("manifest missing canonical target: codex", findings)
        self.assertEqual([], MODULE._target_drift("repo", {"plugin", "claude", "codex"}))
        scope_findings = MODULE._target_drift("workspace", {"plugin", "claude", "codex"})
        self.assertTrue(any("manifest scope must equal repo" in finding for finding in scope_findings))


if __name__ == "__main__":
    unittest.main()
