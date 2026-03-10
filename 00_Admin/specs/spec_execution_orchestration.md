---
title: Execution Orchestration Spec
id: spec_execution_orchestration
module: admin
status: active
license: Apache-2.0
version: 0.3.1
created: 2026-01-15
updated: 2026-03-04
owner: ai_ops
ai_generated: true
---

<!-- markdownlint-disable-next-line MD025 -->
# Execution Orchestration Spec

## 1. Purpose

Define the canonical lifecycle, triggers, and state tracking for workbook execution so AI agents can execute work
consistently without inference.

## 2. Scope

Applies to all workbooks executed in `90_Sandbox/ai_workbooks/` and any execution state files in module execution
folders (for example, `02_Modules/<module>/execution/`).

## 3. Workbook Lifecycle (Canonical)

Use two status axes to avoid vocabulary drift:

### 3.1 Artifact Status (metadata)

Artifact status uses repo-wide values:

- `planned`
- `stub`
- `active`
- `completed`
- `deprecated`

### 3.2 Execution Status (run state)

Execution status tracks runtime progress:

- `ready`
- `executing`
- `paused`
- `failed`
- `archived`

State transitions to `executing`, `failed`, or `archived` MUST include a
decision record with supporting evidence in execution log or state file.

## 4. Trigger Mechanisms

Workbooks execute via one of these triggers:

- **explicit**: requestor approval and execution workbook run
- **scheduled**: time-based runs (rare; must be documented)
- **event-driven**: triggered by upstream artifacts or outputs (must be documented)

Trigger type SHOULD be recorded in the execution log.

## 5. State Tracking

Execution state MUST be captured in an `execution_state.yaml` file that conforms to
`00_Admin/configs/validator/schema_execution_state.yaml` when state tracking is used.

If no execution state file exists, the workbook MUST capture `execution_status`
in its Execution Log section. Workbook frontmatter `status` remains artifact
status and should not be repurposed as run state.

Execution state file usage:

- Required for multi-phase or resumable workbooks.
- Required when a handoff spans multiple agents or sessions.
- Optional for single-session runs if the Execution Log is complete.

Execution state file location:

- Default: workbundle root as `execution_state.yaml`.
- Module execution runs: `02_Modules/<module>/execution/execution_state.yaml`.
- Program-level runs: program root as `execution_state.yaml`.

Execution state ownership:

- Executor updates phase, outputs, and blockers during execution.
- Validator updates final execution status after validation (archived/failed).
- Coordinator records transitions when multiple agents are involved.

## 6. Output and Handoff Protocol

On completion:

- Record outputs with paths and any contract references.
- Update execution status to `archived` (or `failed` with blockers).
- Provide a compacted context payload if a handoff is expected.

For CSCC execution lanes, handoff/context evidence MUST identify the active
context source path at each boundary:

- standalone workbook/runbook: workbook/runbook body compacted context section,
- bundled lanes: bundle README compacted context section,
- program lanes: program README compacted context section (with bundle override when delegated).

## 7. Validation Requirements

Before reporting completion:

- Run required validators and lint steps.
- Confirm registry updates when canonical artifacts are added or moved.
- Record validation commands in the execution log.

## 8. Validator Applicability Matrix

<!-- markdownlint-disable MD013 -->
| Artifact Type | Required Validators | Notes |
| --- | --- | --- |
| Workbook | `python 00_Admin/scripts/validate_repo_rules.py --config 00_Admin/configs/validator/validator_config.yaml` | Required for execution completion |
| Runbook | `python 00_Admin/scripts/validate_repo_rules.py --config 00_Admin/configs/validator/validator_config.yaml` | Required before reporting completion |
| Guide/Spec/Policy | `markdownlint <changed_paths>` | Required for governance updates |
| Canonical structure change | `00_Admin/scripts/generate_repo_structure.ps1` | Required when canonical files/dirs are added or removed |
<!-- markdownlint-enable MD013 -->

## 9. Related References

- Guide: `00_Admin/guides/ai_operations/guide_execution_orchestration.md`

## 10. Drift Recovery and Cleanup Reliability

Execution lanes that include cleanup actions MUST use lock-aware, non-silent
fallback behavior when move/delete operations fail.

Required sequence:

1. Attempt planned cleanup action within approved scope.
2. If blocked, classify blocker type:
   - `hard_lock`
   - `soft_lock`
   - `policy_block`
3. Attempt non-destructive archive-first fallback where allowed.
4. If fallback is also blocked, stop destructive actions and report explicit
   manual next actions.
5. Never silently skip unresolved cleanup items.

Minimum evidence when blocked:

- blocker type
- blocked path(s)
- fallback attempted
- remaining manual action

## 11. Operational Reliability Validation Scenarios

These scenarios validate post-bootstrap execution reliability and SHOULD be
applied in completion crosschecks for cleanup/contract-heavy lanes.

### ORS-01: Output Contract Presence Validation

Expected checks:

- contract-required artifacts exist,
- required fields/order/schema constraints are validated,
- pass/fail includes explicit file-level evidence.

### ORS-02: Lock-Aware Cleanup Fallback Validation

Expected checks:

- blocker type is explicitly classified,
- archive-first fallback is attempted when policy allows,
- unresolved blockers include explicit manual follow-up.
