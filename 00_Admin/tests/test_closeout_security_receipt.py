"""Focused contract tests for the closeout security pre-pass and validator."""

from __future__ import annotations

import hashlib
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

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
