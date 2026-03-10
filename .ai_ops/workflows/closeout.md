---
description: Finalize a work session with cleanup, lint, commit, and push.
name: closeout
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
    short-description: Finalize a work session with cleanup, lint, commit, and push.
  interface:
    display_name: closeout
    short_description: Finalize a work session with cleanup, lint, commit, and push.
  policy:
    allow_implicit_invocation: true
exports:
  claude_plugin:
    enabled: true
    skill_name: closeout
  codex:
    enabled: true
    skill_name: closeout
  claude_project:
    enabled: true
    skill_name: closeout
---

# /closeout

## Purpose

Finalize a work session with cleanup, lint, commit, and push.

## Inputs and Preconditions

- Apply bootstrap guard BRG-01 before closeout steps.
- If inputs are insufficient or the request is illogical, pause and ask for clarification.

## Context Routing Hook

Use `00_Admin/configs/context_routing.yaml` as the canonical onboarding
contract.

1. Apply `commands._defaults.guard_profile` and `commands.closeout.guard_profile`.
2. Resolve onboarding tier in order: `fresh_bootstrap`,
   `resume_same_scope`, `recenter` (fallback `fresh_bootstrap` when state is
   unknown).
3. Load `always_read`; expand `read_on_demand` only when needed.
4. Emit route metadata in closeout output: `bootstrap_path`, `resume_basis`,
   and `reads_applied`.
5. If requested action is outside closeout scope or requires canonical
   remediation edits, transition to `/work`.

## Decision Matrix (Cold-Start)

### Decision Matrix - Inside (Maintainer)

- No changes: report there is nothing to close out.
- Multiple active artifacts: ask which context to close out.
- Active workbundle/workprogram/workbook/runbundle/runprogram/runbook: close out the selected context.

### Decision Matrix - External (User)

- No changes: report there is nothing to close out.
- Multiple active artifacts: ask which context to close out.
- Active work context: close out the selected context.

## Steps

### Inside Repo (Maintainer)

1. Apply bootstrap guard BRG-01: if bootstrap requirements are missing or
   unverifiable, apply `fresh_bootstrap` tier (read `AGENTS.md`) before lane
   steps.
2. If there are no changes, report there is nothing to close out and stop.
3. Update status/checkpoint notes for the selected context (if applicable).
4. Harvest keepers from scratchpad documents:
   - Promote valuable content to appropriate locations
   - Archive or delete remaining scratchpad content
   - **Default**: If unsure about an item's value, mark it as "Needs Review" and leave it in the scratchpad.
5. If a workbundle exists and a summary is requested, add `work_summary.md`.
6. Run workbook boundary check before validation/commit:
   - primary scope: touched files inside the selected workbook/workbundle path
   - promoted scope: explicitly promoted destinations documented by the active workbook
   - out-of-scope: any unrelated touched paths; require explicit confirmation before commit
   - include the scope breakdown in the closeout summary output
   - if touched paths include infrastructure surfaces (`.ai_ops/workflows/**`,
     `00_Admin/scripts/**`, `00_Admin/configs/**`, validator
     schemas), apply the checklist in
     `00_Admin/specs/spec_infrastructure_change_validation_gate.md` and record
     evidence before commit
7. If `00_Admin/backlog/future_work_registry.yaml` changed, regenerate scorecard:
   `python ai_ops/00_Admin/scripts/generate_future_work_scorecard.py`.
8. Run configured validation checks in this order:
   - repo-defined validators/checks from the active closeout contract,
   - then configured linters (markdownlint, yamllint, ruff, pre-commit) if present.
9. Evaluate commit gate explicitly:
   - If required configured checks exist, all must pass before commit.
   - If no checks are configured, require explicit user confirmation before
     commit.
   - If any required check fails, stop closeout and transition to `/work` for
     remediation.
10. Stage changes and generate commit message summary.
11. Commit with turbo authorization only when the commit gate passed and no
    explicit user hold was given.
12. Push to remote.
13. **Container completion check (Workbundle/Workprogram):**
    - **If inside a Workbundle:**
      - Check if all workbooks in the workbundle are `completed`.
      - If yes, prompt: "All workbooks in this workbundle are complete. Archive the entire workbundle to 99_Trash?"
      - If no, report which workbooks remain incomplete.
    - **If inside a Workprogram:**
      - Check if all child workbundles/workbooks are `completed` or `archived`.
      - If yes, prompt: "All items in this workprogram are complete. Archive the entire workprogram to 99_Trash?"
14. Archive completed work artifacts to `99_Trash/`:
    - Completed solitary workbook → move to Trash
    - Completed workbundle (all workbooks complete, user confirmed) → move workbundle folder to Trash
    - Completed workprogram (all workbundles complete) → move workprogram folder to Trash
    - Partially complete artifacts → leave in place
15. After relocation/archive actions, run stale-reference checks on touched
    docs/indexes and fix or report broken references before finishing.
16. Confirm closeout complete with summary of changes shipped.

### External Repo (User)

1. Apply bootstrap guard BRG-01 before lane steps.
2. If there are no changes, report there is nothing to close out and stop.
3. Update any work tracking artifacts (notes, checkpoints) if requested.
4. Read `customizations.validation_policy.governed_mode` from `.ai_ops/local/config.yaml`.
5. If `governed_mode: ai_ops`, run ai_ops validators/linters against the target scope when available.
6. If `governed_mode: repo_native`, run the repo's configured linters
   (check for .markdownlint.json, .yamllint, pre-commit hooks).
7. If no linters configured, offer to run common linters.
8. Stage changes and generate commit message summary.
9. Confirm before commit.
10. Confirm before push.
11. Summarize changes shipped.
12. If the target repo implements a future-work registry + scorecard pattern,
    run that repo's generator only when the target registry changed in approved scope.

## Outputs

- Summary of shipped changes and validation results.
- Updated workbundle status/checkpoints (inside repo).
- Optional work summary (only if requested or required by the active work artifact).

## Resources

- `00_Admin/runbooks/rb_commit_push_streamlining_01.md`
- `00_Admin/policies/policy_git_workflow_conventions.md`
- `00_Admin/guides/ai_operations/guide_scratchpad_usage.md`
- `00_Admin/specs/spec_infrastructure_change_validation_gate.md`
- `00_Admin/specs/spec_workbundle_dependency_tracking.md`

## Roles

Default role: Executor (execution); Validator for lint results.

## Risks and Limits

- Inside repo, turbo authorization may skip pauses; confirm the user wants that.
- Closeout is fast; mistakes can be costly if scope is wrong.
- Do not force push without explicit request.
- Do not skip linters (unless user explicitly requests).
- Do not commit sensitive files (.env, credentials, secrets).
- Do not delete scratchpad content without confirmation.
- Do not push without confirming in external repos.
- Do not assume command folders exist; if missing, read `.ai_ops/workflows/closeout.md` manually.
