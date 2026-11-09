"""Focused tests for update_artifact_status.py: status vocabulary, note cap, --remove, --check, error handling."""

from __future__ import annotations

import contextlib
import copy
import hashlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path

import yaml

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "update_artifact_status.py"
spec = importlib.util.spec_from_file_location("update_artifact_status", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

STATE = {
    "schema_version": 1,
    "work_context": {
        "active_artifacts": [
            {"id": "wb_a", "type": "workbook", "repo": "ai_ops", "status": "active", "note": "a"},
            {"id": "wb_b", "type": "workbook", "repo": "ai_ops", "status": "completed", "note": "b"},
            {"id": "wb_dup", "type": "workbundle", "repo": "ai_ops", "status": "active", "note": "readme"},
            {"id": "wb_dup", "type": "workbook", "repo": "ai_ops", "status": "active", "note": "book"},
            {"id": "wb_c", "type": "workbook", "repo": "governed_repo", "status": "planned", "note": "c"},
        ]
    },
}


class UpdateArtifactStatusTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "work_state.yaml"
        self.write(STATE)
        self.saved_path = mod._WORK_STATE_PATH
        mod._WORK_STATE_PATH = self.path

    def tearDown(self) -> None:
        mod._WORK_STATE_PATH = self.saved_path
        self.tmp.cleanup()

    def write(self, data: dict) -> None:
        with self.path.open("w", encoding="utf-8", newline="\n") as fh:
            yaml.dump(data, fh, default_flow_style=False, allow_unicode=True, sort_keys=False)

    def run_main(self, *argv: str) -> int:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return mod.main(list(argv))

    def entries(self) -> list[dict]:
        return yaml.safe_load(self.path.read_text(encoding="utf-8"))["work_context"]["active_artifacts"]

    def digest(self) -> str:
        return hashlib.sha256(self.path.read_bytes()).hexdigest()

    def test_status_removal_keeps_unrelated_entries(self) -> None:
        before = self.entries()
        self.assertEqual(self.run_main("--id", "wb_b", "--remove"), 0)
        after = self.entries()
        self.assertEqual([e["id"] for e in after], ["wb_a", "wb_dup", "wb_dup", "wb_c"])
        self.assertEqual(after, [e for e in before if e["id"] != "wb_b"])

    def test_dry_run_leaves_file_unchanged(self) -> None:
        digest = self.digest()
        self.assertEqual(self.run_main("--id", "wb_a", "--remove", "--dry-run"), 2)
        self.assertEqual(self.run_main("--id", "wb_b", "--remove", "--dry-run"), 0)
        self.assertEqual(self.run_main("--id", "wb_a", "--status", "completed", "--dry-run"), 0)
        self.assertEqual(self.digest(), digest)

    def test_active_or_planned_removal_is_rejected_without_writing(self) -> None:
        digest = self.digest()
        for artifact_id in ("wb_a", "wb_c"):
            self.assertEqual(self.run_main("--id", artifact_id, "--remove"), 2)
        self.assertEqual(self.digest(), digest)

    def test_missing_id(self) -> None:
        digest = self.digest()
        self.assertEqual(self.run_main("--id", "wb_missing", "--remove"), 1)
        self.assertEqual(self.run_main("--id", "wb_missing", "--status", "active"), 1)
        self.assertEqual(self.digest(), digest)

    def test_rejected_status_and_note_input(self) -> None:
        digest = self.digest()
        for status in ("archived", "blocked", "pending_operator_review", "superseded"):
            self.assertEqual(self.run_main("--id", "wb_a", "--status", status), 2)
        self.assertEqual(self.run_main("--id", "wb_a", "--status", "active", "--note", "x" * 301), 2)
        self.assertEqual(self.run_main("--id", "wb_a", "--status", "active", "--note", "a | b"), 0)
        self.assertNotEqual(self.digest(), digest)
        self.assertEqual(self.entries()[0]["note"], "a | b")
        self.assertEqual(self.run_main("--id", "wb_a", "--status", "complete", "--note", "y" * 300), 0)
        self.assertEqual(self.entries()[0]["status"], "completed")
        self.assertEqual(len(self.entries()[0]["note"]), 300)

    def test_beta_status_alias_normalizes_to_stub(self) -> None:
        self.assertEqual(self.run_main("--id", "wb_a", "--status", "beta"), 0)
        self.assertEqual(self.entries()[0]["status"], "stub")

    def test_archive_restoration(self) -> None:
        original = self.entries()
        index = 1
        archived = copy.deepcopy(original[index])
        self.assertEqual(self.run_main("--id", "wb_b", "--remove"), 0)
        data = yaml.safe_load(self.path.read_text(encoding="utf-8"))
        data["work_context"]["active_artifacts"].insert(index, archived)
        self.write(data)
        self.assertEqual(self.entries(), original)

    def test_duplicate_id_rejected_without_all_matches(self) -> None:
        digest = self.digest()
        self.assertEqual(self.run_main("--id", "wb_dup", "--remove"), 2)
        self.assertEqual(self.digest(), digest)
        data = copy.deepcopy(STATE)
        for entry in data["work_context"]["active_artifacts"]:
            if entry["id"] == "wb_dup":
                entry["status"] = "completed"
        self.write(data)
        self.assertEqual(self.run_main("--id", "wb_dup", "--remove", "--all-matches"), 0)
        self.assertEqual([e["id"] for e in self.entries()], ["wb_a", "wb_b", "wb_c"])

    def test_all_matches_rejects_when_any_duplicate_is_active(self) -> None:
        digest = self.digest()
        self.assertEqual(self.run_main("--id", "wb_dup", "--remove", "--all-matches"), 2)
        self.assertEqual(self.digest(), digest)

    def clean(self) -> dict:
        data = copy.deepcopy(STATE)
        del data["work_context"]["active_artifacts"][3]  # drop the duplicate id
        return data

    def test_check_exit_codes_and_read_only(self) -> None:
        self.write(self.clean())
        digest = self.digest()
        self.assertEqual(self.run_main("--check"), 0)
        self.assertEqual(self.digest(), digest)
        data = self.clean()
        data["work_context"]["active_artifacts"][0]["status"] = "pending_operator_review"
        self.write(data)
        self.assertEqual(self.run_main("--check"), 3)
        data = self.clean()
        data["work_context"]["active_artifacts"][1]["note"] = "z" * 301
        self.write(data)
        digest = self.digest()
        self.assertEqual(self.run_main("--check"), 3)
        self.assertEqual(self.digest(), digest)

    def test_targeted_check_limits_policy_scan(self) -> None:
        data = self.clean()
        data["work_context"]["active_artifacts"][2]["note"] = "z" * 301
        self.write(data)
        self.assertEqual(self.run_main("--check", "--id", "wb_a"), 0)
        self.assertEqual(self.run_main("--check", "--id", "wb_c"), 0)
        self.assertEqual(self.run_main("--check", "--id", "wb_dup"), 3)
        self.assertEqual(self.run_main("--check", "--id", "wb_missing"), 1)

    def test_check_flags_duplicate_ids(self) -> None:
        digest = self.digest()
        self.assertEqual(self.run_main("--check"), 3)
        self.assertEqual(self.digest(), digest)

    def test_status_update_rejects_duplicate_id_without_writing(self) -> None:
        digest = self.digest()
        self.assertEqual(self.run_main("--id", "wb_dup", "--status", "completed"), 2)
        self.assertEqual(self.digest(), digest)

    def test_missing_active_artifacts_is_a_state_error(self) -> None:
        self.write({"work_context": {}})
        digest = self.digest()
        self.assertEqual(self.run_main("--check"), 2)
        self.assertEqual(self.run_main("--id", "wb_a", "--status", "active"), 2)
        self.assertEqual(self.digest(), digest)

    def test_malformed_active_artifact_is_a_state_error(self) -> None:
        self.write({"work_context": {"active_artifacts": [{"status": "active"}]}})
        digest = self.digest()
        self.assertEqual(self.run_main("--check"), 2)
        self.assertEqual(self.run_main("--id", "wb_a", "--status", "active"), 2)
        self.assertEqual(self.digest(), digest)

    def test_check_rejects_non_text_note(self) -> None:
        data = self.clean()
        data["work_context"]["active_artifacts"][0]["note"] = {"unexpected": "mapping"}
        self.write(data)
        digest = self.digest()
        self.assertEqual(self.run_main("--check"), 3)
        self.assertEqual(self.digest(), digest)

    def test_null_or_empty_work_context_exits_2(self) -> None:
        for data in ({"work_context": None}, {"schema_version": 1}, {}):
            self.write(data)
            digest = self.digest()
            self.assertEqual(self.run_main("--check"), 2)
            self.assertEqual(self.run_main("--id", "wb_a", "--remove"), 2)
            self.assertEqual(self.run_main("--id", "wb_a", "--status", "active"), 2)
            self.assertEqual(self.digest(), digest)

    def test_unreadable_state_file_exits_2(self) -> None:
        for raw in (b"work_context: [unclosed\n", b"\xff\xfe not utf-8\n"):
            self.path.write_bytes(raw)
            self.assertEqual(self.run_main("--check"), 2)
            self.assertEqual(self.run_main("--id", "wb_a", "--remove"), 2)
            self.assertEqual(self.path.read_bytes(), raw)

    def test_write_failure_exits_2_and_leaves_no_temp_file(self) -> None:
        digest = self.digest()
        saved = mod.os.replace

        def fail(src, dst):
            raise PermissionError("locked")

        mod.os.replace = fail
        try:
            self.assertEqual(self.run_main("--id", "wb_b", "--remove"), 2)
            self.assertEqual(self.run_main("--id", "wb_a", "--status", "completed"), 2)
        finally:
            mod.os.replace = saved
        self.assertEqual(self.digest(), digest)
        self.assertEqual([p.name for p in self.path.parent.iterdir()], ["work_state.yaml"])

    def test_option_combinations_rejected(self) -> None:
        combinations = (
            ("--id", "wb_a"),
            ("--id", "wb_a", "--status", "active", "--remove"),
            ("--id", "wb_a", "--remove", "--note", "n"),
            ("--id", "wb_a", "--status", "active", "--all-matches"),
        )
        for argv in combinations:
            with self.assertRaises(SystemExit):
                self.run_main(*argv)

    def test_no_readme_flag_rejected(self) -> None:
        digest = self.digest()
        with self.assertRaises(SystemExit) as ctx:
            self.run_main("--id", "wb_a", "--status", "active", "--no-readme")
        self.assertEqual(ctx.exception.code, 2)
        self.assertEqual(self.digest(), digest)

    def test_status_update_leaves_readme_untouched(self) -> None:
        readme = self.path.parent / "README.md"
        readme.write_bytes(b"## Status\n\n| `wb_a` | active | a |\n- [ ] wb_a\n")
        data = copy.deepcopy(STATE)
        data["work_context"]["active_artifacts"][0]["path"] = str(readme)
        self.write(data)
        before = readme.read_bytes()
        self.assertEqual(self.run_main("--id", "wb_a", "--status", "completed"), 0)
        self.assertEqual(self.entries()[0]["status"], "completed")
        self.assertEqual(readme.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
