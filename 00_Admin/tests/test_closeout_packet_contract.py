"""Contract tests for the tree-bound closeout packet lane."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

BUILDER_SPEC = importlib.util.spec_from_file_location("build_closeout_packet", SCRIPTS / "build_closeout_packet.py")
assert BUILDER_SPEC is not None and BUILDER_SPEC.loader is not None
BUILDER = importlib.util.module_from_spec(BUILDER_SPEC)
BUILDER_SPEC.loader.exec_module(BUILDER)
sys.modules["build_closeout_packet"] = BUILDER
APPLIER_SPEC = importlib.util.spec_from_file_location("apply_closeout_packet", SCRIPTS / "apply_closeout_packet.py")
assert APPLIER_SPEC is not None and APPLIER_SPEC.loader is not None
APPLIER = importlib.util.module_from_spec(APPLIER_SPEC)
APPLIER_SPEC.loader.exec_module(APPLIER)


class CloseoutPacketContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp_dir.name) / "repo"
        self.repo.mkdir()
        self._git("init", "-b", "main")
        self._git("config", "user.email", "tests@example.invalid")
        self._git("config", "user.name", "Packet Tests")
        (self.repo / "existing.txt").write_text("base\n", encoding="utf-8")
        policy = self.repo / "00_Admin" / "configs" / "closeout_security_tiers.yaml"
        policy.parent.mkdir(parents=True)
        policy.write_text("version: 1.0.0\n", encoding="utf-8")
        self._git("add", "--", "existing.txt", "00_Admin/configs/closeout_security_tiers.yaml")
        self._git("commit", "-m", "baseline")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _git(self, *args: str, check: bool = True) -> str:
        completed = subprocess.run(
            ["git", "-C", str(self.repo), *args],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if check and completed.returncode:
            raise AssertionError(completed.stderr)
        return completed.stdout.strip()

    def _approval(self, packet_path: Path) -> Path:
        packet = yaml.safe_load(packet_path.read_text(encoding="utf-8"))
        approval = packet_path.parent / "approval.yaml"
        approval.write_text(
            yaml.safe_dump(
                {
                    "decision": "approve",
                    "run_id": packet["run_id"],
                    "packet_sha256": packet["prepared_packet_sha256"],
                    "head": packet["head"],
                    "branch": packet["branch"],
                    "projected_tree_sha256": packet["projected_tree_sha256"],
                    "include_set_sha256": packet["include_set_sha256"],
                    "mutation_plan_sha256": packet["mutation_plan_sha256"],
                    "approved_by": "test-operator",
                    "approved_at": "2026-10-23T00:00:00+00:00",
                    "approval_ref": "test-approval",
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        return approval

    def test_builder_and_applier_bind_exact_tree_and_preserve_unrelated_stage(self) -> None:
        (self.repo / "unrelated.txt").write_text("unrelated\n", encoding="utf-8")
        self._git("add", "--", "unrelated.txt")
        (self.repo / "existing.txt").write_text("changed\n", encoding="utf-8")
        (self.repo / "new.txt").write_text("new\n", encoding="utf-8")
        packet = BUILDER.build_packet(
            self.repo,
            ["existing.txt", "new.txt"],
            "apply packet test",
            self.repo / "packets",
            allow_fixture_defaults=True,
        )
        commit_sha = APPLIER.apply_packet(packet, self._approval(packet))
        self.assertEqual(40, len(commit_sha))
        committed = self._git("diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").splitlines()
        self.assertEqual(["existing.txt", "new.txt"], committed)
        self.assertEqual(["unrelated.txt"], self._git("diff", "--cached", "--name-only").splitlines())
        packet_data = yaml.safe_load(packet.read_text(encoding="utf-8"))
        self.assertEqual("APPLIED", packet_data["state"])
        self.assertTrue(packet_data["result"]["index_match"])
        self.assertTrue(packet_data["result"]["push_allowed"])
        self.assertEqual(commit_sha, APPLIER.verify_push_ready(packet))

    def test_multiline_commit_message_normalizes_body_trailer_and_crlf(self) -> None:
        (self.repo / "existing.txt").write_text("changed\n", encoding="utf-8")
        message = "  subject  \r\n\r\nBody line  \r\nCo-Authored-By: Test <test@example.invalid>\r\n"
        expected = "  subject\n\nBody line\nCo-Authored-By: Test <test@example.invalid>"
        self.assertEqual(expected, BUILDER.normalize_commit_message(message))
        packet = BUILDER.build_packet(
            self.repo, ["existing.txt"], message, self.repo / "packets", allow_fixture_defaults=True
        )
        packet_data = yaml.safe_load(packet.read_text(encoding="utf-8"))
        self.assertEqual(expected, packet_data["commit_message"])
        commit_sha = APPLIER.apply_packet(packet, self._approval(packet))
        self.assertEqual(commit_sha, self._git("rev-parse", "HEAD"))
        self.assertEqual(expected, BUILDER.normalize_commit_message(APPLIER._read_commit_message(self.repo)))

    def test_builder_rejects_nonignored_untracked_path_outside_include(self) -> None:
        (self.repo / "existing.txt").write_text("changed\n", encoding="utf-8")
        (self.repo / "stray.txt").write_text("not approved\n", encoding="utf-8")
        with self.assertRaisesRegex(BUILDER.PacketError, "outside the approved include set"):
            BUILDER.build_packet(
                self.repo, ["existing.txt"], "stray file test", self.repo / "packets", allow_fixture_defaults=True
            )

    def test_packet_tamper_is_rejected_before_repository_mutation(self) -> None:
        (self.repo / "existing.txt").write_text("changed\n", encoding="utf-8")
        packet = BUILDER.build_packet(
            self.repo, ["existing.txt"], "tamper test", self.repo / "packets", allow_fixture_defaults=True
        )
        approval = self._approval(packet)
        packet_data = yaml.safe_load(packet.read_text(encoding="utf-8"))
        packet_data["commit_message"] = "tampered"
        packet.write_text(yaml.safe_dump(packet_data, sort_keys=False), encoding="utf-8")
        with self.assertRaises(BUILDER.PacketError):
            APPLIER.apply_packet(packet, approval)
        self.assertEqual("baseline", self._git("log", "-1", "--pretty=%s"))
        self.assertEqual("", self._git("diff", "--cached", "--name-only"))

    def test_projection_drift_invalidates_before_staging(self) -> None:
        (self.repo / "existing.txt").write_text("changed\n", encoding="utf-8")
        packet = BUILDER.build_packet(
            self.repo, ["existing.txt"], "drift test", self.repo / "packets", allow_fixture_defaults=True
        )
        (self.repo / "existing.txt").write_text("drifted\n", encoding="utf-8")
        with self.assertRaises(BUILDER.PacketError):
            APPLIER.apply_packet(packet, self._approval(packet))
        packet_data = yaml.safe_load(packet.read_text(encoding="utf-8"))
        self.assertEqual("INVALIDATED", packet_data["state"])
        self.assertEqual("", self._git("diff", "--cached", "--name-only"))

    def test_builder_rejects_symlink_include(self) -> None:
        target = self.repo / "existing.txt"
        link = self.repo / "link.txt"
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks are unavailable in this test environment")
        with self.assertRaises(BUILDER.PacketError):
            BUILDER.build_packet(
                self.repo, ["link.txt"], "symlink test", self.repo / "packets", allow_fixture_defaults=True
            )

    def test_hook_mutation_invalidates_before_commit(self) -> None:
        (self.repo / "existing.txt").write_text("changed\n", encoding="utf-8")
        hook = self.repo / ".git" / "hooks" / "pre-commit"
        hook.write_text(
            "#!/usr/bin/env python\nimport sys\nsys.exit(0)\n",
            encoding="utf-8",
        )
        if os.name != "nt":
            hook.chmod(0o755)
        packet = BUILDER.build_packet(
            self.repo, ["existing.txt"], "hook test", self.repo / "packets", allow_fixture_defaults=True
        )
        hook.write_text("#!/bin/sh\nprintf 'mutated hook\\n' >> existing.txt\nexit 0\n", encoding="utf-8")
        with self.assertRaises(BUILDER.PacketError):
            APPLIER.apply_packet(packet, self._approval(packet))
        packet_data = yaml.safe_load(packet.read_text(encoding="utf-8"))
        self.assertEqual("INVALIDATED", packet_data["state"])

    def test_policy_snapshot_binds_head_bytes(self) -> None:
        snapshot = BUILDER.policy_snapshot(self.repo)
        self.assertEqual("target_HEAD", snapshot["source"])
        self.assertEqual(
            BUILDER.sha256_bytes(
                bytes(
                    BUILDER._git(
                        self.repo,
                        "show",
                        "HEAD:00_Admin/configs/closeout_security_tiers.yaml",
                        text=False,
                    )
                )
            ),
            snapshot["sha256"],
        )

    def test_workflow_packet_requires_generated_manifest(self) -> None:
        (self.repo / ".ai_ops" / "workflows").mkdir(parents=True)
        workflow = self.repo / ".ai_ops" / "workflows" / "closeout.md"
        workflow.write_text("changed\n", encoding="utf-8")
        with self.assertRaises(BUILDER.PacketError):
            BUILDER.build_packet(
                self.repo,
                [".ai_ops/workflows/closeout.md"],
                "coupling test",
                self.repo / "packets",
                allow_fixture_defaults=True,
            )

    def test_approval_base_binding_is_required(self) -> None:
        (self.repo / "existing.txt").write_text("changed\n", encoding="utf-8")
        packet = BUILDER.build_packet(
            self.repo, ["existing.txt"], "approval binding", self.repo / "packets", allow_fixture_defaults=True
        )
        approval = yaml.safe_load(self._approval(packet).read_text(encoding="utf-8"))
        approval.pop("head")
        approval_path = packet.parent / "approval-bad.yaml"
        approval_path.write_text(yaml.safe_dump(approval, sort_keys=False), encoding="utf-8")
        with self.assertRaises(BUILDER.PacketError):
            APPLIER.apply_packet(packet, approval_path)

    def test_applier_recomputes_cost_limits_from_observed_projection(self) -> None:
        packet = {
            "routing_contract": {
                "limits": {
                    "repositories": 1,
                    "roots_per_repository": 1,
                    "files": 1,
                    "bytes_searched": 10,
                    "elapsed_seconds": 120,
                }
            }
        }
        observed = {
            "repositories": 1,
            "roots_per_repository": 1,
            "files": 2,
            "bytes_searched": 10,
            "elapsed_seconds": 0,
        }
        exceeded = APPLIER._recomputed_exceeded(packet, observed, APPLIER.datetime.now(APPLIER.timezone.utc))
        self.assertEqual({"files": {"limit": 1, "observed": 2}}, exceeded)

    def test_cost_mismatch_preserves_parked_state(self) -> None:
        routing = self.repo / "00_Admin" / "configs" / "context_routing.yaml"
        routing.write_text(
            yaml.safe_dump(
                {
                    "version": "test",
                    "closeout_packet": {
                        "version": "test",
                        "packet_root": "packets",
                        "limits": {
                            "repositories": 1,
                            "roots_per_repository": 8,
                            "files": 1,
                            "bytes_searched": 100000,
                            "elapsed_seconds": 120,
                        },
                    },
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        (self.repo / "existing.txt").write_text("changed\n", encoding="utf-8")
        (self.repo / "second.txt").write_text("second\n", encoding="utf-8")
        packet = BUILDER.build_packet(
            self.repo,
            ["00_Admin/configs/context_routing.yaml", "existing.txt", "second.txt"],
            "park test",
            self.repo / "packets",
        )
        packet_data = yaml.safe_load(packet.read_text(encoding="utf-8"))
        packet_data["state"] = "PENDING"
        packet_data["approval_contract"]["packet_state"] = "PENDING"
        packet_data["cost_profile"]["exceeded"]["files"]["observed"] = 3
        digest = BUILDER.packet_digest(packet_data)
        packet_data["packet_sha256"] = digest
        packet_data["prepared_packet_sha256"] = digest
        packet.write_text(yaml.safe_dump(packet_data, sort_keys=False), encoding="utf-8")
        with self.assertRaises(BUILDER.PacketError):
            APPLIER.apply_packet(packet, self._approval(packet))
        self.assertEqual("PARKED", yaml.safe_load(packet.read_text(encoding="utf-8"))["state"])

    def test_post_commit_worktree_drift_blocks_push(self) -> None:
        (self.repo / "existing.txt").write_text("changed\n", encoding="utf-8")
        packet = BUILDER.build_packet(
            self.repo,
            ["existing.txt"],
            "post commit drift",
            self.repo / "packets",
            allow_fixture_defaults=True,
        )
        original_commit = APPLIER._run_commit

        def commit_then_drift(
            repo: Path, message: str, paths: list[str], hooks_path: Path | None = None
        ) -> tuple[int, str, str]:
            result = original_commit(repo, message, paths, hooks_path)
            (repo / "existing.txt").write_text("post-commit drift\n", encoding="utf-8")
            return result

        APPLIER._run_commit = commit_then_drift
        try:
            with self.assertRaises(BUILDER.PacketError):
                APPLIER.apply_packet(packet, self._approval(packet))
        finally:
            APPLIER._run_commit = original_commit
        packet_data = yaml.safe_load(packet.read_text(encoding="utf-8"))
        self.assertEqual("FAILED", packet_data["state"])
        self.assertNotIn("push_allowed", packet_data["result"])
        self.assertIn("do not push until verify-push succeeds", packet_data["result"]["recovery"])

    def test_executed_pre_commit_hook_mutation_is_rejected_before_commit(self) -> None:
        (self.repo / "existing.txt").write_text("changed\n", encoding="utf-8")
        hook = self.repo / ".git" / "hooks" / "pre-commit"
        hook.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        packet = BUILDER.build_packet(
            self.repo,
            ["existing.txt"],
            "executed hook test",
            self.repo / "packets",
            allow_fixture_defaults=True,
        )
        def mutate(repo: Path, _hook_name: str, env: dict[str, str] | None = None) -> tuple[int, str, str]:
            (repo / "existing.txt").write_text("hook mutation\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "--", "existing.txt"], env=env, check=True)
            return 0, "", ""

        with mock.patch.object(APPLIER, "_run_hook", side_effect=mutate):
            with self.assertRaises(BUILDER.PacketError):
                APPLIER.apply_packet(packet, self._approval(packet))
        self.assertEqual("baseline", self._git("log", "-1", "--pretty=%s"))
        self.assertEqual("", self._git("diff", "--cached", "--name-only"))

    def test_rejecting_commit_msg_hook_blocks_commit(self) -> None:
        (self.repo / "existing.txt").write_text("changed\n", encoding="utf-8")
        hook = self.repo / ".git" / "hooks" / "commit-msg"
        hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        if os.name != "nt":
            hook.chmod(0o755)
        packet = BUILDER.build_packet(
            self.repo,
            ["existing.txt"],
            "rejecting commit message hook",
            self.repo / "packets",
            allow_fixture_defaults=True,
        )
        with self.assertRaises(BUILDER.PacketError):
            APPLIER.apply_packet(packet, self._approval(packet))
        self.assertEqual("baseline", self._git("log", "-1", "--pretty=%s"))
        self.assertEqual("", self._git("diff", "--cached", "--name-only"))

    def test_native_second_pre_commit_mutation_is_rejected_before_commit(self) -> None:
        (self.repo / "existing.txt").write_text("changed\n", encoding="utf-8")
        hook = self.repo / ".git" / "hooks" / "pre-commit"
        hook.write_text("hook placeholder\n", encoding="utf-8")
        packet = BUILDER.build_packet(
            self.repo,
            ["existing.txt"],
            "native hook guard",
            self.repo / "packets",
            allow_fixture_defaults=True,
        )
        calls = 0

        def mutate_on_second(
            repo: Path, _hook_name: str, env: dict[str, str] | None = None
        ) -> tuple[int, str, str]:
            nonlocal calls
            calls += 1
            if calls == 2:
                (repo / "existing.txt").write_text("native mutation\n", encoding="utf-8")
                subprocess.run(["git", "-C", str(repo), "add", "--", "existing.txt"], env=env, check=True)
            return 0, "", ""

        with mock.patch.object(APPLIER, "_run_hook", side_effect=mutate_on_second):
            with self.assertRaises(BUILDER.PacketError) as context:
                APPLIER.apply_packet(packet, self._approval(packet))
        self.assertIn("pre-commit hook changed the real index before commit", str(context.exception))
        self.assertEqual(2, calls)
        self.assertEqual("baseline", self._git("log", "-1", "--pretty=%s"))
        self.assertEqual("", self._git("diff", "--cached", "--name-only"))

    def test_harmless_pre_commit_hook_allows_approved_commit(self) -> None:
        (self.repo / "existing.txt").write_text("changed\n", encoding="utf-8")
        hook = self.repo / ".git" / "hooks" / "pre-commit"
        hook.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        packet = BUILDER.build_packet(
            self.repo,
            ["existing.txt"],
            "harmless hook",
            self.repo / "packets",
            allow_fixture_defaults=True,
        )
        original_commit = APPLIER._run_commit

        def commit_without_sandbox_shell(
            repo: Path, message: str, paths: list[str], hooks_path: Path | None = None
        ) -> tuple[int, str, str]:
            self.assertIsNone(hooks_path)
            hook.unlink()
            try:
                return original_commit(repo, message, paths, hooks_path)
            finally:
                hook.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")

        with mock.patch.object(APPLIER, "_run_hook", return_value=(0, "", "")) as run_hook:
            with mock.patch.object(APPLIER, "_run_commit", side_effect=commit_without_sandbox_shell):
                commit_sha = APPLIER.apply_packet(packet, self._approval(packet))
        self.assertEqual(commit_sha, self._git("rev-parse", "HEAD"))
        self.assertEqual("harmless hook", self._git("log", "-1", "--pretty=%s"))
        self.assertEqual(2, run_hook.call_count)

    def test_copied_commit_msg_hook_rejection_blocks_commit(self) -> None:
        (self.repo / "existing.txt").write_text("changed\n", encoding="utf-8")
        pre_commit = self.repo / ".git" / "hooks" / "pre-commit"
        pre_commit.write_text("hook placeholder\n", encoding="utf-8")
        commit_msg = self.repo / ".git" / "hooks" / "commit-msg"
        commit_msg.write_text("#!/bin/sh\nprintf 'commit-msg rejected\\n' >&2\nexit 1\n", encoding="utf-8")
        packet = BUILDER.build_packet(
            self.repo,
            ["existing.txt"],
            "copied commit message rejection",
            self.repo / "packets",
            allow_fixture_defaults=True,
        )
        def reject_commit(
            _repo: Path, _message: str, _paths: list[str], hooks_path: Path | None = None
        ) -> tuple[int, str, str]:
            self.assertIsNone(hooks_path)
            return 1, "", "commit-msg rejected"

        with mock.patch.object(APPLIER, "_run_hook", return_value=(0, "", "")):
            with mock.patch.object(APPLIER, "_run_commit", side_effect=reject_commit):
                with self.assertRaises(BUILDER.PacketError) as context:
                    APPLIER.apply_packet(packet, self._approval(packet))
        self.assertIn("commit-msg rejected", str(context.exception))
        self.assertEqual("baseline", self._git("log", "-1", "--pretty=%s"))
        self.assertEqual("", self._git("diff", "--cached", "--name-only"))


if __name__ == "__main__":
    unittest.main()
