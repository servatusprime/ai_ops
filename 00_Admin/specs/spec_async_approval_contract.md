---
title: Async Approval Contract Spec
id: spec_async_approval_contract
module: admin
status: active
license: Apache-2.0
version: 1.0.1
created: 2026-04-23
updated: 2026-05-05
owner: ai_ops
ai_generated: true
spec_archetype: output_contract_spec
related:
  - 00_Admin/specs/spec_policy_decision_record.md
  - 00_Admin/specs/spec_governance_lifecycle.md
  - AGENTS.md
---

<!-- markdownlint-disable MD013 MD025 MD041 -->
# Async Approval Contract Spec

## Quick Reference

- **What:** Defines how agents park at L3/L4 gates when the operator is asynchronous.
- **Action:** `PARK` - save state, move to other work, resume when approval arrives.
- **Field:** `approval_contract:` in agent output or workbook gate section.
- **Context snapshot:** Required - must enable any agent to resume cold from saved state.
- **Non-harness:** ai_ops defines the schema; platforms handle the delivery channel.
- See also: `spec_policy_decision_record.md` (REQUIRE_APPROVAL decision that triggers this contract),
  CSCC resumability principle in `AGENTS.md`.

## Purpose

The Async Approval Contract fills the gap between authority level gates ("require human approval
at L3/L4") and the operational reality of async operators (mobile, away from terminal). It defines
the PARK action and the information an agent must save to enable seamless resume when approval
arrives. The design is aligned with the CSCC (Cold-Start Context Constrained) resumability
principle already in ai_ops: context snapshots that enable any agent to resume a parked task.

Without this contract, agents at an L3/L4 gate either block indefinitely or proceed without
approval. With it, agents park cleanly and resume deterministically.

## Scope

Applies to any agent that encounters an L3 or L4 authority gate during an active session where
the operator is not synchronously present.

## 1. Schema

```yaml
approval_contract:
  request_id: "<workbook-id or task-id>"
  requested_by: "<lane or agent ID>"
  requested_at: "<ISO 8601 timestamp>"
  authority_level: <3 or 4>
  scope_summary: "<one sentence - what is being requested and why>"
  channel: "<dispatch | openclaw_telegram | openclaw_slack | claude_code>"
  timeout_hours: <integer>
  timeout_action: PARK              # PARK | ESCALATE | DENY
  approval_state: PENDING           # PENDING | APPROVED | DENIED | TIMED_OUT
  context_snapshot_path: "<relative path to CSCC context artifact>"
  approved_by: null                 # filled on approval
  approved_at: null                 # ISO 8601; filled on approval
```

`context_snapshot_path` is REQUIRED. It MUST point to an artifact that gives a cold-start agent
full context to resume the parked task without additional information.

## 2. PARK Action

`PARK` is the default `timeout_action` and SHOULD be used unless the workbook specifies otherwise. When an agent PARKs:

1. It records the `approval_contract:` block in the active workbook gate section.
2. It saves current state as a CSCC-compliant context artifact at `context_snapshot_path`.
3. It emits a `REQUIRE_APPROVAL` PDR (see `spec_policy_decision_record.md`).
4. It moves to other independent work if available, or halts gracefully.
5. On approval: any agent reads the snapshot and resumes from the exact park point.

`PARK` is preferred over `DENY` because it preserves the approved scope and queued work.
It is preferred over `ESCALATE` unless an explicit escalation path has been defined in the
governance context.

## 3. CSCC Linkage

The context snapshot at `context_snapshot_path` MUST be CSCC-compliant:

- A cold-start agent reading only the snapshot and the referenced workbook MUST be able to resume.
- The snapshot MUST include: current phase, task in progress, files modified, open decisions,
  and the `approval_contract:` reference.
- The snapshot SHOULD be a Markdown document, not a tool state dump or binary artifact.
- For most workbook-based tasks, the workbook itself (with completed checkboxes and execution notes)
  satisfies this requirement when it accurately reflects current state.

## 4. Channel Types

| Channel | Description |
| --- | --- |
| `dispatch` | Anthropic Dispatch mobile notification |
| `openclaw_telegram` | OpenClaw Telegram message via channel layer |
| `openclaw_slack` | OpenClaw Slack message via channel layer |
| `claude_code` | Direct Claude Code terminal prompt or graceful halt |

The `channel` field is informational; ai_ops does not send messages. The platform reads the
`approval_contract:` output and dispatches notification via its own channel layer.

## 5. Timeout Policy

If `timeout_hours` elapses without a state change from `PENDING`:

| `timeout_action` | Outcome |
| --- | --- |
| `PARK` | Agent saves state and halts. `approval_state` becomes `TIMED_OUT`. Work remains queued for future resume. |
| `ESCALATE` | Platform notifies a secondary approver. Platform-specific implementation required. |
| `DENY` | Contract treated as denied. Agent MUST NOT proceed with the parked task. |

**Default:** `PARK` with `timeout_hours: 24` unless the workbook specifies otherwise.

## 6. Examples

### 6.1 Active L4 Gate - Awaiting Approval

```yaml
approval_contract:
  request_id: "wb_example_governance_change_01-phase2"
  requested_by: "Coordinator"
  requested_at: "2026-04-23T09:00:00-04:00"
  authority_level: 4
  scope_summary: "L4 approval to author new governance specs for G-1 through G-4"
  channel: "claude_code"
  timeout_hours: 48
  timeout_action: PARK
  approval_state: PENDING
  context_snapshot_path: "90_Sandbox/ai_workbooks/<active_workbook_packet>/<active_workbook>.md"
  approved_by: null
  approved_at: null
```

### 6.2 Approved Contract

```yaml
approval_contract:
  request_id: "wb_example_governance_change_01-phase2"
  requested_by: "Coordinator"
  requested_at: "2026-04-23T09:00:00-04:00"
  authority_level: 4
  scope_summary: "L4 approval to author new governance specs for G-1 through G-4"
  channel: "claude_code"
  timeout_hours: 48
  timeout_action: PARK
  approval_state: APPROVED
  context_snapshot_path: "90_Sandbox/ai_workbooks/<active_workbook_packet>/<active_workbook>.md"
  approved_by: "servatusprime"
  approved_at: "2026-04-23T12:00:00-04:00"
```

## 7. Change Log

- 1.0.1 (2026-05-04): Section 2 - replaced "recommended" with SHOULD per spec language standard (`00_Admin/specs/README.md#spec-characteristics`).
- 1.0.0 (2026-04-23): Initial spec authored per `wb_platform_governance_uplift_01` Phase 4.
