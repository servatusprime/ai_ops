"""Focused contract tests for the closeout security pre-pass and validator."""

from __future__ import annotations

import hashlib
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

ROOT = Path(__file__).resolve().parents[2]


def load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PREPASS = load("closeout_security_prepass", "00_Admin/scripts/closeout_security_prepass.py")
VALIDATOR = load("validate_closeout_security_receipt", "00_Admin/scripts/validate_closeout_security_receipt.py")
EMITTER = load("emit_closeout_security_snapshot", "00_Admin/scripts/emit_closeout_security_snapshot.py")


class CloseoutSecurityReceiptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = {
            "version": "0.1.0",
            "ruleset_version": "0.1.0",
            "tiers": {"T0": {"path_prefixes": ["90_Sandbox/"]}, "T1": {"path_prefixes": [""]}},
            "forced_t2_files": ["AGENTS.md"],
            "forced_t2_prefixes": [".ai_ops/workflows/"],
            "binary_extensions": [".bin"],
            "generated_prefixes": ["generated/"],
            "secret_patterns": [],
            "instruction_patterns": [],
        }

    def _write_receipt(self, path: Path, value: dict) -> None:
        value.pop("receipt_sha256", None)
        value["receipt_sha256"] = hashlib.sha256(VALIDATOR.canonical_receipt(value)).hexdigest()
        path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")

    def test_forced_t2_and_t0_routing(self) -> None:
        self.assertEqual("T2", PREPASS.tier_for("AGENTS.md", self.config))
        self.assertEqual("T2", PREPASS.tier_for(".ai_ops/workflows/closeout.md", self.config))
        self.assertEqual("T0", PREPASS.tier_for("90_Sandbox/note.md", self.config))
        self.assertEqual("T1", PREPASS.tier_for("00_Admin/scripts/tool.py", self.config))

    def test_prepass_tripwires_candidates(self) -> None:
        status, hits = PREPASS.scan_text("x.py", b"subprocess.run(cmd, shell=True)\n", self.config)
        self.assertEqual("candidate", status)
        self.assertTrue(hits)

    def test_binary_and_generated_classification(self) -> None:
        self.assertTrue(PREPASS.is_binary("x.bin", b"text", self.config))
        self.assertTrue(PREPASS.is_generated("generated/out.yaml", self.config))
        self.assertEqual(
            "hash_only_deleted_binary",
            PREPASS.review_basis("deleted_binary", True),
        )
        self.assertEqual("full_content", PREPASS.review_basis("deleted", False))
        self.assertEqual("digest_bound_binary", PREPASS.review_basis("binary", True))

    def test_total_review_budget_is_optional(self) -> None:
        config = {**self.config, "packet": {"max_total_review_tokens": 100}}
        self.assertEqual(100, PREPASS.enforce_total_review_budget([60, 40], config))
        with self.assertRaises(SystemExit):
            PREPASS.enforce_total_review_budget([60, 41], config)
        with self.assertRaises(SystemExit):
            VALIDATOR.enforce_total_review_budget([60, 41], config)
        self.assertEqual(101, PREPASS.enforce_total_review_budget([60, 41], self.config))
        self.assertEqual(
            101,
            PREPASS.enforce_total_review_budget(
                [60, 41], {**self.config, "packet": {"max_total_review_tokens": None}}
            ),
        )
        VALIDATOR.enforce_total_review_budget(
            [60, 41], {**self.config, "packet": {"max_total_review_tokens": None}}
        )
        with self.assertRaises(SystemExit):
            PREPASS.enforce_total_review_budget([1], {**self.config, "packet": {"max_total_review_tokens": True}})
        with self.assertRaises(SystemExit):
            VALIDATOR.enforce_total_review_budget([1], {**self.config, "packet": {"max_total_review_tokens": "100"}})

    def test_null_session_budget_batches_each_packet_without_dropping_scope(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            packet_paths = []
            for name in ("packet-a.md", "packet-b.md", "packet-c.md"):
                path = Path(temp_dir) / name
                path.write_text(name + "\n", encoding="utf-8")
                packet_paths.append(str(path))
            batches = PREPASS.build_review_batches(packet_paths, [10, 20, 30], None)
        self.assertEqual(3, len(batches))
        self.assertEqual(packet_paths, [batch["packet_files"][0] for batch in batches])

    def test_review_cost_warning_has_no_aggregate_ceiling(self) -> None:
        self.assertIsNone(PREPASS.REVIEW_COST_VISIBILITY_THRESHOLD)
        self.assertIsNone(PREPASS.review_cost_warning(10_000_000))

    def test_changed_text_can_reuse_full_baseline_for_bounded_delta(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            source = repo / "app.py"
            source.write_text("value = 1\n" + ("# stable\n" * 4000), encoding="utf-8")
            for command in (
                ["git", "init", "--quiet"],
                ["git", "config", "user.email", "test@example.invalid"],
                ["git", "config", "user.name", "Closeout Test"],
                ["git", "add", "app.py"],
                ["git", "commit", "--quiet", "-m", "fixture"],
            ):
                subprocess.run(command, cwd=repo, check=True)
            source.write_text(source.read_text(encoding="utf-8").replace("value = 1", "value = 2"), encoding="utf-8")
            subprocess.run(["git", "add", "app.py"], cwd=repo, check=True)
            current = source.read_bytes()
            old = {
                "sha256": hashlib.sha256(b"value = 1\n" + (b"# stable\n" * 4000)).hexdigest(),
                "mode": "100644",
                "file_kind": "text",
                "prepass_status": "clean",
                "review_basis": "full_content",
                "coverage": "fully_reviewed",
                "reviewer": "Sol",
                "reviewer_model": "medium",
                "reviewer_runtime": "test",
                "review_method": "full-file-plus-diff",
                "independent_pass": False,
                "independent_reviewer": "not_required",
                "independent_evidence": "not_required",
                "disposition": "pass",
                "finding_refs": [],
                "coverage_notes": "source_bytes=32000; review_basis=full_content",
            }
            row = {
                **old,
                "path": "app.py",
                "sha256": hashlib.sha256(current).hexdigest(),
                "source_bytes": len(current),
            }
            PREPASS.preserve_attestation(
                row,
                old,
                baseline_ref=".ai_ops/local/closeout_security/latest.baseline.yaml",
                baseline_sha256="a" * 64,
                repo=repo,
                source="staged",
                config={"packet": {"delta_reuse_min_bytes": 20, "delta_context_lines": 10, "delta_max_bytes": 20000}},
            )
            self.assertEqual("delta_with_baseline", row["review_basis"])
            self.assertEqual("pending", row["review_method"])
            self.assertIn("value = 2", row["_packet_content"])

    def test_incomplete_receipt_is_not_promoted_to_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            packet = repo / "packet.md"
            packet.write_text("baseline packet\n", encoding="utf-8")
            receipt_path = repo / "latest.yaml"
            existing = {
                "receipt_version": "0.2.0",
                "review_batches": [{
                    "id": "batch-001",
                    "packet_files": [str(packet)],
                    "packet_estimated_tokens": [4],
                    "packet_sha256": [hashlib.sha256(packet.read_bytes()).hexdigest()],
                }],
            }
            baseline_path, baseline = PREPASS.copy_baseline_receipt(repo, receipt_path, existing)
            self.assertIsNone(baseline_path)
            self.assertIsNone(baseline)

    def test_complete_baseline_capture_preserves_packet_bytes_before_refresh(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            packet = repo / "packet.md"
            packet.write_text("baseline packet\n", encoding="utf-8")
            receipt_path = repo / "latest.yaml"
            existing = {
                "receipt_version": "0.2.0",
                "rows": [{
                    "path": "app.py",
                    "review_basis": "full_content",
                    "coverage": "fully_reviewed",
                    "disposition": "pass",
                    "review_method": "full-file-plus-diff",
                    "reviewer": "Sol",
                }],
                "review_batches": [{
                    "id": "batch-001",
                    "packet_files": [str(packet)],
                    "packet_estimated_tokens": [4],
                    "packet_sha256": [hashlib.sha256(packet.read_bytes()).hexdigest()],
                }],
            }
            existing["receipt_sha256"] = PREPASS.receipt_digest(existing)
            baseline_path, baseline = PREPASS.copy_baseline_receipt(repo, receipt_path, existing)
            self.assertIsNotNone(baseline_path)
            self.assertIsNotNone(baseline)
            preserved_packet = repo / baseline["review_batches"][0]["packet_files"][0]
            self.assertTrue(preserved_packet.is_file())
            self.assertEqual(packet.read_bytes(), preserved_packet.read_bytes())
            self.assertNotEqual(packet.resolve(), preserved_packet.resolve())

    def test_independent_snapshot_emitter_binds_t2_rows(self) -> None:
        receipt = {
            "receipt_version": "0.2.0",
            "repo_root": "C:/repo",
            "base_head": "a" * 40,
            "source": "staged",
            "include_set_sha256": "b" * 64,
            "tiers_config_version": "0.2.0",
            "ruleset_version": "0.2.0",
            "scope_lock_sha256": "c" * 64,
            "source_bytes_total": 10,
            "review_tokens_total": 5,
            "review_batches": [{
                "id": "batch-001",
                "packet_files": ["packet.md"],
                "packet_estimated_tokens": [5],
                "packet_sha256": ["d" * 64],
            }],
            "rows": [{
                "path": "app.py",
                "sha256": "e" * 64,
                "revision_basis": "index:app.py",
                "file_kind": "text",
                "review_basis": "full_content",
                "mode": "100644",
                "source_bytes": 10,
                "tier": "T2",
                "coverage": "fully_reviewed",
                "prepass_status": "clean",
                "reviewer": "Primary",
                "reviewer_model": "maximum",
                "reviewer_runtime": "ai-ops-reviewer",
                "review_method": "full-file-plus-diff",
                "independent_pass": True,
                "independent_reviewer": "Sol",
                "independent_evidence": "pending",
                "chunk_count": 1,
                "disposition": "pass",
                "finding_refs": [],
                "coverage_notes": "",
            }],
        }
        snapshot = EMITTER.build_snapshot(
            receipt,
            {
                "independent_reviewer": "Sol",
                "rows": [{
                    "path": "app.py",
                    "sha256": "e" * 64,
                    "mode": "100644",
                    "reviewer": "Sol",
                    "disposition": "pass",
                    "review_notes": "Reviewed current staged bytes and bounded diff.",
                }],
            },
        )
        self.assertEqual("1.0.0", snapshot["snapshot_version"])
        self.assertEqual("app.py", snapshot["rows"][0]["path"])
        self.assertEqual("Sol", snapshot["rows"][0]["reviewer"])

    def test_default_review_budget_matches_policy_headroom(self) -> None:
        policy = yaml.safe_load(
            (ROOT / "00_Admin/configs/closeout_security_tiers.yaml").read_text(encoding="utf-8")
        )
        packet = policy["packet"]
        self.assertIsNone(packet["session_token_budget"])
        self.assertIsNone(packet["max_total_review_tokens"])
        self.assertIsNone(PREPASS.DEFAULT_MAX_TOTAL_REVIEW_TOKENS)
        self.assertIsNone(VALIDATOR.DEFAULT_MAX_TOTAL_REVIEW_TOKENS)
        self.assertEqual(128846, PREPASS.enforce_total_review_budget([128846], {}))

    def test_canonical_policy_enables_deterministic_admission_for_missing_policy_only(self) -> None:
        policy = yaml.safe_load(
            (ROOT / "00_Admin/configs/closeout_security_tiers.yaml").read_text(encoding="utf-8")
        )
        deterministic = policy["admission"]["deterministic_admission"]
        self.assertIs(True, deterministic["enabled"])
        self.assertEqual(["missing_target_policy"], deterministic["allowed_policy_sources"])
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            for command in (
                ["git", "init", "--quiet"],
                ["git", "config", "user.email", "test@example.invalid"],
                ["git", "config", "user.name", "Closeout Test"],
            ):
                subprocess.run(command, cwd=repo, check=True)
            (repo / "tracked.txt").write_text("fixture\n", encoding="utf-8")
            subprocess.run(["git", "add", "tracked.txt"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "--quiet", "-m", "fixture"], cwd=repo, check=True)
            for module in (PREPASS, VALIDATOR):
                with self.subTest(module=module.__name__, case="repository without policy or hook"):
                    module.validate_deterministic_applicability(repo, policy, "missing_target_policy")
                with self.subTest(module=module.__name__, case="target_HEAD source"):
                    with self.assertRaisesRegex(SystemExit, "not allowed"):
                        module.validate_deterministic_applicability(repo, policy, "target_HEAD")
                with self.subTest(module=module.__name__, case="ai_ops itself stays reviewer-read"):
                    with self.assertRaisesRegex(SystemExit, "target policy exists"):
                        module.validate_deterministic_applicability(ROOT, policy, "missing_target_policy")

    def test_deterministic_admission_is_machine_validated_without_review_packets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            policy = repo / "external_closeout_policy.yaml"
            policy.write_text(
                yaml.safe_dump({
                    **self.config,
                    "version": "0.4.0",
                    "ruleset_version": "0.4.0",
                    "packet": {
                        "estimated_tokens_per_packet": 20000,
                        "session_token_budget": 120000,
                        "max_total_review_tokens": 120000,
                    },
                    "admission": {
                        "reviewer_read": {"enabled": True, "reviewer_packets": True},
                        "deterministic_admission": {
                            "enabled": True,
                            "reviewer_packets": False,
                            "allowed_policy_sources": ["missing_target_policy"],
                        },
                    },
                    "forced_t2_files": [],
                    "forced_t2_prefixes": [],
                    "tiers": {
                        "T0": {"path_prefixes": []},
                        "T1": {"path_prefixes": [""]},
                        "T2": {"path_prefixes": []},
                    },
                }),
                encoding="utf-8",
            )
            note = repo / "note.txt"
            note.write_text("before\n", encoding="utf-8")
            for command in (
                ["git", "init", "--quiet"],
                ["git", "config", "user.email", "test@example.invalid"],
                ["git", "config", "user.name", "Closeout Test"],
                ["git", "add", "."],
                ["git", "commit", "--quiet", "-m", "fixture"],
            ):
                result = subprocess.run(command, cwd=repo, capture_output=True, text=True, check=False)
                self.assertEqual(0, result.returncode, result.stderr)
            note.write_text("after\n", encoding="utf-8")
            subprocess.run(["git", "add", "note.txt"], cwd=repo, check=True)
            receipt = repo / ".ai_ops/local/receipt.yaml"
            prepass = subprocess.run(
                [
                    sys.executable,
                    str(PREPASS.__file__),
                    "--repo-root", str(repo),
                    "--source", "staged",
                    "--config", str(policy),
                    "--admission-mode", "deterministic_admission",
                    "--policy-source", "missing_target_policy",
                    "--operator-approval-ref", "decision-123",
                    "--receipt-path", str(receipt),
                    "note.txt",
                ],
                cwd=repo,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, prepass.returncode, prepass.stderr)
            data = yaml.safe_load(receipt.read_text(encoding="utf-8"))
            self.assertEqual("0.4.0", data["receipt_version"])
            self.assertEqual("deterministic_admission", data["overall_disposition"])
            self.assertEqual([], data["review_batches"])
            self.assertEqual(0, data["review_tokens_total"])
            validation = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR.__file__),
                    "--repo-root", str(repo),
                    "--receipt", str(receipt),
                    "--config", str(policy),
                    "--gate",
                    "--staged",
                ],
                cwd=repo,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, validation.returncode, validation.stderr)
            data["overall_disposition"] = "pass"
            self._write_receipt(receipt, data)
            invalid_deterministic = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR.__file__),
                    "--repo-root", str(repo),
                    "--receipt", str(receipt),
                    "--config", str(policy),
                    "--gate",
                    "--staged",
                ],
                cwd=repo,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(0, invalid_deterministic.returncode)

    def test_deterministic_admission_rejects_policy_and_hook_governed_repo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            (repo / "00_Admin/configs").mkdir(parents=True)
            policy = {
                **self.config,
                "version": "0.4.0",
                "ruleset_version": "0.4.0",
                "admission": {
                    "deterministic_admission": {
                        "enabled": True,
                        "allowed_policy_sources": ["target_HEAD", "missing_target_policy"],
                    }
                },
            }
            (repo / "00_Admin/configs/closeout_security_tiers.yaml").write_text(
                yaml.safe_dump(policy), encoding="utf-8"
            )
            (repo / ".pre-commit-config.yaml").write_text(
                "repos:\n"
                "  - repo: local\n"
                "    hooks:\n"
                "      - id: ai-ops-closeout-security\n"
                "        entry: python 00_Admin/scripts/hooks/validate_closeout_security_head.py\n",
                encoding="utf-8",
            )
            tracked = repo / "tracked.txt"
            tracked.write_text("fixture\n", encoding="utf-8")
            for command in (
                ["git", "init", "--quiet"],
                ["git", "config", "user.email", "test@example.invalid"],
                ["git", "config", "user.name", "Closeout Test"],
                ["git", "add", "."],
                ["git", "commit", "--quiet", "-m", "fixture"],
            ):
                result = subprocess.run(command, cwd=repo, capture_output=True, text=True, check=False)
                self.assertEqual(0, result.returncode, result.stderr)
            (repo / ".git/hooks/pre-commit").write_text(
                "#!/usr/bin/env bash\n"
                "ARGS=(hook-impl --config=.pre-commit-config.yaml --hook-type=pre-commit)\n"
                "exec pre-commit \"${ARGS[@]}\"\n",
                encoding="utf-8",
            )
            receipt = repo / "receipt.yaml"
            prepass = subprocess.run(
                [
                    sys.executable,
                    str(PREPASS.__file__),
                    "--repo-root", str(repo),
                    "--source", "head",
                    "--admission-mode", "deterministic_admission",
                    "--policy-source", "target_HEAD",
                    "--operator-approval-ref", "decision-123",
                    "--receipt-path", str(receipt),
                    "tracked.txt",
                ],
                cwd=repo,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(0, prepass.returncode)
            self.assertIn("not applicable", prepass.stderr)
            with self.assertRaises(SystemExit):
                VALIDATOR.validate_deterministic_applicability(repo, policy, "target_HEAD")

    def test_deterministic_admission_rejects_hook_only_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            subprocess.run(["git", "init", "--quiet"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Closeout Test"], cwd=repo, check=True)
            (repo / "tracked.txt").write_text("fixture\n", encoding="utf-8")
            subprocess.run(["git", "add", "tracked.txt"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "--quiet", "-m", "fixture"], cwd=repo, check=True)
            (repo / ".pre-commit-config.yaml").write_text(
                "repos:\n"
                "  - repo: local\n"
                "    hooks:\n"
                "      - id: ai-ops-closeout-security\n"
                "        entry: python 00_Admin/scripts/hooks/validate_closeout_security_head.py\n",
                encoding="utf-8",
            )
            (repo / ".git/hooks/pre-commit").write_text(
                "validate_closeout_security_head.py\n", encoding="utf-8"
            )
            policy = {
                "admission": {
                    "deterministic_admission": {
                        "enabled": True,
                        "allowed_policy_sources": ["missing_target_policy"],
                    }
                }
            }
            for module in (PREPASS, VALIDATOR):
                with self.subTest(module=module.__name__):
                    with self.assertRaisesRegex(SystemExit, "policy or closeout hook"):
                        module.validate_deterministic_applicability(
                            repo, policy, "missing_target_policy"
                        )

    def test_hook_detection_uses_common_git_dir_for_linked_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir) / "main"
            linked = Path(temp_dir) / "linked"
            repo.mkdir()
            subprocess.run(["git", "init", "--quiet"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Closeout Test"], cwd=repo, check=True)
            (repo / "tracked.txt").write_text("fixture\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "--quiet", "-m", "fixture"], cwd=repo, check=True)
            subprocess.run(
                ["git", "worktree", "add", "--detach", str(linked)],
                cwd=repo,
                capture_output=True,
                text=True,
                check=True,
            )
            (repo / ".git/hooks/pre-commit").write_text(
                "validate_closeout_security_head.py\n", encoding="utf-8"
            )
            self.assertTrue(PREPASS.closeout_hook_present(linked))
            self.assertTrue(VALIDATOR.closeout_hook_present(linked))

    def test_deterministic_admission_rejects_pre_push_dispatcher(self) -> None:
        for module in (PREPASS, VALIDATOR):
            with self.subTest(module=module.__name__):
                with tempfile.TemporaryDirectory() as temp_dir:
                    repo = Path(temp_dir)
                    subprocess.run(["git", "init", "--quiet"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "config", "user.email", "test@example.invalid"],
                        cwd=repo,
                        check=True,
                    )
                    subprocess.run(
                        ["git", "config", "user.name", "Closeout Test"],
                        cwd=repo,
                        check=True,
                    )
                    (repo / "tracked.txt").write_text("fixture\n", encoding="utf-8")
                    subprocess.run(["git", "add", "tracked.txt"], cwd=repo, check=True)
                    subprocess.run(["git", "commit", "--quiet", "-m", "fixture"], cwd=repo, check=True)
                    (repo / ".git/hooks/pre-push").write_text(
                        "#!/usr/bin/env bash\nexec pre-push.dispatcher\n",
                        encoding="utf-8",
                    )
                    (repo / ".git/hooks/pre-push.dispatcher").write_text(
                        "#!/usr/bin/env bash\n"
                        "ARGS=(hook-impl --config=.pre-commit-config.yaml --hook-type=pre-push)\n"
                        "exec pre-commit \"${ARGS[@]}\"\n",
                        encoding="utf-8",
                    )
                    (repo / ".pre-commit-config.yaml").write_text(
                        "repos:\n  - repo: local\n    hooks:\n      - id: ai-ops-closeout-security\n",
                        encoding="utf-8",
                    )
                    policy = {
                        "admission": {
                            "deterministic_admission": {
                                "enabled": True,
                                "allowed_policy_sources": ["missing_target_policy"],
                            }
                        }
                    }
                    with self.assertRaisesRegex(SystemExit, "policy or closeout hook"):
                        module.validate_deterministic_applicability(
                            repo, policy, "missing_target_policy"
                        )

    def test_hook_detection_fails_closed_when_git_path_cannot_be_resolved(self) -> None:
        repo = Path("unresolvable-repository")
        for module in (PREPASS, VALIDATOR):
            with self.subTest(module=module.__name__):
                failed_config = subprocess.CompletedProcess(
                    [], 2, stdout=b"", stderr=b"git metadata unavailable"
                )
                with mock.patch.object(module.subprocess, "run", return_value=failed_config):
                    with self.assertRaisesRegex(SystemExit, "cannot resolve Git hooks path"):
                        module.closeout_hook_present(repo)

    def test_policy_lookup_and_hook_read_errors_fail_closed(self) -> None:
        repo = Path("unresolvable-repository")
        for module in (PREPASS, VALIDATOR):
            with self.subTest(module=module.__name__, check="policy"):
                failed_policy = subprocess.CompletedProcess(
                    [], 128, stdout=b"", stderr=b"git metadata unavailable"
                )
                with mock.patch.object(module.subprocess, "run", return_value=failed_policy):
                    with self.assertRaisesRegex(SystemExit, "cannot determine target policy presence"):
                        module.target_policy_present(repo)

            with self.subTest(module=module.__name__, check="hook-read"):
                with tempfile.TemporaryDirectory() as temp_dir:
                    hook_repo = Path(temp_dir)
                    subprocess.run(["git", "init", "--quiet"], cwd=hook_repo, check=True)
                    hook = hook_repo / ".git/hooks/pre-commit"
                    hook.write_text("validate_closeout_security_head.py\n", encoding="utf-8")
                    with mock.patch.object(Path, "read_text", side_effect=OSError("permission denied")):
                        with self.assertRaisesRegex(SystemExit, "cannot read installed hook"):
                            module.closeout_hook_present(hook_repo)

    def test_dispatcher_config_read_error_fails_closed(self) -> None:
        for module in (PREPASS, VALIDATOR):
            with self.subTest(module=module.__name__):
                with tempfile.TemporaryDirectory() as temp_dir:
                    repo = Path(temp_dir)
                    subprocess.run(["git", "init", "--quiet"], cwd=repo, check=True)
                    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
                    subprocess.run(["git", "config", "user.name", "Closeout Test"], cwd=repo, check=True)
                    (repo / "tracked.txt").write_text("fixture\n", encoding="utf-8")
                    subprocess.run(["git", "add", "tracked.txt"], cwd=repo, check=True)
                    subprocess.run(["git", "commit", "--quiet", "-m", "fixture"], cwd=repo, check=True)
                    (repo / ".git/hooks/pre-commit").write_text("hook-impl\n", encoding="utf-8")
                    (repo / ".pre-commit-config.yaml").write_text("repos: []\n", encoding="utf-8")

                    with mock.patch.object(
                        Path,
                        "read_text",
                        side_effect=["hook-impl\n", OSError("permission denied")],
                    ):
                        with self.assertRaisesRegex(SystemExit, "cannot read dispatcher configuration"):
                            module.closeout_hook_present(repo)

    def test_large_deleted_structured_data_requires_parsed_safe_structure(self) -> None:
        config = {
            **self.config,
            "large_deleted_data": {
                "enabled": True,
                "min_source_bytes": 1,
                "approved_path_patterns": ["03_Projects/*"],
                "approved_extensions": [".geojson"],
                "blocked_structure_keys": ["command", "recovery"],
                "max_structure_nodes": 100,
            },
        }
        safe = (
            b'{"type":"FeatureCollection","features":[{"type":"Feature","geometry":'
            b'{"type":"Point","coordinates":[1,2]},"properties":{}}]}'
        )
        summary = PREPASS.structured_data_summary("03_Projects/map.geojson", safe, config)
        self.assertIsNotNone(summary)
        self.assertEqual("structured_deleted_data", PREPASS.review_basis("deleted", False, summary))
        blocked = b'{"type":"FeatureCollection","command":"run","features":[]}'
        self.assertIsNone(PREPASS.structured_data_summary("03_Projects/map.geojson", blocked, config))
        self.assertIsNone(
            PREPASS.structured_data_summary(
                "03_Projects/runner.json", b'{"steps":[{"argv":["python"]}]}', config
            )
        )
        self.assertIsNone(
            PREPASS.structured_data_summary(
                "03_Projects/bad.geojson", b'{"type":"FeatureCollection","features":"bad"}', config
            )
        )
        self.assertIsNone(
            PREPASS.structured_data_summary("03_Projects/bad.csv", b"a,b\n1\n", {**config, "large_deleted_data": {
                **config["large_deleted_data"], "approved_extensions": [".csv"]
            }})
        )
        self.assertIsNone(PREPASS.structured_data_summary("90_Sandbox/map.geojson", safe, config))
        for invalid in (
            b'{"type":"Object","features":[]}',
            b'{"type":"FeatureCollection","features":[{"type":"Feature","argv":[],"properties":{}}]}',
            b'{"type":"FeatureCollection","steps":[],"features":[]}',
            b'{"type":"FeatureCollection","features":[{"type":"Feature","geometry":{"type":"Point"},"properties":{}}]}',
            b'{"type":"FeatureCollection","features":[{"type":"Feature","geometry":{"type":"Point","coordinates":[{"argv":[]}]},"properties":{}}]}',
            b'{"type":"FeatureCollection","bbox":{"argv":[]},"features":[]}',
            b'{"type":"FeatureCollection","features":[{"type":"Feature","geometry":{"type":"Point","coordinates":[0,0],"geometries":{"argv":[]}},"properties":{}}]}',
            b'{"type":"FeatureCollection","features":[{"type":"Feature","geometry":{"type":"GeometryCollection","geometries":[],"coordinates":{"argv":[]}},"properties":{}}]}',
        ):
            self.assertIsNone(PREPASS.structured_data_summary("03_Projects/map.geojson", invalid, config))

    def test_structured_deleted_data_packet_omits_source_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            packet = Path(directory) / "packet.md"
            row = {
                "path": "03_Projects/map.geojson",
                "sha256": hashlib.sha256(b"large").hexdigest(),
                "revision_basis": "HEAD:03_Projects/map.geojson",
                "tier": "T1",
                "file_kind": "deleted",
                "review_basis": "structured_deleted_data",
                "prepass_status": "clean",
                "finding_refs": [],
                "content_bytes": 99999999,
                "structural_summary": '{"format":"json"};summary_sha256=' + "a" * 64,
            }
            paths, _, counts = PREPASS.build_packet([row], packet, 20000)
            packet_text = Path(paths[0]).read_text(encoding="utf-8")
            sections = VALIDATOR.parse_packet_sections(packet_text.encode("utf-8"))
        self.assertEqual(1, counts["03_Projects/map.geojson"])
        self.assertIsNone(sections[0]["content"])
        self.assertIn("Large deleted structured data content omitted", packet_text)

    def test_scope_lock_binds_status_and_digest(self) -> None:
        rows = [{"path": "a.txt", "mode": "100644", "sha256": "a" * 64}]
        first = PREPASS.scope_lock(["a.txt"], rows, {"a.txt": "D"})
        second = PREPASS.scope_lock(["a.txt"], rows, {"a.txt": "M"})
        self.assertNotEqual(first, second)
        self.assertEqual(first, PREPASS.scope_lock(["a.txt"], rows, {"a.txt": "D"}))

    def test_change_records_handles_large_include_sets_without_pathspec_expansion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            tracked = repo / "tracked.txt"
            tracked.write_text("before\n", encoding="utf-8")
            for command in (
                ["git", "init", "--quiet"],
                ["git", "config", "user.email", "test@example.invalid"],
                ["git", "config", "user.name", "Closeout Test"],
                ["git", "add", "tracked.txt"],
                ["git", "commit", "--quiet", "-m", "fixture"],
            ):
                result = subprocess.run(command, cwd=repo, capture_output=True, text=True, check=False)
                self.assertEqual(0, result.returncode, result.stderr)
            tracked.write_text("after\n", encoding="utf-8")
            long_paths = [f"requested/{'x' * 180}/{index}.txt" for index in range(800)]
            records = PREPASS.change_records(repo, ["tracked.txt", *long_paths], "worktree")
            self.assertEqual("M", records["tracked.txt"])
            self.assertEqual("H", records[long_paths[-1]])

    def test_prepass_budget_failure_writes_no_receipt_or_packet(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            repo = Path(directory)
            (repo / "00_Admin/configs").mkdir(parents=True)
            config = {
                **self.config,
                "packet": {
                    "estimated_tokens_per_packet": 20000,
                    "session_token_budget": 120000,
                    "max_total_review_tokens": 1000,
                },
            }
            (repo / "00_Admin/configs/closeout_security_tiers.yaml").write_text(
                yaml.safe_dump(config), encoding="utf-8"
            )
            receipt = repo / "receipt.yaml"
            packet = repo / "packet.md"
            with mock.patch.object(PREPASS, "git_head", return_value="a" * 40), \
                mock.patch.object(PREPASS, "is_deleted", return_value=False), \
                mock.patch.object(PREPASS, "read_source", return_value=(b"x" * 5000, "HEAD:large.txt")), \
                mock.patch.object(PREPASS, "change_records", return_value={"large.txt": "H"}), \
                mock.patch.object(PREPASS, "git_mode", return_value="100644"), \
                mock.patch.object(sys, "argv", [
                    "closeout_security_prepass.py",
                    "--repo-root", str(repo),
                    "--source", "head",
                    "--receipt-path", str(receipt),
                    "--packet-path", str(packet),
                    "large.txt",
                ]):
                with self.assertRaises(SystemExit):
                    PREPASS.main()
            self.assertFalse(receipt.exists())
            self.assertFalse(packet.exists())

    def test_evidence_references_are_hash_bound(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            evidence = repo / "evidence.txt"
            data = b"evidence"
            evidence.write_bytes(data)
            digest = hashlib.sha256(data).hexdigest()
            VALIDATOR.validate_evidence_ref(repo, f"evidence.txt@{digest}")
            with self.assertRaises(SystemExit):
                VALIDATOR.validate_evidence_ref(repo, f"missing.txt@{digest}")
            with self.assertRaises(SystemExit):
                VALIDATOR.validate_evidence_ref(repo, f"evidence.txt@{'0' * 64}")

    def test_structured_deleted_data_review_requires_recovered_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            artifact = b'{"type":"FeatureCollection","features":[]}'
            recovery = repo / "recovered.geojson"
            recovery.write_bytes(artifact)
            references = repo / "references.txt"
            references.write_text("dependency scan: no active references\n", encoding="utf-8")
            structure = repo / "structure.txt"
            structure.write_text("parsed FeatureCollection with zero records\n", encoding="utf-8")
            sha = hashlib.sha256(artifact).hexdigest()
            summary = '{"format":"json","records":0};summary_sha256=' + "a" * 64
            refs_hash = hashlib.sha256(references.read_bytes()).hexdigest()
            structure_hash = hashlib.sha256(structure.read_bytes()).hexdigest()
            recovery_hash = hashlib.sha256(recovery.read_bytes()).hexdigest()
            notes = (
                f"references=references.txt@{refs_hash}; recovery=recovered.geojson@{recovery_hash}; "
                f"structure=structure.txt@{structure_hash}; references_target_sha256={sha}; "
                f"recovery_target_sha256={sha}; recovery_path=recovered.geojson; "
                f"structure_summary_sha256={hashlib.sha256(summary.encode()).hexdigest()}; "
                "producer=source-system; consumers=no-active-consumer; retention_owner=repo-owner; "
                "retrieval_method=path"
            )
            row = {
                "path": "03_Projects/old.geojson",
                "sha256": sha,
                "file_kind": "deleted",
                "review_basis": "structured_deleted_data",
                "prepass_status": "clean",
                "review_method": "structured-deletion-reference-review",
                "structural_summary": summary,
                "coverage_notes": notes,
            }
            VALIDATOR.validate_structured_deleted_data_review(repo, row)
            recovery.write_bytes(b"changed")
            with self.assertRaises(SystemExit):
                VALIDATOR.validate_structured_deleted_data_review(repo, row)

    def test_review_approval_requires_affirmative_frozen_scope_and_timezone(self) -> None:
        scope = "a" * 64
        valid = {
            "scope_lock_sha256": scope,
            "approved_by": "operator",
            "approved_at": "2026-10-21T12:00:00Z",
            "decision": "approve",
        }
        VALIDATOR.validate_review_approval(valid, scope)
        for invalid in (
            {**valid, "decision": "hold"},
            {**valid, "approved_at": "2026-10-21T12:00:00"},
            {**valid, "scope_lock_sha256": "b" * 64},
            {**valid, "approved_by": " pending "},
            {**valid, "approved_by": "none"},
        ):
            with self.assertRaises(SystemExit):
                VALIDATOR.validate_review_approval(invalid, scope)

    def test_v2_shape_requires_batch_and_deletion_attestation_fields(self) -> None:
        receipt = {
            "receipt_version": "0.2.0",
            "repo_root": str(ROOT),
            "base_head": "a" * 40,
            "source": "staged",
            "include_set_sha256": "b" * 64,
            "tiers_config_version": "0.2.0",
            "ruleset_version": "0.2.0",
            "scope_lock_sha256": "c" * 64,
            "source_bytes_total": 10,
            "review_tokens_total": 5,
            "review_batches": [{
                "id": "batch-001",
                "packet_files": ["packet.md"],
                "packet_estimated_tokens": [5],
                "packet_sha256": ["d" * 64],
            }],
            "rows": [{
                "path": "old.pdf",
                "sha256": "e" * 64,
                "revision_basis": "HEAD:old.pdf",
                "file_kind": "deleted_binary",
                "review_basis": "hash_only_deleted_binary",
                "mode": "100644",
                "source_bytes": 10,
                "tier": "T1",
                "coverage": "not_reviewed",
                "prepass_status": "clean",
                "reviewer": "pending",
                "reviewer_model": "medium",
                "reviewer_runtime": "ai-ops-reviewer",
                "review_method": "pending",
                "independent_pass": False,
                "independent_reviewer": "pending",
                "independent_evidence": "pending",
                "chunk_count": 1,
                "disposition": "pending",
                "finding_refs": [],
                "coverage_notes": "",
            }],
        }
        VALIDATOR.validate_shape(receipt)
        invalid = dict(receipt)
        invalid["rows"] = [dict(receipt["rows"][0], review_basis="hash_only_deleted_text")]
        with self.assertRaises(SystemExit):
            VALIDATOR.validate_shape(invalid)

    def test_v2_gate_accepts_hash_only_deleted_binary_with_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            (repo / "00_Admin/configs").mkdir(parents=True)
            (repo / "00_Admin/configs/closeout_security_tiers.yaml").write_text(
                yaml.safe_dump({
                    "version": "0.2.0",
                    "ruleset_version": "0.2.0",
                    "packet": {"estimated_tokens_per_packet": 20000, "session_token_budget": 120000},
                    "tiers": {
                        "T0": {"path_prefixes": ["90_Sandbox/"]},
                        "T1": {"path_prefixes": [""]},
                        "T2": {"path_prefixes": []},
                    },
                    "forced_t2_files": [],
                    "forced_t2_prefixes": [],
                    "binary_extensions": [".pdf"],
                    "generated_prefixes": [],
                    "secret_patterns": [],
                    "instruction_patterns": [],
                }),
                encoding="utf-8",
            )
            old = repo / "old.pdf"
            old.write_bytes(b"%PDF-1.7\nfixture\n")
            for command in (
                ["git", "init", "--quiet"],
                ["git", "config", "user.email", "test@example.invalid"],
                ["git", "config", "user.name", "Closeout Test"],
                ["git", "add", "00_Admin/configs/closeout_security_tiers.yaml", "old.pdf"],
                ["git", "commit", "--quiet", "-m", "fixture"],
                ["git", "rm", "--quiet", "old.pdf"],
            ):
                result = subprocess.run(command, cwd=repo, capture_output=True, text=True, check=False)
                self.assertEqual(0, result.returncode, result.stderr)
            receipt = repo / "receipt.yaml"
            packet = repo / "packet.md"
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "00_Admin/scripts/closeout_security_prepass.py"),
                    "--repo-root", str(repo), "--source", "staged",
                    "--receipt-path", str(receipt), "--packet-path", str(packet), "old.pdf",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            data = yaml.safe_load(receipt.read_text(encoding="utf-8"))
            row = data["rows"][0]
            self.assertEqual("HEAD:old.pdf", row["revision_basis"])
            row.update({
                "coverage": "fully_reviewed",
                "reviewer": "Sol",
                "review_method": "hash-only-deletion-reference-review",
                "disposition": "pass",
            })
            evidence = repo / "deletion-review.txt"
            evidence.write_text(f"artifact_sha256={row['sha256']}\n", encoding="utf-8")
            evidence_digest = hashlib.sha256(evidence.read_bytes()).hexdigest()
            valid_notes = (
                "source_bytes=18; review_basis=hash_only_deleted_binary; "
                f"references=deletion-review.txt@{evidence_digest}; "
                f"recovery=deletion-review.txt@{evidence_digest}; "
                f"references_target_sha256={row['sha256']}; recovery_target_sha256={row['sha256']}"
            )
            row["coverage_notes"] = valid_notes
            row["file_kind"] = "deleted"
            row["review_basis"] = "full_content"
            row["review_method"] = "full-file-plus-diff"
            self._write_receipt(receipt, data)
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "00_Admin/scripts/validate_closeout_security_receipt.py"),
                    "--repo-root", str(repo), "--receipt", str(receipt), "--gate", "--staged",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(0, result.returncode)
            row["file_kind"] = "deleted_binary"
            row["review_basis"] = "hash_only_deleted_binary"
            row["review_method"] = "hash-only-deletion-reference-review"
            row["coverage_notes"] = row["coverage_notes"].replace(
                f"recovery=deletion-review.txt@{evidence_digest}", "recovery=missing"
            )
            self._write_receipt(receipt, data)
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "00_Admin/scripts/validate_closeout_security_receipt.py"),
                    "--repo-root", str(repo), "--receipt", str(receipt), "--gate", "--staged",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(0, result.returncode)
            row["coverage_notes"] = row["coverage_notes"].replace(
                "recovery=missing", f"recovery=missing/path@{'0' * 64}"
            )
            self._write_receipt(receipt, data)
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "00_Admin/scripts/validate_closeout_security_receipt.py"),
                    "--repo-root", str(repo), "--receipt", str(receipt), "--gate", "--staged",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(0, result.returncode)
            row["coverage_notes"] = valid_notes
            self._write_receipt(receipt, data)
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "00_Admin/scripts/validate_closeout_security_receipt.py"),
                    "--repo-root", str(repo), "--receipt", str(receipt), "--gate", "--staged",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("PASS 1 rows source=staged gate=true", result.stdout)

    def test_v2_gate_accepts_structured_deleted_data_only_with_full_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            config = {
                "version": "0.2.0",
                "ruleset_version": "0.2.0",
                "packet": {"estimated_tokens_per_packet": 20000, "session_token_budget": 120000},
                "tiers": {
                    "T0": {"path_prefixes": ["90_Sandbox/"]},
                    "T1": {"path_prefixes": [""]},
                    "T2": {"path_prefixes": []},
                },
                "forced_t2_files": [],
                "forced_t2_prefixes": [],
                "binary_extensions": [".pdf"],
                "generated_prefixes": [],
                "secret_patterns": [],
                "instruction_patterns": [],
                "additional_tripwires": [],
                "large_deleted_data": {
                    "enabled": True,
                    "min_source_bytes": 1,
                    "approved_path_patterns": ["03_Projects/*/outputs/*"],
                    "approved_extensions": [".csv"],
                    "blocked_structure_keys": ["command", "recovery"],
                    "max_structure_nodes": 1000,
                },
            }
            config_path = repo / "00_Admin/configs/closeout_security_tiers.yaml"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
            old_path = repo / "03_Projects/test/outputs/old.csv"
            old_path.parent.mkdir(parents=True)
            old_path.write_text("id,value\n1,alpha\n", encoding="utf-8")
            for command in (
                ["git", "init", "--quiet"],
                ["git", "config", "user.email", "test@example.invalid"],
                ["git", "config", "user.name", "Closeout Test"],
                ["git", "add", "."],
                ["git", "commit", "--quiet", "-m", "fixture"],
                ["git", "rm", "--quiet", "03_Projects/test/outputs/old.csv"],
            ):
                result = subprocess.run(command, cwd=repo, capture_output=True, text=True, check=False)
                self.assertEqual(0, result.returncode, result.stderr)
            receipt = repo / "receipt.yaml"
            packet = repo / "packet.md"
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "00_Admin/scripts/closeout_security_prepass.py"),
                    "--repo-root", str(repo), "--config", str(config_path), "--source", "staged",
                    "--receipt-path", str(receipt), "--packet-path", str(packet),
                    "03_Projects/test/outputs/old.csv",
                ],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            data = yaml.safe_load(receipt.read_text(encoding="utf-8"))
            row = data["rows"][0]
            self.assertEqual("structured_deleted_data", row["review_basis"])
            recovery = repo / "recovered.csv"
            recovery.write_text("id,value\n1,alpha\n", encoding="utf-8")
            references = repo / "references.txt"
            references.write_text("dependency scan: no active references\n", encoding="utf-8")
            structure = repo / "structure.txt"
            structure.write_text("csv_tabular; fields=id,value; records=1\n", encoding="utf-8")
            refs_hash = hashlib.sha256(references.read_bytes()).hexdigest()
            structure_hash = hashlib.sha256(structure.read_bytes()).hexdigest()
            recovery_hash = hashlib.sha256(recovery.read_bytes()).hexdigest()
            summary_hash = hashlib.sha256(row["structural_summary"].encode()).hexdigest()
            row.update({
                "coverage": "fully_reviewed",
                "reviewer": "Sol",
                "review_method": "structured-deletion-reference-review",
                "disposition": "pass",
                "coverage_notes": (
                    f"references=references.txt@{refs_hash}; recovery=recovered.csv@{recovery_hash}; "
                    f"structure=structure.txt@{structure_hash}; references_target_sha256={row['sha256']}; "
                    f"recovery_target_sha256={row['sha256']}; recovery_path=recovered.csv; "
                    f"structure_summary_sha256={summary_hash}; producer=fixture; consumers=no-active-consumer; "
                    "retention_owner=operator; retrieval_method=recovered.csv"
                ),
            })
            data["review_approval"] = {
                "scope_lock_sha256": data["scope_lock_sha256"],
                "approved_by": "operator",
                "approved_at": "2026-10-21T12:00:00Z",
                "decision": "approve",
            }
            self._write_receipt(receipt, data)
            command = [
                sys.executable, str(ROOT / "00_Admin/scripts/validate_closeout_security_receipt.py"),
                "--repo-root", str(repo), "--receipt", str(receipt), "--gate", "--staged",
            ]
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(0, result.returncode, result.stderr)
            data["review_approval"]["decision"] = "hold"
            self._write_receipt(receipt, data)
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertNotEqual(0, result.returncode)

    def test_safe_paths_and_include_hash_are_deterministic(self) -> None:
        self.assertEqual("a/b.txt", PREPASS.rel_path("./a\\b.txt"))
        with self.assertRaises(SystemExit):
            PREPASS.rel_path("../outside.txt")
        self.assertEqual(VALIDATOR.include_hash(["b", "a"]), VALIDATOR.include_hash(["a", "b"]))

    def test_validator_rejects_unsafe_path_and_under_tier(self) -> None:
        with self.assertRaises(SystemExit):
            VALIDATOR.safe_path("../outside")
        self.assertTrue(
            VALIDATOR.forced_t2(
                "AGENTS.md", {"forced_t2_files": ["AGENTS.md"], "forced_t2_prefixes": []}
            )
        )
        self.assertTrue(
            VALIDATOR.forced_t2(
                "00_Admin/configs/new.yaml", {"forced_t2_files": [], "forced_t2_prefixes": []}
            )
        )

    def test_receipt_digest_omits_self_digest(self) -> None:
        receipt = {"receipt_version": "0.1.0", "rows": [], "receipt_sha256": "old"}
        digest = hashlib.sha256(VALIDATOR.canonical_receipt(receipt)).hexdigest()
        receipt["receipt_sha256"] = digest
        self.assertEqual(digest, hashlib.sha256(VALIDATOR.canonical_receipt(receipt)).hexdigest())

    def test_trailer_mismatch_fails(self) -> None:
        with self.assertRaises(SystemExit):
            VALIDATOR.check_trailer("Closeout-Security: pass wrong wrong", "pass", "a" * 64, "b" * 64)

    def test_receipt_source_bytes_reads_head_file(self) -> None:
        data, basis = VALIDATOR.source_bytes(ROOT, ".gitignore", "head", "text")
        self.assertTrue(data)
        self.assertEqual("HEAD:.gitignore", basis)

    def test_prepass_accepts_staged_source_mode(self) -> None:
        data, basis = PREPASS.read_source(ROOT, ".gitignore", "staged")
        self.assertTrue(data)
        self.assertEqual(":.gitignore", basis)

    def test_packet_sections_bind_full_text_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            packet = Path(directory) / "packet.md"
            content = "alpha\n```\nomega\n"
            row = {
                "path": "fixture.txt",
                "sha256": hashlib.sha256(content.encode()).hexdigest(),
                "revision_basis": "fixture",
                "tier": "T1",
                "file_kind": "text",
                "prepass_status": "clean",
                "finding_refs": [],
                "content": content,
                "content_bytes": len(content.encode()),
            }
            paths, _, counts = PREPASS.build_packet([row], packet, 20000)
            sections = VALIDATOR.parse_packet_sections(Path(paths[0]).read_bytes())
        self.assertEqual({"fixture.txt"}, {section["path"] for section in sections})
        self.assertEqual(1, counts["fixture.txt"])
        self.assertEqual(content, sections[0]["content"])

    def test_head_hook_rejects_trailer_when_receipt_is_missing(self) -> None:
        hook = ROOT / "00_Admin/scripts/hooks/validate_closeout_security_head.py"
        with tempfile.TemporaryDirectory() as directory:
            message = Path(directory) / "commit-message.txt"
            message.write_text("test\n\nCloseout-Security: pass x y\n", encoding="utf-8")
            receipt = ROOT / ".ai_ops/local/closeout_security/does-not-exist.yaml"
            result = subprocess.run(
                [
                    sys.executable,
                    str(hook),
                    "--repo-root",
                    str(ROOT),
                    "--receipt",
                    str(receipt),
                    "--staged",
                    "--commit-msg-file",
                    str(message),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(1, result.returncode)
        self.assertIn("receipt is missing", result.stderr)

    def test_head_hook_leaves_manual_first_landing_without_trailer_alone(self) -> None:
        hook = ROOT / "00_Admin/scripts/hooks/validate_closeout_security_head.py"
        receipt = ROOT / ".ai_ops/local/closeout_security/first_landing_only.yaml"
        with tempfile.TemporaryDirectory() as temp_dir:
            isolated_index = Path(temp_dir) / "index"
            hook_env = {**os.environ, "GIT_INDEX_FILE": str(isolated_index)}
            subprocess.run(
                ["git", "-C", str(ROOT), "read-tree", "HEAD"],
                env=hook_env,
                check=True,
                capture_output=True,
                text=True,
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(hook),
                    "--repo-root", str(ROOT),
                    "--receipt", str(receipt),
                    "--staged",
                ],
                env=hook_env,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("no receipt", result.stdout)


if __name__ == "__main__":
    unittest.main()
