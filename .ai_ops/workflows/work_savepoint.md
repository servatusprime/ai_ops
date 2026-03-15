---
description: Commit and push active work as a savepoint, then end the ai_ops session.
name: work_savepoint
kind: workflow
version: 1.0.3
status: active
owner: ai_ops
license: Apache-2.0
claude:
  argument-hint: "[--no-commit]"
  disable-model-invocation: false
  user-invocable: true
  allowed-tools: null
  model: null
  context: null
  agent: null
codex:
  metadata:
    short-description: Commit and push active work as a savepoint, then end the ai_ops session.
  interface:
    display_name: work_savepoint
    short_description: Commit and push active work as a savepoint, then end the ai_ops session.
  policy:
    allow_implicit_invocation: true
exports:
  claude_plugin:
    enabled: true
    skill_name: work_savepoint
  codex:
    enabled: true
    skill_name: work_savepoint
  claude_project:
    enabled: true
    skill_name: work_savepoint
---

# /work_savepoint

## Purpose

Commit and push active work as a savepoint, then end the ai_ops session.
Default behavior is commit + push with a `savepoint:` prefix message. Pass
`--no-commit` to end the session without committing.

## Inputs and Preconditions

- Active work context should exist or be confirmed.
- If inputs are insufficient or the request is illogical, pause and ask for clarification.

## Context Routing Hook

Use `00_Admin/configs/context_routing.yaml` as the canonical onboarding
contract.

1. Apply `commands._defaults.guard_profile` and
   `commands.work_savepoint.guard_profile`.
2. Resolve onboarding tier in order: `fresh_bootstrap`,
   `resume_same_scope`, `recenter` (fallback `fresh_bootstrap` when state is
   unknown).
3. Enforce BRG-01:
   if bootstrap requirements are missing or unverifiable, apply
   `fresh_bootstrap` tier (read `AGENTS.md`) before lane steps.
4. Load `always_read`; expand `read_on_demand` only when needed.
5. Emit route metadata: `bootstrap_path`, `resume_basis`, and `reads_applied`.
6. Do not execute edits from `/work_savepoint`; transition to `/work` for any
   requested changes.

## Decision Matrix (Cold-Start)

### Steps: Direct Mode

- No active artifacts and `--no-commit` not passed: end the ai_ops_session with no commit.
- `--no-commit` flag present: end the ai_ops_session without committing; skip Steps 3–5 below.
- Active workbundle/workbook/runbundle/runprogram/runbook with uncommitted changes: proceed with commit + push.

1. **Identify scope**: Run `git status` to confirm which files have changes.
2. **Stage changes**: Stage relevant tracked files; do not stage `.ai_ops/local/` or `90_Sandbox/` (gitignored).
3. **Commit**: Create a commit with message `savepoint: <brief description of active work>`.
4. **Push**: Push the commit to the remote branch.
5. **Report**: Confirm commit hash, branch, and any warnings.
6. **End session**: Work context in `.ai_ops/local/work_state.yaml` persists
   (artifacts remain in_progress). Note how to resume.

- Multiple active artifacts: ask which context to include in the savepoint message; then proceed.
  - **Default**: Savepoint **All Active** contexts in a single commit.

### Steps: Governed Mode

- No active artifacts and `--no-commit` not passed: end the session with no commit.
- `--no-commit` flag present: end session without committing.
- Active user artifacts: proceed with commit + push as above.
  - If `customizations.validation_policy.governed_mode` is `ai_ops`, run ai_ops
    validators/linters for the governed repo before commit (unless the requestor
    explicitly asks to skip).
  - If `customizations.validation_policy.governed_mode` is `repo_native`, run
    the target repo's configured validators/linters before commit when available.

### Steps: Standalone Mode

1. Confirm which context (if any) should be saved.
2. If `--no-commit` is not passed, commit + push with `savepoint:` prefix.
3. End the session and note how to resume.

## State Behavior

- `work_context.active_artifacts` in `.ai_ops/local/work_state.yaml` persists after
  savepoint (like leaving work on your desk).
- The session ends, but artifacts remain available for the next `/work` invocation.
- No automatic cleanup or state clearing occurs.

## Outputs

- Savepoint confirmation; include commit hash, branch, and push status.
- If `--no-commit` was passed, report session end only.
- Report exactly which artifact(s) were included in the savepoint message.

## Resources

- `00_Admin/guides/ai_operations/guide_ai_operations_stack.md`
- Active workbundle/workbook checkpoint section
- Compacted context for the selected artifact (if any)

## Roles

Default role: Executor (savepoint writer).

## Risks and Limits

- Pauses ai_ops guidance until /work or /work_status is invoked again.
- Do not change scope or start new work.
- Do not assume command folders exist; if missing, read `.ai_ops/workflows/work_savepoint.md` manually.
