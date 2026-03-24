---
description: Summarize active work context and blockers.
name: work_status
kind: workflow
version: 0.1.1
status: active
owner: ai_ops
license: Apache-2.0
claude:
  argument-hint: null
  disable-model-invocation: false
  user-invocable: true
  allowed-tools: null
  model: null
  context: null
  agent: null
codex:
  metadata:
    short-description: Summarize active work context and blockers.
  interface:
    display_name: work_status
    short_description: Summarize active work context and blockers.
  policy:
    allow_implicit_invocation: true
exports:
  claude_plugin:
    enabled: true
    skill_name: work_status
  codex:
    enabled: true
    skill_name: work_status
  claude_project:
    enabled: true
    skill_name: work_status
---

<!-- markdownlint-disable MD013 -->
# /work_status

## Purpose

Summarize active work context and blockers.

## Inputs and Preconditions

- None required; if no work context exists, ask to set it up.
- If inputs are insufficient or the request is illogical, pause and ask for clarification.

## Context Routing Hook

Use `00_Admin/configs/context_routing.yaml` as the canonical onboarding
contract.

1. Apply `commands._defaults.guard_profile` and
   `commands.work_status.guard_profile`.
2. Resolve onboarding tier in order: `fresh_bootstrap`,
   `resume_same_scope`, `recenter` (fallback `fresh_bootstrap` when state is
   unknown).
3. Load `always_read`; expand `read_on_demand` only when needed.
4. Emit status metadata: `bootstrap_path`, `resume_basis`, and `reads_applied`.
5. Do not execute edits from `/work_status`; transition to `/work` for any
   requested changes.

## Decision Matrix (Cold-Start)

### Decision Matrix - Inside (Maintainer)

- No active artifacts: provide empty status and suggest `/work` to begin.
- Multiple active artifacts: list them and ask which to summarize in detail.
  - **Default**: Summarize **All Active** artifacts in a consolidated list.
- Active workbundle/workprogram/workbook/runbundle/runprogram/runbook: summarize active context.

### Decision Matrix - External (User)

- No active artifacts: offer to set up work tracking and suggest `/work`.
- Multiple active artifacts: list them and ask which to summarize in detail.
- Active user artifacts: summarize their current context.

## Steps

### Inside Repo (Maintainer)

1. Apply bootstrap guard BRG-01: if bootstrap requirements are missing or
   unverifiable, apply `fresh_bootstrap` tier (read `AGENTS.md`) before lane
   steps.
2. If routing resolved `resume_same_scope`, keep current target scope and skip
   bootstrap rereads.
3. Read `.ai_ops/local/work_state.yaml` for active artifact context (absence =
   no active work; not an error).
4. Show work/run program/workbundle/bundle context with current status.
5. List blockers and dependencies.
6. Suggest next steps based on active work context.
7. Point to the selected artifact README or execution spine.
8. Add a concise "Cross-Session Recap" block:
   - recent commits since last known work checkpoint (if available)
   - artifact status changes
   - newly surfaced blockers

### External Repo (User)

1. Apply bootstrap guard BRG-01 before lane steps.
2. If routing resolved `resume_same_scope`, continue without bootstrap rereads.
3. Show user's work context if tracked (workbooks, active tasks).
4. If no work context exists, offer to set up work tracking.
5. List any blockers or notes from previous sessions.
6. Add a concise "Cross-Session Recap" block when prior context exists.

## Status Output Blocks (Required)

Include these blocks in status responses when context exists:

1. **Active Context Summary**
   - target repo
   - active artifacts
   - current phase/task (if known)
2. **Cross-Session Recap**
   - what changed since last checkpoint
3. **Authority Trail Snapshot**
   - most recent authority classification and rationale (if recorded)
4. **Next Step**
   - one suggested next action with pointer to owning artifact

If authority trail data is missing, note that explicitly and point to
`/work` selfcheck requirements for evidence capture.

## Outputs

- Status summary with blockers and suggested next steps.

## Resources

- `.ai_ops/local/work_state.yaml` (active work context — machine-local, gitignored)
- `00_Admin/guides/architecture/guide_aiops_agent_endpoint.md`

## Lane

Default lane: Coordinator (reporting only).

## Risks and Limits

- Low risk; avoid expanding scope beyond status.
- Do not modify files or change work context.
- Do not assume command folders exist; if missing, read `.ai_ops/workflows/work_status.md` manually.
