"""Focused contract tests for the closeout security pre-pass and validator."""

from __future__ import annotations

import hashlib
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

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

    def test_scope_lock_binds_status_and_digest(self) -> None:
        rows = [{"path": "a.txt", "mode": "100644", "sha256": "a" * 64}]
        first = PREPASS.scope_lock(["a.txt"], rows, {"a.txt": "D"})
        second = PREPASS.scope_lock(["a.txt"], rows, {"a.txt": "M"})
        self.assertNotEqual(first, second)
        self.assertEqual(first, PREPASS.scope_lock(["a.txt"], rows, {"a.txt": "D"}))

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
            receipt.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
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
            receipt.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
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
            receipt.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
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
            receipt.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
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
        with tempfile.TemporaryDirectory(dir=ROOT / "tmp") as directory:
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
        with tempfile.TemporaryDirectory(dir=ROOT / "tmp") as directory:
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


if __name__ == "__main__":
    unittest.main()
