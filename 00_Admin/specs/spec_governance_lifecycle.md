---
title: Governance Lifecycle Spec
id: spec_governance_lifecycle
module: admin
status: active
license: Apache-2.0
version: 1.0.2
created: 2026-04-23
updated: 2026-05-05
owner: ai_ops
ai_generated: true
spec_archetype: governance_spec
related:
  - 00_Admin/specs/spec_policy_decision_record.md
  - 00_Admin/specs/spec_async_approval_contract.md
  - 00_Admin/specs/spec_cost_governance.md
  - 00_Admin/specs/spec_work_mode_direct.md
  - 00_Admin/specs/spec_work_mode_governed.md
  - AGENTS.md
---

<!-- markdownlint-disable MD013 MD025 MD041 -->
# Governance Lifecycle Spec

## Quick Reference

- **What:** Maps ai_ops governance mechanisms to three lifecycle stages: Before, During, Across.
- **Circuit breaker:** Self-interrupt conditions agents MUST honor during unattended execution.
- **Trigger output:** Circuit breaker conditions emit a PDR (`spec_policy_decision_record.md`).
- **Non-harness:** These are governance *definitions* - conditions and signals, not runtime monitors.
- See also: `spec_policy_decision_record.md`, `spec_async_approval_contract.md`,
  `spec_cost_governance.md` (`session_token_budget` feeds the budget circuit breaker).

## Purpose

Defines the three lifecycle stages at which ai_ops governance is active, maps each stage to
its governing mechanisms, and specifies the circuit breaker conditions under which an agent
MUST self-interrupt. Circuit breakers are the most significant governance gap for unattended
execution - they define the conditions under which an agent aborts and parks rather than
continuing when governance integrity degrades.

## Scope

Applies to all agents in any execution mode. Circuit breaker conditions are mandatory for
unattended execution (Dispatch, OpenClaw) and SHOULD be honored in all Claude Code sessions.

## 1. Governance Lifecycle Map

The three stages and their ai_ops mechanisms. Governance signals are what ai_ops emits;
platform-specific implementation of those signals is out of scope for this spec.

| Stage | ai_ops Mechanism | Governance Signal |
| --- | --- | --- |
| **Before** | Workbook approval gate, authority level evaluation, PDR emission | Pre-acceptance validation point - agent confirms authorization before starting |
| **During** | Lane authority boundaries, L1 pre-authorized scope, scratchpad logging | Per-step authority enforcement - agent checks scope before each consequential action |
| **During (circuit breaker)** | Circuit breaker conditions (Section 2 below) | Session abort / PARK signal - agent self-interrupts when conditions degrade |
| **Across** | Crosscheck reviews, workbook run logs, harvest reports | Session state persistence, audit surface - record of what was decided and done |

## 2. Circuit Breaker Conditions

An agent MUST self-interrupt (PARK) and emit a PDR when any of the following conditions are met:

### 2.1 Token Budget Exceeded

- **Trigger:** Session or workpacket token consumption exceeds the budget defined in
  `cost_governance.session_token_budget` or `cost_governance.workpacket_token_budget`
  (see `spec_cost_governance.md`). If no budget is set, this condition does not apply.
- **Action:** PARK with `decision: DENY`, rationale "Token budget exceeded."
- **Note:** At `alert_threshold_pct` of budget (default 80%), emit a `ALLOW_WITH_CONSTRAINTS` PDR
  as a budget warning before the hard stop.

### 2.2 Scope Creep Detected

- **Trigger:** A required action touches files, paths, or repositories not declared in the
  active workbook's scope section.
- **Action:** PARK with `decision: REQUIRE_APPROVAL`, rationale "Scope expansion requires approval."
- **Note:** Minor file touches (e.g., updating an index that includes a new spec) are not
  scope creep if the spec creation was within scope.

### 2.3 Authority Escalation Required

- **Trigger:** An action requires higher authority than the agent currently holds in context.
  This is distinct from a pre-declared gate - this is an unexpected escalation mid-execution.
- **Action:** Emit `REQUIRE_APPROVAL` PDR and PARK. Do not proceed.
- **Note:** Pre-declared gates (Phase 2 gate) are handled by the workbook gate pattern, not here.

### 2.4 Stale Context

- **Trigger:** Context compaction has occurred mid-session and the agent cannot confirm its
  current state against the workbook's Execution Notes or Status Checklist.
- **Action:** PARK. Emit PDR with `decision: REQUIRE_APPROVAL`, rationale "Stale context -
  context refresh required before resuming." Request context refresh from the active workbook
  before resuming.
- **Note:** After compaction, re-read the workbook start-to-finish before continuing.

### 2.5 Consecutive Tool Failures

- **Trigger:** Three or more consecutive tool errors on the same task without a successful
  intermediate step.
- **Action:** PARK with `decision: DENY`, rationale "Repeated tool failures - requires investigation."
- **Note:** A different task succeeding does not reset the counter. The counter resets on a
  successful tool call within the same task.

## 3. Circuit Breaker PDR Template

When any circuit breaker fires, the agent emits a PDR referencing this spec:

```yaml
policy_decision:
  action_requested: "<what the agent was attempting>"
  authority_required: <N>
  authority_held: <N>
  decision: REQUIRE_APPROVAL   # or DENY depending on condition
  constraints: []
  rationale: "<circuit breaker condition name>: <one sentence>"
  evidence_refs:
    - 00_Admin/specs/spec_governance_lifecycle.md#2-circuit-breaker-conditions
  emitted_at: "<ISO 8601>"
  emitted_by: "<lane>"
```

## 4. Platform Integration Notes

These notes describe governance intent - platform-specific implementation belongs in
downstream platform docs:

- **Before stage:** Platform should provide a pre-session validation surface where the
  workbook approval state is confirmed before execution begins.
- **During stage:** Platform's per-step authority check surface should be able to receive
  PDR output from the agent and route `REQUIRE_APPROVAL` decisions to the operator.
- **Circuit breaker:** Platform should honor the PARK signal and preserve session state.
  The `context_snapshot_path` in the accompanying `approval_contract:` identifies where
  state was saved.
- **Across stage:** Platform should persist session artifacts (workbook, run log) for
  post-execution audit via crosscheck review.

## 5. Change Log

- 1.0.2 (2026-05-04): Section Scope - replaced "strongly recommended" with SHOULD per spec language standard.
- 1.0.1 (2026-04-23): Section 2.4 Stale Context - added explicit PDR emission step (patch per crosscheck finding).
- 1.0.0 (2026-04-23): Initial spec authored per `wb_platform_governance_uplift_01` Phase 5.
