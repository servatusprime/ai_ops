#!/usr/bin/env python3
"""Classify whether closeout may enter future-work registry logic.

The classifier is intentionally side-effect free.  A registry mention does not
activate completion behavior; callers must provide an explicit applicability
state and satisfy the state-specific contract before loading completion logic,
regenerating a scorecard, or mutating a registry.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Any, Iterable

NOT_APPLICABLE = "not_applicable"
LINKED_ONLY = "linked_only"
COMPLETION_HANDOFF = "completion_handoff"
REGISTRY_SYNC = "registry_sync"
APPLICABILITY_STATES = (
    NOT_APPLICABLE,
    LINKED_ONLY,
    COMPLETION_HANDOFF,
    REGISTRY_SYNC,
)


class ApplicabilityError(ValueError):
    """The requested applicability state is not sufficiently bound."""


def _normalized(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted({str(value).strip() for value in values if str(value).strip()}))


@dataclass(frozen=True)
class FutureWorkApplicability:
    """Machine-readable closeout behavior selected by an explicit contract."""

    state: str
    registry_ids: tuple[str, ...]
    referenced_ids: tuple[str, ...]
    load_registry_context: bool
    load_completion_logic: bool
    regenerate_scorecard: bool
    mutate_registry: bool
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "future_work": self.state,
            "registry_ids": list(self.registry_ids),
            "referenced_ids": list(self.referenced_ids),
            "load_registry_context": self.load_registry_context,
            "load_completion_logic": self.load_completion_logic,
            "regenerate_scorecard": self.regenerate_scorecard,
            "mutate_registry": self.mutate_registry,
            "reason": self.reason,
        }


def classify_future_work_applicability(
    intent: str = NOT_APPLICABLE,
    *,
    registry_ids: Iterable[str] = (),
    referenced_ids: Iterable[str] = (),
    execution_status: str | None = None,
    completion_state: str | None = None,
    artifact_paths: Iterable[str] = (),
    verified_receipt: bool = False,
) -> FutureWorkApplicability:
    """Validate one explicit future-work applicability state.

    ``referenced_ids`` are evidence for reporting only.  They never promote the
    default ``not_applicable`` state.  Completion and registry mutation require
    one exact registry ID and a non-empty artifact set.
    """

    if intent not in APPLICABILITY_STATES:
        raise ApplicabilityError(f"unsupported future-work applicability: {intent}")

    ids = _normalized(registry_ids)
    references = _normalized(referenced_ids)
    artifacts = _normalized(artifact_paths)

    if intent == NOT_APPLICABLE:
        if ids or execution_status or completion_state or artifacts or verified_receipt:
            raise ApplicabilityError(
                "not_applicable cannot carry a registry or completion binding; "
                "use linked_only for explicit dependency context"
            )
        return FutureWorkApplicability(
            state=intent,
            registry_ids=(),
            referenced_ids=references,
            load_registry_context=False,
            load_completion_logic=False,
            regenerate_scorecard=False,
            mutate_registry=False,
            reason="ordinary scoped closeout has no registry completion transaction",
        )

    if intent == LINKED_ONLY:
        if not ids:
            raise ApplicabilityError("linked_only requires at least one referenced registry ID")
        if execution_status or completion_state or artifacts or verified_receipt:
            raise ApplicabilityError("linked_only cannot carry completion or receipt bindings")
        return FutureWorkApplicability(
            state=intent,
            registry_ids=ids,
            referenced_ids=references,
            load_registry_context=True,
            load_completion_logic=False,
            regenerate_scorecard=False,
            mutate_registry=False,
            reason="read dependency context only; no completion or registry mutation",
        )

    if len(ids) != 1:
        raise ApplicabilityError(f"{intent} requires exactly one registry ID")
    if not artifacts:
        raise ApplicabilityError(f"{intent} requires a non-empty artifact set")

    if intent == COMPLETION_HANDOFF:
        if execution_status != "completed" or completion_state != "ready_for_receipt":
            raise ApplicabilityError(
                "completion_handoff requires execution_status=completed and "
                "completion_state=ready_for_receipt"
            )
        if verified_receipt:
            raise ApplicabilityError("completion_handoff must precede receipt verification")
        return FutureWorkApplicability(
            state=intent,
            registry_ids=ids,
            referenced_ids=references,
            load_registry_context=True,
            load_completion_logic=True,
            regenerate_scorecard=False,
            mutate_registry=False,
            reason="implementation is complete and bound for receipt handoff",
        )

    if not verified_receipt:
        raise ApplicabilityError("registry_sync requires a verified success receipt")
    return FutureWorkApplicability(
        state=intent,
        registry_ids=ids,
        referenced_ids=references,
        load_registry_context=True,
        load_completion_logic=True,
        regenerate_scorecard=True,
        mutate_registry=True,
        reason="verified receipt exists; run the exact registry/scorecard sync transaction",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--intent", choices=APPLICABILITY_STATES, default=NOT_APPLICABLE)
    parser.add_argument("--registry-id", action="append", default=[])
    parser.add_argument("--referenced-id", action="append", default=[])
    parser.add_argument("--execution-status")
    parser.add_argument("--completion-state")
    parser.add_argument("--artifact-path", action="append", default=[])
    parser.add_argument("--verified-receipt", action="store_true")
    args = parser.parse_args()
    try:
        result = classify_future_work_applicability(
            args.intent,
            registry_ids=args.registry_id,
            referenced_ids=args.referenced_id,
            execution_status=args.execution_status,
            completion_state=args.completion_state,
            artifact_paths=args.artifact_path,
            verified_receipt=args.verified_receipt,
        )
    except ApplicabilityError as exc:
        print(f"closeout-applicability: {exc}")
        return 2
    print(json.dumps(result.as_dict(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
