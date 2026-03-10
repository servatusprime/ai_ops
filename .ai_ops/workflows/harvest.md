---
description: Harvest, prune, and summarize work artifacts across one or more targets.
name: harvest
kind: workflow
version: 0.1.2
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
    short-description: Harvest, prune, and summarize work artifacts across one or
      more targets.
  interface:
    display_name: harvest
    short_description: Harvest, prune, and summarize work artifacts across one or
      more targets.
  policy:
    allow_implicit_invocation: true
exports:
  claude_plugin:
    enabled: true
    skill_name: harvest
  codex:
    enabled: true
    skill_name: harvest
  claude_project:
    enabled: true
    skill_name: harvest
---

# /harvest

## Purpose

Harvest, prune, and summarize work artifacts across one or more targets.

## Inputs and Preconditions

- One or more target locations (files or folders).
- Confirm whether scope is limited to the last active work context.
- If no targets are provided, pause and ask for them.
- If inputs are insufficient or the request is illogical, pause and ask for clarification.

## Context Routing Hook

Use `00_Admin/configs/context_routing.yaml` as the canonical onboarding
contract.

1. Apply `commands._defaults.guard_profile` and `commands.harvest.guard_profile`.
2. Resolve onboarding tier in order: `fresh_bootstrap`,
   `resume_same_scope`, `recenter` (fallback `fresh_bootstrap` when state is
   unknown).
3. Enforce BRG-01:
   if bootstrap requirements are missing or unverifiable, apply
   `fresh_bootstrap` tier (read `AGENTS.md`) before lane steps.
4. Load `always_read`; expand `read_on_demand` only when needed.
5. Emit route metadata: `bootstrap_path`, `resume_basis`, and `reads_applied`.
6. If requested action requires canonical remediation edits, transition to
   `/work`.

## Decision Matrix (Cold-Start)

### Decision Matrix - Inside (Maintainer)

- No targets provided: ask for target paths; do not assume scope.
- Multiple targets: confirm priority and sequence.
- Workprogram/runprogram target: harvest within the program (not limited to a single workbundle/bundle).

### Decision Matrix - External (User)

- No targets provided: ask for targets and repo context.
- Multiple targets: confirm priority and sequence.

## Steps

### Scope Confirmation

Target precedence:

1. Explicit user-provided targets
2. Confirmed fallback to `.ai_ops/local/work_state.yaml` `work_context.active_artifacts`

If the user provides complete, non-conflicting targets in the same turn, use
those targets and proceed. Otherwise:

1. If request text is seed/proposal/datapoint intake (no explicit execution
   command), capture in active scratchpad and pause for confirmation before file
   actions.
2. Ask the user to list the harvest targets (one or more paths) when targets
   are missing or ambiguous.
3. Read active context from `.ai_ops/local/work_state.yaml` `work_context.active_artifacts` only
   when explicit targets are still missing.
   - If populated, offer **Active Artifacts** as fallback and confirm before
     use.
   - If empty, do not infer recent scope from chat memory; require explicit
     targets.
4. If targets include canonical paths (00_Admin), request explicit confirmation.
5. If the request is illogical or out of scope, ask for clarification before proceeding.

### Inside Repo (Maintainer)

1. Inventory files in each target.
2. Identify keepers to promote and artifacts to prune.
3. Default to pruning harvested scratchpads/artifacts after promotion unless the requestor opts to retain.
4. Propose actions (promote/move/archive/delete) and get confirmation.
5. Execute approved actions.
6. After relocation actions (move/archive/delete), run stale-reference checks on
   touched docs/indices and fix or report broken references before completion.
7. Update workbundle README or compacted context when applicable.
8. If `00_Admin/backlog/future_work_registry.yaml` changed, regenerate scorecard:
   `python ai_ops/00_Admin/scripts/generate_future_work_scorecard.py`.
9. Provide a short harvest summary in chat.
10. If multi-target or complex, create a short `harvest_report.md` in the primary target.

### External Repo (User)

1. Inventory files in each target.
2. Apply the repo's own rules for keep/prune decisions.
3. Propose actions and confirm before changes.
4. Execute approved actions.
5. Provide a short harvest summary in chat.
6. If the target repo implements a future-work registry + scorecard pattern,
   run that repo's generator only when the target registry changed in approved scope.

## Outputs

- Short harvest summary in chat.
- Optional `harvest_report.md` for multi-target or complex harvests.

## Resources

- `00_Admin/guides/ai_operations/guide_scratchpad_usage.md`
- `00_Admin/guides/authoring/guide_workbooks.md`

## Roles

Default roles: Coordinator → Executor.

## Risks and Limits

- If multiple targets are provided, confirm scope before moving or deleting anything.
- This command can delete artifacts; always confirm before pruning.
- Do not assume scope without confirmation.
- Do not delete artifacts without user approval.
- Do not change governance files unless explicitly authorized.
- Do not assume command folders exist; if missing, read `.ai_ops/workflows/harvest.md` manually.
