"""Focused tests for future-work applicability gating."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from closeout_applicability import (
    ApplicabilityError,
    classify_future_work_applicability,
)


class CloseoutApplicabilityTests(unittest.TestCase):
    def test_default_and_registry_mentions_are_not_applicable(self) -> None:
        result = classify_future_work_applicability(
            referenced_ids=["fw_reference_only"],
        )
        self.assertEqual("not_applicable", result.state)
        self.assertFalse(result.load_registry_context)
        self.assertFalse(result.load_completion_logic)
        self.assertFalse(result.regenerate_scorecard)
        self.assertFalse(result.mutate_registry)

        with self.assertRaises(ApplicabilityError):
            classify_future_work_applicability(
                registry_ids=["fw_bound_by_mistake"],
            )

    def test_linked_only_is_read_only(self) -> None:
        result = classify_future_work_applicability(
            "linked_only",
            registry_ids=["fw_linked"],
        )
        self.assertTrue(result.load_registry_context)
        self.assertFalse(result.load_completion_logic)
        self.assertFalse(result.regenerate_scorecard)
        self.assertFalse(result.mutate_registry)

    def test_completion_handoff_requires_exact_binding(self) -> None:
        result = classify_future_work_applicability(
            "completion_handoff",
            registry_ids=["fw_complete"],
            execution_status="completed",
            completion_state="ready_for_receipt",
            artifact_paths=["workbook.md"],
        )
        self.assertTrue(result.load_completion_logic)
        self.assertFalse(result.regenerate_scorecard)
        self.assertFalse(result.mutate_registry)

        with self.assertRaises(ApplicabilityError):
            classify_future_work_applicability(
                "completion_handoff",
                registry_ids=["fw_complete"],
                execution_status="completed",
                completion_state="ready_for_receipt",
            )

    def test_registry_sync_requires_verified_receipt(self) -> None:
        with self.assertRaises(ApplicabilityError):
            classify_future_work_applicability(
                "registry_sync",
                registry_ids=["fw_sync"],
                artifact_paths=["receipt.yaml"],
            )

        result = classify_future_work_applicability(
            "registry_sync",
            registry_ids=["fw_sync"],
            artifact_paths=["receipt.yaml"],
            verified_receipt=True,
        )
        self.assertTrue(result.load_completion_logic)
        self.assertTrue(result.regenerate_scorecard)
        self.assertTrue(result.mutate_registry)

    def test_linked_and_completion_states_require_single_explicit_id(self) -> None:
        with self.assertRaises(ApplicabilityError):
            classify_future_work_applicability("linked_only")
        with self.assertRaises(ApplicabilityError):
            classify_future_work_applicability(
                "registry_sync",
                registry_ids=["fw_a", "fw_b"],
                artifact_paths=["receipt.yaml"],
                verified_receipt=True,
            )


if __name__ == "__main__":
    unittest.main()
