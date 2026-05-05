---
title: Cost Governance Spec
id: spec_cost_governance
module: admin
status: active
license: Apache-2.0
version: 1.0.2
created: 2026-04-23
updated: 2026-05-05
owner: ai_ops
ai_generated: true
spec_archetype: output_contract_spec
related:
  - 00_Admin/guides/ai_operations/guide_ai_operations_stack.md
  - 00_Admin/specs/spec_governance_lifecycle.md
  - 00_Admin/specs/spec_policy_decision_record.md
  - AGENTS.md
---

<!-- markdownlint-disable MD013 MD025 MD041 -->
# Cost Governance Spec

## Quick Reference

- **What:** Quantitative cost governance schema - extends the Thrift quality axis with opt-in budgets.
- **Field:** `cost_governance:` optional frontmatter in workbooks and other execution artifacts.
- **Default:** All values `null` - cost governance is opt-in; absence means thrift judgment applies.
- **Non-harness:** Agents *read* this block and self-govern; ai_ops does not enforce budgets.
- **Budget exceeded:** Triggers circuit breaker PARK (see `spec_governance_lifecycle.md` Section 2.1).
- See also: `guide_ai_operations_stack.md` Thrift axis (normative interpretation),
  `spec_governance_lifecycle.md` (budget circuit breaker).

## Purpose

Extends the Thrift quality axis with quantitative cost governance levers: token budgets,
model routing preferences, and alert thresholds. The Thrift axis defines efficiency as
the qualitative goal; this spec defines the optional machine-readable contract agents use
to self-govern their cost footprint.

This is governance-as-documentation - agents read the `cost_governance:` block and apply it.
Platforms may choose to enforce it externally, but ai_ops imposes no enforcement infrastructure.

## Scope

The `cost_governance:` field is applicable to all 8 execution artifact types: workbook, runbook,
execution spine, pipeline, workbundle, runbundle, workprogram, and runprogram. It is always
optional. Absence means all values are effectively `null` - agents apply thrift judgment
without a hard budget constraint.

## 1. Schema

```yaml
cost_governance:
  session_token_budget: null        # max input+output tokens per session; null = unset
  workpacket_token_budget: null     # max tokens per workpacket (one workbook phase or runbook run)
  model_routing:
    planning: null                  # model ID for Coordinator/Planner lanes; null = agent default
    execution: null                 # model ID for Executor/Builder lanes; null = agent default
    review: null                    # model ID for Reviewer/crosscheck lanes; null = agent default
  alert_threshold_pct: 80           # emit budget-warning PDR at this % of any active budget
  exceeded_action: PARK             # PARK | DOWNGRADE_MODEL | ABORT
```

## 2. Field Definitions

### 2.1 `session_token_budget`

Maximum total input + output tokens for the entire session. Applies from session start.
When reached, the agent MUST trigger the budget circuit breaker (`spec_governance_lifecycle.md` Section 2.1).

`null` = unset. Agents apply thrift judgment without a hard session limit.

### 2.2 `workpacket_token_budget`

Maximum tokens for a single workpacket (one workbook phase, one runbook execution, or one
pipeline stage). Resets at the boundary of each workpacket.

`null` = unset. If `session_token_budget` is also set, both limits apply independently.

### 2.3 `model_routing`

Governance *preference* (not runtime enforcement) for which model tier to use per lane class:

- `planning`: Coordinator and Planner lanes - typically lower-cost reasoning
- `execution`: Executor and Builder lanes - implementation tasks
- `review`: Reviewer and crosscheck lanes - highest judgment requirement

`null` = use the agent's default model for that lane. This does not override platform-level
model assignment; it is a preference the agent may honor when it has model-selection capability.

### 2.4 `alert_threshold_pct`

When any active budget reaches this percentage of its limit, the agent MUST emit an
`ALLOW_WITH_CONSTRAINTS` PDR as a budget-warning signal before continuing. Default: 80.

This provides an early warning before the hard `exceeded_action` triggers.

### 2.5 `exceeded_action`

Action taken when a budget limit is reached:

| Value | Behavior |
| --- | --- |
| `PARK` | Emit DENY PDR, save context snapshot, halt. Resume when human authorizes continuation. **Default.** |
| `DOWNGRADE_MODEL` | Switch to a lower-cost model for the current lane if available. Continue with downgraded tier. |
| `ABORT` | Emit DENY PDR, halt immediately. Do not save resume state. |

`PARK` SHOULD be the `exceeded_action` for most workbook-driven sessions. `ABORT` is appropriate only for
non-resumable operations where partial completion is worse than none.

## 3. Usage Examples

### 3.1 Minimal: Budget-Constrained Workbook

```yaml
cost_governance:
  session_token_budget: 500000
  workpacket_token_budget: 100000
  model_routing:
    planning: null
    execution: null
    review: null
  alert_threshold_pct: 80
  exceeded_action: PARK
```

### 3.2 Model-Routing Only (No Hard Budget)

```yaml
cost_governance:
  session_token_budget: null
  workpacket_token_budget: null
  model_routing:
    planning: "claude-haiku-4-5-20251001"
    execution: "claude-sonnet-4-6"
    review: "claude-opus-4-7"
  alert_threshold_pct: 80
  exceeded_action: PARK
```

### 3.3 Thrift Judgment Only (No Token Budget)

Omit the `cost_governance:` block entirely, or include it with token budgets unset.
`alert_threshold_pct` and `exceeded_action` retain defaults even when budgets are
unset - they have no effect when no budget is active.

```yaml
cost_governance:
  session_token_budget: null
  workpacket_token_budget: null
  model_routing:
    planning: null
    execution: null
    review: null
  alert_threshold_pct: 80
  exceeded_action: PARK
```

Agents apply the Thrift quality axis qualitatively. No circuit breaker budget trigger applies.

## 4. Change Log

- 1.0.2 (2026-05-04): Section 2.5 - replaced "recommended" with SHOULD per spec language standard.
- 1.0.1 (2026-04-23): Section 3.3 title clarified to "Thrift Judgment Only (No Token Budget)" with explanatory note (patch per crosscheck finding).
- 1.0.0 (2026-04-23): Initial spec authored per `wb_platform_governance_uplift_01` Phase 6.
