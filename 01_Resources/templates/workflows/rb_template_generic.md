---
title: Runbook: <task_title>
id: rb_<topic>_<scope>
version: 0.3.2
status: active
license: Apache-2.0
last_updated: 2026-03-19
owner: ai_ops
ai_role: executor
model_profile: "<model_a>:<reasoning_level> | <model_b>:<reasoning_level>"
# model_profile guidance: select tier based on task complexity:
#   low (haiku-class)   -- research, read-only, bounded repeatable steps
#   medium (sonnet-class) -- implementation, file writes, moderate coordination
#   high (opus-class)   -- architectural decisions, multi-surface governance changes
execution_mode: sequential
execution_topology: single_agent
activated_lanes:
  - Coordinator
  - Executor
  - Reviewer
delegation_policy: explicit_only
convergence_profile: iterative_convergence_minimal
parallel_coordination_id: null  # Set only when sibling active artifacts must coordinate early
depends_on: []
shared_files: []
lock_scope: none
description: >
  Reusable runbook template for repeatable execution procedures.
related:
  - 00_Admin/guides/authoring/guide_runbooks.md
  - 00_Admin/specs/spec_runbook_structure.md
cost_governance:  # Work-family: MAY self-impose limits. Run-family: SHOULD populate. null = thrift judgment. See spec_cost_governance.md.
  session_token_budget: null
  workpacket_token_budget: null
  model_routing:
    planning: null
    execution: null
    review: null
  alert_threshold_pct: 80
  exceeded_action: PARK
---

<!-- markdownlint-disable MD013 MD033 -->
<!-- markdownlint-disable-next-line MD025 -->
# Runbook: <task_title>

## Purpose

- State the reusable objective in 1-3 bullets.

---

## Phases

**At-a-glance phase reference.** Per-run status tracked in Execution Log below.

- Ph 0: Cold-Start and Pre-flight
- Ph 1: Execution
- Ph 2: Verification
- Ph 3: Selfcheck / Crosscheck

---

## Approvals and Decisions

**Resolve all open items before first use. These are publication-time decisions, not per-run.**

### Pre-Authorized

- Runbook scope: [echo the scope in one sentence] -- authorized by requestor [date]

### Open Items (resolve before publication)

- [Open question or decision needing requestor input before this runbook is published for use]

<!-- If none, write: "- None -- all scope confirmed before publication" -->

### Locked Design Decisions

<!-- Record any design choices locked before publication. -->

- **[Decision label]:** [Decision and rationale]

---

## Execution Topology Contract

Use this near-top section to declare the authoritative execution/delegation
contract for the runbook.

```yaml
execution_topology_contract:
  lead_lane: Coordinator
  task_brief: "<one-line mission for the lead lane>"
  spawn_criteria:
    - "<when delegation is justified>"
  do_not_delegate_when:
    - "<when the lead retains the work>"
  required_context_pack:
    must_read:
      - "<artifact>"
  permission_envelope:
    delegated_default: "<read-only findings support|...>"
    lead_agent: "<final integration and authority-surface writes>"
  lane_return_contracts:
    Reviewer: "<expected return shape>"
```

Rules:

- Keep the full contract in the runbook. Spines and pipelines should carry only
  coordination summaries and references to child execution artifacts.
- For strictly single-agent runs, keep the block minimal but still declare the
  lead lane and stop conditions.
- Use delegated workers only for bounded sidecar tasks where delegation is
  actually efficient.

---

## Ordered Execution Queue

<!-- Delegation-intent rule (conditional):
For delegated or specialized run steps, use
`**[Agent: <canonical_lane> | <model_tier>]**` instead of a bare `**[Agent]**`
marker and add an indented `Delegation Brief:` line under the step.
Keep the lane surface-agnostic but canonical (for example `Researcher`,
`Planner`, `Executor`, `Reviewer`, `Linter`, `Closer`) and avoid
provider-specific runtime labels in canonical runbooks.
See `00_Admin/guides/authoring/guide_workbooks.md` section
`Delegation Intent Markers (conditional)` for full rules. -->

### Phase 0: Cold-Start and Pre-flight (Agent -- Level 0)

- 0.1 Verify model profile meets authority level declared in frontmatter **[Agent]**
- 0.2 Read this runbook fully **[Agent]**
- 0.3 Read runbundle README (or execution spine if present) **[Agent]**
- 0.4 Confirm all preconditions pass **[Agent]**
- 0.5 **Ambiguity Stop Gate** -- if any instruction is unclear, stop and ask requestor;
  do not proceed **[Agent/Requestor]**

**-> Ph 0 complete when:** All readiness checks passed; no ambiguity flagged.

### Phase 1: Execution (Agent)

- 1.1 <execution step 1> **[Agent]**
- 1.2 <execution step 2> **[Agent]**
- 1.3 <execution step 3> **[Agent]**

<!-- Example delegated step:
- 1.4 Map current state **[Agent: Researcher | medium]**
     Delegation Brief: Return findings only and do not modify files during the read pass.
-->

**-> Ph 1 complete when:** All steps executed or blocked with evidence.

### Phase 2: Verification (Agent)

- 2.1 Run validation commands **[Agent]**
- 2.2 Confirm postconditions are met **[Agent]**
- 2.3 Record findings in Verification Checklist **[Agent]**

**-> Ph 2 complete when:** All validation commands pass; postconditions confirmed.

### Phase 3: Selfcheck

- 3.1 Run selfcheck loop per AGENTS.md standard (max 3 iterations) **[Agent]**
- 3.2 Record evidence in Selfcheck Results section **[Agent]**

---

## Scope and Authority

- In-scope:
- Out-of-scope:
- Approval gates:

---

## Inputs

- Files, systems, and parameters required to run.

---

## Preconditions

- What must be true before execution begins.

---

## Planning Outputs

### Assumptions

- <assumption>

### Risks and Mitigations

- Risk: <risk>. Mitigation: <mitigation>.

### Success Criteria

- <success criterion>

---

## Steps

1. First execution step.
1. Second execution step.
1. Third execution step.

---

## Validation Commands

```powershell
# Example: path checks
Test-Path "00_Admin/runbooks/rb_example.md"

# Example: repo validator
python 00_Admin/scripts/validate_repo_rules.py --config 00_Admin/configs/validator/validator_config.yaml
```

---

## Outputs

- Files or systems updated/created by this run.

---

## Postconditions

- What must be true after successful execution.

---

## Verification Checklist

- Preconditions satisfied
- Steps executed in order
- Validation commands executed
- Outputs created/updated
- Postconditions met

---

## Execution Log

Per-run evidence. Add a row for each execution.

| Run | Date | Executor | Outcome | Notes |
| --- | --- | --- | --- | --- |
| 1 | YYYY-MM-DD | `<model or human>` | pass / fail / blocked | `<key output or path:line>` |

---

## Selfcheck Results

Evidence schema: each entry requires **path:line** or **command + key output** --
narrative-only evidence is not acceptable.

| Run | Iteration | Check | Status | Evidence | Environment |
| --- | --- | --- | --- | --- | --- |
| 1 | 1 | End-to-end task verification | pending | `<path:line or command:key_output>` | `<env_name>` |

---

## Crosscheck Stop Marker

Crosscheck is a publication gate and a post-significant-change gate -- not required
on every execution. Record crosscheck results below.

| Date | Trigger | Scope | Outcome | Findings |
| --- | --- | --- | --- | --- |
| YYYY-MM-DD | initial publication / change: <summary> | this runbook | pass / findings | <summary or none> |
