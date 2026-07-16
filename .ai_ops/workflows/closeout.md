---
description: Finalize a work session with cleanup, lint, commit, and push.
name: closeout
kind: workflow
version: 0.3.1
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

<!-- markdownlint-disable MD013 -->
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

Use `00_Admin/guides/ai_operations/guide_workflows.md` for canonical
artifact-selection and execution-context matrices. This block covers only
closeout-specific branching.

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
   - For stabilized workbook lessons, complete the harvest placement checklist:
     stable rule, canonical target, enforcement target, documentation target,
     owner, validation, follow-on state, and verified target path/section/version.
   - "Intended target" without verified placement evidence is incomplete.
5. If a workbundle exists and a summary is requested, add `work_summary.md`.
6. When promotion or pruning is in scope, require the applicable templates:
   - `01_Resources/templates/workflows/canonical_promotion_manifest_template.md`
     for copy/replace/promotion actions;
   - `01_Resources/templates/workflows/artifact_cleanup_manifest_template.md`
     for transient cleanup and retention decisions.
   Do not delete an artifact whose manifest row lacks approval, retention class,
   rollback treatment, and cleanup dependency.

   When any promoted canonical artifact is depended-upon by the current batch
   (i.e., written in this session and consumed by later phases before a
   standalone commit), agents MUST record a `promote_forward_contract:` block in
   the canonical promotion manifest for each such artifact:

   - `artifact_path`: repo-relative path of the promoted artifact
   - `evidence_ref`: path:line or command confirming the artifact is present and
     valid at the point it is consumed downstream
   - `rollback_plan`: how to revert if the promotion must be undone
   - `actor`: the agent or operator who authorized the promote-forward
   - `approval_authority`: the authority level and gate (e.g., "L4, servatusprime 2026-06-19")
   - `manifest_sync_batch`: `true` when the manifest sync is included in the
     same commit batch as the promotion; `false` with a rollback note if deferred

   This requirement applies prospectively. It does not retroactively invalidate
   promotion records that pre-date this clause.
7. Run workbook boundary check before validation/commit:
   - primary scope: touched files inside the selected workbook/workbundle path
     (use the scoped `git status`/`git diff --stat` discovery pattern in
     `policy_git_workflow_conventions.md` "Scoped Discovery for Narrow-Lane
     Work" to isolate this from full-repo worktree noise)
   - promoted scope: explicitly promoted destinations documented by the active workbook
   - out-of-scope: any unrelated touched paths (via unscoped `git status -sb`);
     require explicit confirmation before commit
   - include the scope breakdown in the closeout summary output
   - write a closeout scope manifest with these buckets before staging:
     `include`, `related_scope_requires_confirmation`, and `exclude`
   - stage only `include`; paths in `related_scope_requires_confirmation` ship
     only after explicit operator confirmation; paths in `exclude` must not be
     staged
   - unrelated dirty paths block unscoped closeout, but may be named in
     `exclude` for a scoped savepoint
   - if touched paths include infrastructure surfaces (`.ai_ops/workflows/**`,
     `00_Admin/scripts/**`, `00_Admin/configs/**`, validator
     schemas), apply the checklist in
     `00_Admin/specs/spec_infrastructure_change_validation_gate.md` and record
     evidence before commit
8. Verify completion-claim parity before status changes:
   - claim only the level actually closed (task, workbook, milestone,
     workbundle, workprogram, or program)
   - do not write a program-complete claim from a milestone closeout unless a
     program-closeout lane ran
   - synchronize required mirror surfaces in the same pass or mark the mirror
     debt as pending with owner and next surface
9. Verify promotion-record parity when canonical promotion occurred:
   - promotion record written for each promoted batch/artifact
   - required mirror set updated in the same leg
   - if not complete, record `record_pending` or `mirrors_pending` with affected
     paths, owner, and retry surface
10. If `00_Admin/backlog/future_work_registry.yaml` changed, regenerate scorecard:
   `python ai_ops/00_Admin/scripts/generate_future_work_scorecard.py`.
11. Run configured validation checks in this order:

- repo-defined validators/checks from the active closeout contract,
- then configured linters (markdownlint, yamllint, ruff, pre-commit) if present.
- when local work artifacts under ignored `90_Sandbox/**` or `99_Trash/**`
     paths are in scope, run equivalent direct lint via temp copy, stdin, or
     explicit ignore override and record the strategy in closeout evidence

12. For Level 3+ completed workbooks, run a divergence audit before commit:
    compare the latest crosscheck, current output state, and later review
    artifacts. If acceptance was overturned, return to `/work`, resolve the
    defect, and rerun completion crosscheck.
13. Verify every operator decision row has decision, rationale, date, and actor;
    pending rows block closeout and convergence claims.
14. Evaluate commit gate explicitly:

    - If required configured checks exist, all must pass before commit.
    - Require an explicit operator approval that names the final `include` set,
      the change summary, and the commit action before every commit, whether or
      not configured checks exist.
    - Require a separate explicit operator approval before every push or PR
      creation; commit approval does not imply publication approval.
    - If no checks are configured, record that fact in the approval packet;
      absence of checks never relaxes the approval requirement.
    - If any required check fails, stop closeout and transition to `/work` for
      remediation.

15. **Container completion check (Workbundle/Workprogram):**

    - **If inside a Workbundle:**
      - Check if all workbooks in the workbundle are `completed`.
      - If yes, prompt: "All workbooks in this workbundle are complete. Archive the entire workbundle to 99_Trash?"
      - If no, report which workbooks remain incomplete.
    - **If inside a Workprogram:**
      - Check if all child workbundles/workbooks are `completed` or `archived`.
      - If yes, prompt: "All items in this workprogram are complete. Archive the entire workprogram to 99_Trash?"

16. Archive completed work artifacts to `99_Trash/`:
    - Completed solitary workbook → move to Trash
    - Completed workbundle (all workbooks complete, user confirmed) → move workbundle folder to Trash
    - Completed workprogram (all workbundles complete) → move workprogram folder to Trash
    - Partially complete artifacts → leave in place
17. After relocation/archive actions, run stale-reference checks on touched
    docs/indexes and fix or report broken references before staging.
18. Update approval/validation log evidence required by policy or the active
    workbook so the shipped commit contains the final archive paths and review
    gate traceability.
19. Stage changes and generate commit message summary.
20. Commit with turbo authorization only when the commit gate passed and no
    explicit user hold was given.
21. Push to remote.
22. Confirm closeout complete with summary of changes shipped.

### External Repo (User)

1. Apply bootstrap guard BRG-01 before lane steps.
2. **Repo-Root Resolution**: Resolve the target repository root before any git operations.
   - Resolve `target_repo` from: explicit user scope → active artifact `repo` field → `.ai_ops/local/config.yaml` `workspace.work_repos` list.
   - **Explicit user scope**: an absolute path or workspace-relative path. Normalize to absolute path before passing to `git -C`.
   - **Unregistered repos**: if `target_repo` cannot be resolved, require explicit user-provided path. Stop and ask if none given.
   - **Windows**: normalize to forward-slash absolute path for all `git -C` calls.
   - Run `git -C <target_repo> rev-parse --show-toplevel` to confirm repo access and establish `repo_root`.
     - If it fails with `dubious ownership`: run `git config --global --add safe.directory <target_repo>` and
       re-run. Record `safe_directory_applied: true`. If the re-run also fails, stop and report.
     - On success: capture output as `repo_root`. Record `safe_directory_applied: false`.
   - All subsequent git commands MUST use `-C <repo_root>` or run from `<repo_root>`.
3. **Git Preflight**: Verify repo state using confirmed `repo_root` from Step 2.
   - Run `git -C <repo_root> rev-parse --abbrev-ref HEAD`. If output is `HEAD`: emit `push_preflight: detached_head` — stop; a branch must be checked out before committing.
   - Run `git -C <repo_root> rev-parse --is-shallow-repository`. If `true`: emit `push_preflight: shallow_clone`. Record warning and proceed.
   - Run `git -C <repo_root> config --get commit.gpgsign`. If `true`: emit `signed_commits_required: true` and verify a signing key is available.
4. If there are no changes, report there is nothing to close out and stop.
5. Update any work tracking artifacts (notes, checkpoints) if requested.
6. **Validator Contract**: Read `customizations.validation_policy.governed_mode` from `.ai_ops/local/config.yaml`.
   Read `governed_repo_validation` from `context_routing.yaml`.
   - Read per-repo override: find the entry in `workspace.work_repos` whose `path`, when resolved relative
     to the workspace root, matches `<target_repo>`, and read its `savepoint_validation.minimum_commands`.
     If no matching entry exists, use `governed_repo_validation.minimum_commands` only.
   - If `governed_mode: ai_ops`: run each command in `minimum_commands` sequentially against `<repo_root>`.
     For commands in `network_sensitive_commands`: retry once on network/sandbox error; if still failing,
     record `validation_skipped_reason` and skip if `allow_partial_on_network_failure: true`.
     Record `validation_escalated: true` if any command was skipped.
   - If `governed_mode: repo_native`: detect repo-native linters (`.markdownlint.json`, `.yamllint`,
     pre-commit hooks) and run them. If none configured, offer to run common linters.
   - Record `validation_commands_run` in output.
7. Stage changes and generate commit message summary.
8. **Push Preflight** (if push is planned): verify `push_preflight_result` from Step 3 is `clean` or `shallow_clone`. If `detached_head`, stop before commit.
9. Commit.
10. **Push and failure handling**: Push to remote.
    - If push fails with `protected branch` or `remote rejected`: emit `push_escalation: pr_required` — create a PR against `<default_branch>` instead.
    - If push fails with authentication error: emit `push_escalation: auth_failure` — stop and report.
    - If push fails for any other reason: record exit code and stderr as `push_escalation: unknown` — stop and report.
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
- `00_Admin/specs/spec_cross_surface_coordination.md`

## Lane

Default lane: Executor (execution); Linter for lint results.

## Risks and Limits

- Inside repo, turbo authorization may skip pauses; confirm the user wants that.
- Closeout is fast; mistakes can be costly if scope is wrong.
- Do not force push without explicit request.
- Do not skip linters (unless user explicitly requests).
- Do not commit sensitive files (.env, credentials, secrets).
- Do not delete scratchpad content without confirmation.
- Do not push without confirming in external repos.
- Do not assume command folders exist; if missing, read `.ai_ops/workflows/closeout.md` manually.
