"""Lifecycle tests for receipt-backed future-work completion."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("complete_future_work", SCRIPTS / "complete_future_work.py")
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


REGISTRY_TEMPLATE = (
    "entries:\n"
    "  - id: {registry_id}\n"
    "    source_workbook: source.md\n"
        "    completion_workbook: 90_Sandbox/ai_workbooks/wb_test_01.md\n"
        "    proposed_workbook: 90_Sandbox/ai_workbooks/wb_test_01.md\n"
    "    scope: Test scope\n"
    "    priority: low\n"
    "    created: 2026-10-23\n"
    "    status: deferred\n"
)
WORKBOOK = (
    "---\n"
    "title: Test workbook\n"
    "id: wb_test_01\n"
    "status: completed\n"
    "version: 1.0.0\n"
    "created: 2026-10-23\n"
    "ai_role: coordinator\n"
    "description: Test workbook\n"
    "---\n"
    "# Test workbook\n"
)


class FutureWorkCompletionTests(unittest.TestCase):
    def _fixture(self, registry_id: str) -> tuple[tempfile.TemporaryDirectory[str], Path, Path, Path, Path]:
        temp_dir = tempfile.TemporaryDirectory()
        root = Path(temp_dir.name)
        (root / "00_Admin" / "backlog").mkdir(parents=True)
        (root / "00_Admin" / "logs").mkdir(parents=True)
        (root / "90_Sandbox" / "ai_workbooks").mkdir(parents=True)
        registry = root / "00_Admin" / "backlog" / "future_work_registry.yaml"
        log = root / "00_Admin" / "logs" / "log_workbook_run.md"
        scorecard = root / "00_Admin" / "backlog" / "future_work_scorecard.md"
        workbook = root / "90_Sandbox" / "ai_workbooks" / "wb_test_01.md"
        review = root / "90_Sandbox" / "ai_workbooks" / "review_pass.md"
        registry.write_text(REGISTRY_TEMPLATE.format(registry_id=registry_id), encoding="utf-8")
        log.write_text("# Run Log\n", encoding="utf-8")
        workbook.write_text(WORKBOOK, encoding="utf-8")
        review.write_text(
            "---\n"
            "status: completed\n"
            "review_type: completion\n"
            "workbook_ref: 90_Sandbox/ai_workbooks/wb_test_01.md\n"
            "---\n\n"
            "Verdict: PASS\n",
            encoding="utf-8",
        )
        scorecard.write_text("placeholder\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(root), "init", "--quiet"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", "Completion Tests"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.email", "tests@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(root), "add", "00_Admin/backlog/future_work_registry.yaml"], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "--quiet", "-m", "baseline"], check=True)
        return temp_dir, root, registry, log, scorecard

    def test_success_deletes_only_after_parity_and_writes_receipt(self) -> None:
        temp_dir, root, registry, log, scorecard = self._fixture("fw_20261023_90")
        try:
            receipt = MODULE.complete(
                repo=root,
                registry_path=registry,
                run_log_path=log,
                scorecard_path=scorecard,
                registry_id="fw_20261023_90",
                completion_workbook="90_Sandbox/ai_workbooks/wb_test_01.md",
                artifacts=["90_Sandbox/ai_workbooks/wb_test_01.md"],
                status="success",
                exit_code=0,
                actor="test-operator",
                run_id="00000000-0000-4000-8000-000000000090",
                provenance_refs=["90_Sandbox/ai_workbooks/review_pass.md"],
                packet_root=root / "packets",
            )
            data = yaml.safe_load(receipt.read_text(encoding="utf-8"))
            self.assertEqual("success", data["status"])
            self.assertTrue(data["registry_deleted"])
            self.assertNotIn("fw_20261023_90", registry.read_text(encoding="utf-8"))
            self.assertIn("run_id: 00000000-0000-4000-8000-000000000090", log.read_text(encoding="utf-8"))
            self.assertNotIn("fw_20261023_90", scorecard.read_text(encoding="utf-8"))
            receipt_data = yaml.safe_load(receipt.read_text(encoding="utf-8"))
            self.assertEqual(MODULE._sha256(log.read_bytes()), receipt_data["run_log_sha256"])
            MODULE.verify_receipt(
                repo=root,
                receipt_path=receipt,
                run_log_path=log,
                registry_path=registry,
            )
            workbook = root / "90_Sandbox" / "ai_workbooks" / "wb_test_01.md"
            workbook.write_text(
                workbook.read_text(encoding="utf-8").replace("version: 1.0.0", "version: 1.1.0"),
                encoding="utf-8",
            )
            MODULE.verify_receipt(
                repo=root,
                receipt_path=receipt,
                run_log_path=log,
                registry_path=registry,
            )
            tampered = yaml.safe_load(receipt.read_text(encoding="utf-8"))
            tampered["artifact_manifest"] = []
            tampered["receipt_sha256"] = MODULE._receipt_digest(tampered)
            receipt.write_text(yaml.safe_dump(tampered, sort_keys=False), encoding="utf-8")
            with self.assertRaises(MODULE.CompletionError):
                MODULE.verify_receipt(
                    repo=root,
                    receipt_path=receipt,
                    run_log_path=log,
                    registry_path=registry,
                )
        finally:
            temp_dir.cleanup()

    def test_success_requires_retained_nonblocking_review(self) -> None:
        temp_dir, root, registry, log, scorecard = self._fixture("fw_20261023_91")
        try:
            with self.assertRaises(MODULE.CompletionError):
                MODULE.complete(
                    repo=root,
                    registry_path=registry,
                    run_log_path=log,
                    scorecard_path=scorecard,
                    registry_id="fw_20261023_91",
                    completion_workbook="90_Sandbox/ai_workbooks/wb_test_01.md",
                    artifacts=["90_Sandbox/ai_workbooks/wb_test_01.md"],
                    status="success",
                    exit_code=0,
                    actor="test-operator",
                    provenance_refs=["test-evidence"],
                    packet_root=root / "packets",
                )
            self.assertIn("fw_20261023_91", registry.read_text(encoding="utf-8"))
        finally:
            temp_dir.cleanup()

    def test_receipt_ready_workbook_can_complete_before_final_closeout(self) -> None:
        temp_dir, root, registry, log, scorecard = self._fixture("fw_20261023_98")
        try:
            workbook = root / "90_Sandbox" / "ai_workbooks" / "wb_test_01.md"
            workbook.write_text(
                workbook.read_text(encoding="utf-8").replace(
                    "status: completed\n", "status: active\nexecution_status: completed\n"
                ).replace(
                    "version: 1.0.0\n", "version: 1.0.0\ncompletion_state: ready_for_receipt\n"
                ),
                encoding="utf-8",
            )
            receipt = MODULE.complete(
                repo=root,
                registry_path=registry,
                run_log_path=log,
                scorecard_path=scorecard,
                registry_id="fw_20261023_98",
                completion_workbook="90_Sandbox/ai_workbooks/wb_test_01.md",
                artifacts=["90_Sandbox/ai_workbooks/wb_test_01.md"],
                status="success",
                exit_code=0,
                actor="test-operator",
                run_id="00000000-0000-4000-8000-000000000098",
                provenance_refs=["90_Sandbox/ai_workbooks/review_pass.md"],
                packet_root=root / "packets",
            )
            data = yaml.safe_load(receipt.read_text(encoding="utf-8"))
            self.assertEqual("ready_for_receipt", data["completion_state"])
            MODULE.verify_receipt(
                repo=root,
                receipt_path=receipt,
                run_log_path=log,
                registry_path=registry,
            )
        finally:
            temp_dir.cleanup()

    def test_active_workbook_without_receipt_ready_state_is_rejected(self) -> None:
        temp_dir, root, registry, log, scorecard = self._fixture("fw_20261023_99")
        try:
            workbook = root / "90_Sandbox" / "ai_workbooks" / "wb_test_01.md"
            workbook.write_text(
                workbook.read_text(encoding="utf-8").replace(
                    "status: completed\n", "status: active\nexecution_status: completed\n"
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(MODULE.CompletionError, "completion_state"):
                MODULE.complete(
                    repo=root,
                    registry_path=registry,
                    run_log_path=log,
                    scorecard_path=scorecard,
                    registry_id="fw_20261023_99",
                    completion_workbook="90_Sandbox/ai_workbooks/wb_test_01.md",
                    artifacts=["90_Sandbox/ai_workbooks/wb_test_01.md"],
                    status="success",
                    exit_code=0,
                    actor="test-operator",
                    run_id="00000000-0000-4000-8000-000000000099",
                    provenance_refs=["90_Sandbox/ai_workbooks/review_pass.md"],
                    packet_root=root / "packets",
                )
        finally:
            temp_dir.cleanup()

    def test_unrelated_review_cannot_authorize_completion(self) -> None:
        temp_dir, root, registry, log, scorecard = self._fixture("fw_20261023_92")
        try:
            unrelated = root / "90_Sandbox" / "ai_workbooks" / "unrelated_review.md"
            unrelated.write_text(
                "---\nstatus: completed\nreview_type: completion\n"
                "workbook_ref: 90_Sandbox/ai_workbooks/other.md\n---\n\nVerdict: PASS\n",
                encoding="utf-8",
            )
            with self.assertRaises(MODULE.CompletionError):
                MODULE.complete(
                    repo=root,
                    registry_path=registry,
                    run_log_path=log,
                    scorecard_path=scorecard,
                    registry_id="fw_20261023_92",
                    completion_workbook="90_Sandbox/ai_workbooks/wb_test_01.md",
                    artifacts=["90_Sandbox/ai_workbooks/wb_test_01.md"],
                    status="success",
                    exit_code=0,
                    actor="test-operator",
                    provenance_refs=["90_Sandbox/ai_workbooks/unrelated_review.md"],
                    packet_root=root / "packets",
                )
            self.assertIn("fw_20261023_92", registry.read_text(encoding="utf-8"))
        finally:
            temp_dir.cleanup()

    def test_blocking_verdict_and_fenced_example_cannot_authorize_completion(self) -> None:
        temp_dir, root, registry, log, scorecard = self._fixture("fw_20261023_93")
        try:
            review = root / "90_Sandbox" / "ai_workbooks" / "blocking_review.md"
            review.write_text(
                "---\nstatus: completed\nreview_type: completion\n"
                "workbook_ref: 90_Sandbox/ai_workbooks/wb_test_01.md\n---\n\n"
                "Verdict: BLOCKING ISSUES\n\n```text\nVerdict: PASS\n```\n",
                encoding="utf-8",
            )
            with self.assertRaises(MODULE.CompletionError):
                MODULE.complete(
                    repo=root,
                    registry_path=registry,
                    run_log_path=log,
                    scorecard_path=scorecard,
                    registry_id="fw_20261023_93",
                    completion_workbook="90_Sandbox/ai_workbooks/wb_test_01.md",
                    artifacts=["90_Sandbox/ai_workbooks/wb_test_01.md"],
                    status="success",
                    exit_code=0,
                    actor="test-operator",
                    provenance_refs=["90_Sandbox/ai_workbooks/blocking_review.md"],
                    packet_root=root / "packets",
                )
        finally:
            temp_dir.cleanup()

    def test_head_registry_binding_is_required(self) -> None:
        temp_dir, root, registry, log, scorecard = self._fixture("fw_20261023_94")
        try:
            head_registry = registry.read_text(encoding="utf-8").replace(
                "proposed_workbook: 90_Sandbox/ai_workbooks/wb_test_01.md",
                "proposed_workbook: null",
            )
            registry.write_text(head_registry, encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", str(registry)], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "--quiet", "-m", "remove binding"], check=True)
            registry.write_text(REGISTRY_TEMPLATE.format(registry_id="fw_20261023_94"), encoding="utf-8")
            with self.assertRaisesRegex(MODULE.CompletionError, "HEAD registry entry"):
                MODULE.complete(
                    repo=root,
                    registry_path=registry,
                    run_log_path=log,
                    scorecard_path=scorecard,
                    registry_id="fw_20261023_94",
                    completion_workbook="90_Sandbox/ai_workbooks/wb_test_01.md",
                    artifacts=["90_Sandbox/ai_workbooks/wb_test_01.md"],
                    status="success",
                    exit_code=0,
                    actor="test-operator",
                    provenance_refs=["90_Sandbox/ai_workbooks/review_pass.md"],
                    packet_root=root / "packets",
                )
        finally:
            temp_dir.cleanup()

    def test_failed_pending_and_stale_preserve_registry(self) -> None:
        for offset, status in enumerate(("failed", "pending", "stale"), start=1):
            with self.subTest(status=status):
                registry_id = f"fw_20261023_{90 + offset:02d}"
                temp_dir, root, registry, _log, scorecard = self._fixture(registry_id)
                try:
                    receipt = MODULE.complete(
                        repo=root,
                        registry_path=registry,
                        run_log_path=root / "00_Admin" / "logs" / "log_workbook_run.md",
                        scorecard_path=scorecard,
                        registry_id=registry_id,
                        completion_workbook="90_Sandbox/ai_workbooks/wb_test_01.md",
                        artifacts=[],
                        status=status,
                        exit_code=1,
                        actor="test-operator",
                        run_id=f"00000000-0000-4000-8000-0000000000{offset:02d}",
                        packet_root=root / "packets",
                    )
                    self.assertIn(registry_id, registry.read_text(encoding="utf-8"))
                    self.assertEqual(status, yaml.safe_load(receipt.read_text(encoding="utf-8"))["status"])
                finally:
                    temp_dir.cleanup()

    def test_text_only_log_claim_cannot_complete_without_completed_workbook(self) -> None:
        temp_dir, root, registry, log, scorecard = self._fixture("fw_20261023_94")
        try:
            log.write_text("completion_workbook: 90_Sandbox/ai_workbooks/wb_test_01.md\n", encoding="utf-8")
            (root / "90_Sandbox" / "ai_workbooks" / "wb_test_01.md").write_text(
                WORKBOOK.replace("status: completed", "status: planned"), encoding="utf-8"
            )
            with self.assertRaises(MODULE.CompletionError):
                MODULE.complete(
                    repo=root,
                    registry_path=registry,
                    run_log_path=log,
                    scorecard_path=scorecard,
                    registry_id="fw_20261023_94",
                    completion_workbook="90_Sandbox/ai_workbooks/wb_test_01.md",
                    artifacts=["90_Sandbox/ai_workbooks/wb_test_01.md"],
                    status="success",
                    exit_code=0,
                    actor="test-operator",
                    run_id="00000000-0000-4000-8000-000000000094",
                    provenance_refs=["90_Sandbox/ai_workbooks/review_pass.md"],
                    packet_root=root / "packets",
                )
            self.assertIn("fw_20261023_94", registry.read_text(encoding="utf-8"))
        finally:
            temp_dir.cleanup()

    def test_success_artifacts_must_include_completion_workbook(self) -> None:
        temp_dir, root, registry, log, scorecard = self._fixture("fw_20261023_97")
        try:
            artifact = root / "evidence.txt"
            artifact.write_text("evidence\n", encoding="utf-8")
            with self.assertRaises(MODULE.CompletionError):
                MODULE.complete(
                    repo=root,
                    registry_path=registry,
                    run_log_path=log,
                    scorecard_path=scorecard,
                    registry_id="fw_20261023_97",
                    completion_workbook="90_Sandbox/ai_workbooks/wb_test_01.md",
                    artifacts=["evidence.txt"],
                    status="success",
                    exit_code=0,
                    actor="test-operator",
                    run_id="00000000-0000-4000-8000-000000000097",
                    provenance_refs=["90_Sandbox/ai_workbooks/review_pass.md"],
                    packet_root=root / "packets",
                )
            self.assertIn("fw_20261023_97", registry.read_text(encoding="utf-8"))
        finally:
            temp_dir.cleanup()

    def test_external_canonical_path_is_rejected(self) -> None:
        temp_dir, root, _registry, log, scorecard = self._fixture("fw_20261023_95")
        try:
            outside = Path(temp_dir.name).parent / "outside-registry.yaml"
            outside.write_text("entries: []\n", encoding="utf-8")
            with self.assertRaises(MODULE.CompletionError):
                MODULE.complete(
                    repo=root,
                    registry_path=outside,
                    run_log_path=log,
                    scorecard_path=scorecard,
                    registry_id="fw_20261023_95",
                    completion_workbook="90_Sandbox/ai_workbooks/wb_test_01.md",
                    artifacts=[],
                    status="pending",
                    exit_code=1,
                    actor="test-operator",
                    run_id="00000000-0000-4000-8000-000000000095",
                    packet_root=root / "packets",
                )
        finally:
            if outside.exists():
                outside.unlink()
            temp_dir.cleanup()

    def test_stale_journal_blocks_and_recovery_restores_target(self) -> None:
        temp_dir, root, registry, _log, _scorecard = self._fixture("fw_20261023_96")
        try:
            packet_root = root / "packets"
            receipt_dir = packet_root / "test-recovery"
            receipt_dir.mkdir(parents=True)
            backup = receipt_dir / "registry.before"
            original = registry.read_bytes()
            backup.write_bytes(original)
            registry.write_text("entries:\n", encoding="utf-8")
            journal = receipt_dir / "transaction_journal.yaml"
            journal.write_text(
                yaml.safe_dump(
                    {
                        "version": "0.1.0",
                        "run_id": "00000000-0000-4000-8000-000000000096",
                        "phase": "prepared",
                        "targets": [
                            {
                                "name": "registry",
                                "path": str(registry),
                                "existed": True,
                                "sha256": MODULE._sha256(original),
                                "backup": str(backup),
                            }
                        ],
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            with self.assertRaises(MODULE.CompletionError):
                MODULE.complete(
                    repo=root,
                    registry_path=registry,
                    run_log_path=root / "00_Admin" / "logs" / "log_workbook_run.md",
                    scorecard_path=root / "00_Admin" / "backlog" / "future_work_scorecard.md",
                    registry_id="fw_20261023_96",
                    completion_workbook="90_Sandbox/ai_workbooks/wb_test_01.md",
                    artifacts=[],
                    status="pending",
                    exit_code=1,
                    actor="test-operator",
                    run_id="00000000-0000-4000-8000-000000000096",
                    packet_root=packet_root,
                )
            MODULE.recover_journal(root, journal)
            self.assertEqual(original, registry.read_bytes())
            self.assertFalse(receipt_dir.exists())
        finally:
            temp_dir.cleanup()


if __name__ == "__main__":
    unittest.main()
