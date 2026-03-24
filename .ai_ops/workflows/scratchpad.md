---
description: Create a scratchpad for session notes and observations.
name: scratchpad
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
    short-description: Create a scratchpad for session notes and observations.
  interface:
    display_name: scratchpad
    short_description: Create a scratchpad for session notes and observations.
  policy:
    allow_implicit_invocation: true
exports:
  claude_plugin:
    enabled: true
    skill_name: scratchpad
  codex:
    enabled: true
    skill_name: scratchpad
  claude_project:
    enabled: true
    skill_name: scratchpad
---

# /scratchpad

## Purpose

Create a scratchpad for session notes and observations.

## Inputs and Preconditions

- Ask the user what the scratchpad is for if unclear.
- If inputs are insufficient or the request is illogical, pause and ask for clarification.

## Context Routing Hook

Use `00_Admin/configs/context_routing.yaml` as the canonical onboarding
contract.

1. Apply `commands._defaults.guard_profile` and
   `commands.scratchpad.guard_profile`.
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

- Target provided (workbundle/workprogram/runbundle/runprogram/workbook/runbook): place scratchpad there.
- Multiple active artifacts: ask which to attach the scratchpad to.
- No target provided: ask where to place the scratchpad.

### Decision Matrix - Governed (External Repo with ai_ops)

- Target provided in external repo: place scratchpad in external repo's sandbox.
- No target in external repo: place in external repo's sandbox (`90_Sandbox/` or equivalent).
- Scratchpads belong in the repo where the work is happening, not in ai_ops.

### Decision Matrix - External (User)

- Target provided (project notes folder or specific artifact): place scratchpad there.
- No target provided: ask where to place notes (docs/notes, .notes, or root).

## Steps

### Inside Repo (Maintainer)

1. Ask for the target artifact or location (workbundle/workprogram/runbundle/runprogram/workbook/runbook).
2. Create scratchpad in the requested location:
   - Workbundle/workprogram/runbundle/runprogram: `_scratchpad_<agent>_<date>.md`
   - Standalone target: `scratchpad_<topic>_<date>.md`
3. Use template from `01_Resources/templates/workflows/scratchpad_template.md`.
4. Scratchpad sections from template are default.
5. If requestor asks to capture potential future work, include the optional
   future-work matrix section at top of that section.

### External Repo (User)

1. Ask for the preferred notes location.
2. Create scratchpad in the requested location.
3. Use simplified template:
   - Date, Topic, Notes, Action Items
4. Do not reference ai_ops internal paths.

## Outputs

- New scratchpad file in the appropriate location.

## Resources

- `00_Admin/guides/ai_operations/guide_scratchpad_usage.md`

## Lane

Default lane: Executor (notes capture).

## Risks and Limits

- Scratchpads are transient; promote keepers before closeout.
- Do not create scratchpads without user context (ask what it's for).
  - **Default Intent**: If unspecified, assume General Session Notes.
  - **Default Location**: If unspecified, place in the root of the active work context or repo root.
- Do not overwrite existing scratchpads (use unique names).
- Do not promote scratchpad content automatically (user decision).
- Do not assume command folders exist; if missing, read `.ai_ops/workflows/scratchpad.md` manually.
