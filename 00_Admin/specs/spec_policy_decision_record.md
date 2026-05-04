---
title: Policy Decision Record Spec
id: spec_policy_decision_record
module: admin
status: active
license: Apache-2.0
version: 1.0.1
created: 2026-04-23
updated: 2026-05-04
owner: ai_ops
ai_generated: true
related:
  - 00_Admin/specs/spec_async_approval_contract.md
  - 00_Admin/specs/spec_governance_lifecycle.md
  - 00_Admin/guides/ai_operations/guide_ai_operations_stack.md
  - AGENTS.md
---

<!-- markdownlint-disable MD013 MD025 MD041 -->
# Policy Decision Record Spec

## Quick Reference

- **What:** YAML block agents emit when evaluating a task against governance authority levels.
- **When:** At every L2+ authority evaluation before taking a consequential action.
- **Field:** `policy_decision:` in the agent's response or workbook evidence section.
- **Values:** `ALLOW` | `DENY` | `REQUIRE_APPROVAL` | `ALLOW_WITH_CONSTRAINTS`
- **Non-harness:** Agents produce PDRs; platforms decide how to surface them.
- See also: `spec_async_approval_contract.md` (REQUIRE_APPROVAL flow),
  `spec_governance_lifecycle.md` (circuit breaker triggers).

## Purpose

The Policy Decision Record (PDR) is the structured governance output agents emit when evaluating
whether a requested action is permitted under the current authority context. It formalizes the
implicit decision ai_ops authority levels have always required agents to make, producing a
machine-readable record that platforms (OpenClaw, Dispatch, Claude Code) can surface, log, and
act on.

Without a PDR, agents make governance decisions silently. With a PDR, every L2+ evaluation
produces an observable, auditable output.

## Scope

Applies to all agents operating under ai_ops governance in any mode (direct or governed).

## 1. Schema

```yaml
policy_decision:
  action_requested: "<brief description of the requested action>"
  authority_required: <0-4>         # minimum authority level for this action
  authority_held: <0-4>             # agent's current authority level in this context
  decision: ALLOW                   # ALLOW | DENY | REQUIRE_APPROVAL | ALLOW_WITH_CONSTRAINTS
  constraints: []                   # list of constraint strings; populated when decision = ALLOW_WITH_CONSTRAINTS
  rationale: "<one sentence>"       # why this decision was reached
  evidence_refs:
    - "<path#section or policy name>"  # at least one reference to ai_ops governance source
  emitted_at: "<ISO 8601 timestamp>"
  emitted_by: "<lane or agent ID>"
```

All fields are required. `constraints` MUST be populated when `decision: ALLOW_WITH_CONSTRAINTS`
and MAY be empty for all other decision values.

## 2. Decision Values

| Value | Meaning | When to use |
| --- | --- | --- |
| `ALLOW` | Action is within the agent's current authority | `authority_held` ≥ `authority_required` |
| `DENY` | Action is explicitly forbidden | Would violate a policy or boundary regardless of authority level |
| `REQUIRE_APPROVAL` | Action requires human approval before proceeding | `authority_held` < `authority_required` (L3/L4 gate) |
| `ALLOW_WITH_CONSTRAINTS` | Action is permitted under specific conditions | `authority_held` ≥ `authority_required` but scope must be narrowed |

## 3. Emission Conditions

Agents MUST emit a PDR when:

- Taking any action that requires L2 authority or higher (non-pre-authorized)
- A circuit breaker condition is triggered (see `spec_governance_lifecycle.md`)
- A task explicitly requests governance evaluation output

Agents SHOULD emit a PDR when:

- Starting a new workbook phase (pre-phase evaluation)
- Any uncertainty exists about whether an action is within scope

Agents MAY omit a PDR for:

- L0–L1 pre-authorized routine actions where no governance question arises

## 4. Platform Consumption Note

The PDR is an information contract. ai_ops defines the schema and emission conditions; platforms
decide how to act on the output:

- **Claude Code:** Agent writes PDR to the terminal or to the workbook's evidence section.
- **OpenClaw:** Gateway reads PDR from agent output; routes to human notification on `REQUIRE_APPROVAL`.
- **Dispatch/Managed Agents:** Session log captures PDR; harness may pause session on `REQUIRE_APPROVAL`.

ai_ops does not enforce PDR handling. The PDR is consumed as structured output — not a wire protocol.

**Recording scope:** Individual PDR emissions are workbook-level records — write them to the
terminal or workbook evidence section. The decision ledger (`00_Admin/decisions/decision_ledger.md`)
is reserved for cross-cutting governance decisions, not routine PDR emissions.

**Frontmatter alignment:** When emitting within a workbook, `authority_held` SHOULD match the
workbook's `authority_level` frontmatter, and `emitted_by` SHOULD match one of the
`activated_lanes`. The PDR carries these fields independently to remain a self-contained
record outside workbook context.

## 5. Examples

### 5.1 ALLOW

```yaml
policy_decision:
  action_requested: "Edit workbook Phase 1 status checkbox"
  authority_required: 1
  authority_held: 1
  decision: ALLOW
  constraints: []
  rationale: "L1 pre-authorized scope; workbook status update is explicitly permitted."
  evidence_refs:
    - AGENTS.md#authority-levels
  emitted_at: "2026-04-23T10:00:00-04:00"
  emitted_by: "Executor"
```

### 5.2 REQUIRE_APPROVAL

```yaml
policy_decision:
  action_requested: "Add new spec file to 00_Admin/specs/"
  authority_required: 4
  authority_held: 1
  decision: REQUIRE_APPROVAL
  constraints: []
  rationale: "New canonical spec requires L4 human approval per AGENTS.md authority gates."
  evidence_refs:
    - AGENTS.md#authority-levels
    - 00_Admin/policies/policy_authority_levels.md
  emitted_at: "2026-04-23T10:05:00-04:00"
  emitted_by: "Coordinator"
```

### 5.3 ALLOW_WITH_CONSTRAINTS

```yaml
policy_decision:
  action_requested: "Update guide_ai_operations_stack.md Thrift section"
  authority_required: 4
  authority_held: 4
  decision: ALLOW_WITH_CONSTRAINTS
  constraints:
    - "Additions only — no existing Thrift rules may be removed or weakened"
    - "Add pointer to spec_cost_governance.md; do not inline the schema"
  rationale: "L4 approval covers guide extension; additive-only constraint preserves existing canon."
  evidence_refs:
    - wb_platform_governance_uplift_01.md#phase-2-gate
  emitted_at: "2026-04-23T10:10:00-04:00"
  emitted_by: "Coordinator"
```

## 6. Change Log

- 1.0.1 (2026-05-04): §4 — added Recording scope note (workbook-level, not decision ledger) and Frontmatter alignment note (authority_held/emitted_by derivation guidance).
- 1.0.0 (2026-04-23): Initial spec authored per `wb_platform_governance_uplift_01` Phase 3.
