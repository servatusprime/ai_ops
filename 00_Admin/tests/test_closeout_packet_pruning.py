from __future__ import annotations

import importlib.util
import io
import sys
import tempfile
import unittest
import uuid
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "00_Admin" / "scripts" / "prune_closeout_packets.py"
sys.path.insert(0, str(ROOT / "00_Admin" / "scripts"))
SPEC = importlib.util.spec_from_file_location("prune_closeout_packets", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class CloseoutPacketPruningTests(unittest.TestCase):
    def _packet(
        self,
        repo: Path,
        run_id: str,
        state: str,
        *,
        valid: bool = True,
        schema_valid: bool = True,
    ) -> Path:
        path = repo / "90_Sandbox" / "ai_workbooks" / "_closeout_packets" / repo.name / run_id
        path.mkdir(parents=True)
        packet = {
            "packet_version": "0.3.1",
            "run_id": run_id,
            "repo_id": repo.name,
            "repo_root": str(repo.resolve()),
            "head": "a" * 40,
            "branch": "main",
            "remote": "origin",
            "remote_url": None,
            "commit_message": "test packet",
            "include": ["README.md"],
            "exclude": [],
            "include_set_sha256": "b" * 64,
            "mutation_plan_sha256": "c" * 64,
            "changes": [
                {
                    "path": "README.md",
                    "action": "modify",
                    "mode": "100644",
                    "blob_sha1": "d" * 40,
                    "sha256": "e" * 64,
                }
            ],
            "projected_tree_manifest": [{"mode": "100644", "path": "README.md", "blob_sha1": "d" * 40}],
            "projected_tree_sha256": "f" * 64,
            "archive_gate": {
                "required": False,
                "status": "not_applicable",
                "receipt_path": None,
                "receipt_sha256": None,
                "manifest_sha256": None,
                "source_absent": None,
                "collision_free": None,
                "tracked_deletions": [],
                "entries": [],
            },
            "pre_existing_index": {"fingerprint_sha256": "1" * 64, "paths": []},
            "pre_existing_index_preserved": {"fingerprint_sha256": "2" * 64, "paths": []},
            "hook_fingerprint": {"sha256": "3" * 64, "hooks_path": ".git/hooks", "files": []},
            "publication_preflight": {
                "publication_route": "direct",
                "protected_default_branch": "main",
                "base_branch": "main",
                "head_branch": "main",
                "required_status_checks": [],
                "allowed_merge_methods": ["merge"],
                "selected_merge_method": "merge",
                "selected_remote": "origin",
                "hook_runtime": {
                    "status": "verified",
                    "pre_commit": "verified",
                    "commit_msg": "verified",
                    "evidence": "test",
                },
            },
            "policy": {"source": "target_HEAD", "version": "0.6.0", "path": "policy", "sha256": "4" * 64},
            "routing_contract": {
                "source": "context_routing",
                "path": "routing",
                "version": "0.2.0",
                "sha256": "5" * 64,
                "limits": {"files": 1},
                "packet_root": "packets",
            },
            "cost_profile": {"limits": {}, "observed": {}, "exceeded": {}},
            "frozen_clock": {
                "started_at": "2026-01-01T00:00:00+00:00",
                "prepared_at": "2026-01-01T00:00:01+00:00",
            },
            "state": state,
            "approval_contract": {
                "approval_state": "PENDING",
                "packet_state": state,
                "required_decision": "combined_scope_clerical_commit_push_merge",
                "approval_turn": "combined",
                "push_separate": False,
                "approved_by": None,
                "approved_at": None,
                "approval_ref": None,
            },
            "result": {},
        }
        if not schema_valid:
            packet.pop("include")
        packet["packet_sha256"] = MODULE.builder.packet_digest(packet)
        packet["prepared_packet_sha256"] = packet["packet_sha256"]
        if not valid:
            packet["packet_sha256"] = "0" * 64
        packet_path = path / "closeout_packet.yaml"
        packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")
        return packet_path

    def test_plan_archives_terminal_non_final_packets_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir) / "ai_ops"
            repo.mkdir()
            final_id = str(uuid.uuid4())
            applied_id = str(uuid.uuid4())
            failed_id = str(uuid.uuid4())
            pending_id = str(uuid.uuid4())
            self._packet(repo, final_id, "APPLIED")
            self._packet(repo, applied_id, "APPLIED")
            self._packet(repo, failed_id, "FAILED")
            self._packet(repo, pending_id, "PENDING")
            future_work = repo / "90_Sandbox" / "ai_workbooks" / "_closeout_packets" / repo.name / str(uuid.uuid4())
            future_work.mkdir(parents=True)
            (future_work / "future_work_completion.yaml").write_text("status: complete\n", encoding="utf-8")

            plan = MODULE.plan_prune(repo, keep_run_id=final_id)

            self.assertEqual({applied_id, failed_id}, {record.run_id for record in plan.candidates})
            self.assertEqual({final_id, pending_id}, {record.run_id for record in plan.protected})
            self.assertEqual((future_work,), plan.non_closeout_entries)

    def test_applied_packets_are_preserved_without_final_run_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir) / "ai_ops"
            repo.mkdir()
            applied_id = str(uuid.uuid4())
            failed_id = str(uuid.uuid4())
            self._packet(repo, applied_id, "APPLIED")
            self._packet(repo, failed_id, "FAILED")

            plan = MODULE.plan_prune(repo)

            applied = next(record for record in plan.records if record.run_id == applied_id)
            self.assertEqual("preserve", applied.action)
            self.assertIn("final run ID", applied.reason)
            self.assertEqual((failed_id,), tuple(record.run_id for record in plan.candidates))

    def test_apply_archives_candidates_and_keeps_final_packet(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir) / "ai_ops"
            repo.mkdir()
            final_id = str(uuid.uuid4())
            failed_id = str(uuid.uuid4())
            final_path = self._packet(repo, final_id, "APPLIED")
            failed_path = self._packet(repo, failed_id, "FAILED")
            plan = MODULE.plan_prune(repo, keep_run_id=final_id)

            archived = MODULE.apply_plan(repo, plan)

            self.assertEqual(
                (repo / "99_Trash" / "closeout_packets" / repo.name / failed_id,),
                archived,
            )
            self.assertTrue(final_path.exists())
            self.assertFalse(failed_path.parent.exists())
            self.assertTrue(archived[0].exists())

    def test_keep_run_id_must_be_applied(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir) / "ai_ops"
            repo.mkdir()
            pending_id = str(uuid.uuid4())
            self._packet(repo, pending_id, "PENDING")

            with self.assertRaisesRegex(MODULE.PruneError, "APPLIED"):
                MODULE.plan_prune(repo, keep_run_id=pending_id)

    def test_invalid_packet_blocks_archive(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir) / "ai_ops"
            repo.mkdir()
            bad_id = str(uuid.uuid4())
            self._packet(repo, bad_id, "FAILED", valid=False)
            plan = MODULE.plan_prune(repo)

            self.assertEqual(1, len(plan.blocked))
            with self.assertRaisesRegex(MODULE.PruneError, "blocked"):
                MODULE.apply_plan(repo, plan)

    def test_schema_invalid_packet_blocks_archive_even_with_valid_digest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir) / "ai_ops"
            repo.mkdir()
            bad_id = str(uuid.uuid4())
            self._packet(repo, bad_id, "FAILED", schema_valid=False)
            plan = MODULE.plan_prune(repo)

            self.assertEqual(1, len(plan.blocked))
            self.assertIn("schema validation", plan.blocked[0].reason)

    def test_partial_archive_failure_rolls_back_prior_moves(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir) / "ai_ops"
            repo.mkdir()
            final_id = str(uuid.uuid4())
            first_id = str(uuid.uuid4())
            second_id = str(uuid.uuid4())
            self._packet(repo, final_id, "APPLIED")
            first = self._packet(repo, first_id, "FAILED")
            second = self._packet(repo, second_id, "INVALIDATED")
            plan = MODULE.plan_prune(repo, keep_run_id=final_id)
            real_move = MODULE.shutil.move
            calls = 0

            def move_with_failure(source: str, destination: str) -> str:
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("simulated archive failure")
                return real_move(source, destination)

            with patch.object(MODULE.shutil, "move", side_effect=move_with_failure):
                with self.assertRaisesRegex(MODULE.PruneError, "rollback was completed"):
                    MODULE.apply_plan(repo, plan)

            self.assertTrue(first.parent.exists())
            self.assertTrue(second.parent.exists())
            self.assertFalse((repo / "99_Trash" / "closeout_packets" / repo.name / first_id).exists())

    def test_symlinked_packet_file_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir) / "ai_ops"
            repo.mkdir()
            run_id = str(uuid.uuid4())
            packet = self._packet(repo, run_id, "FAILED")
            target = repo / "outside-packet.yaml"
            target.write_text(packet.read_text(encoding="utf-8"), encoding="utf-8")
            packet.unlink()
            try:
                packet.symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks are unavailable in this test environment")

            plan = MODULE.plan_prune(repo)

            self.assertEqual(1, len(plan.blocked))
            self.assertIn("reparse", plan.blocked[0].reason)

    def test_apply_requires_final_run_id_at_cli_boundary(self) -> None:
        with redirect_stderr(io.StringIO()):
            self.assertEqual(2, MODULE.main(["--repo-root", str(ROOT), "--apply"]))


if __name__ == "__main__":
    unittest.main()
