---
description: Commit and push active work as a savepoint, then end the ai_ops session.
name: work_savepoint
kind: workflow
version: 1.1.1
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

<!-- markdownlint-disable MD013 -->
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
- `--no-commit` flag present: end the ai_ops_session without committing; skip Steps 4–6 below.
- Active workbundle/workbook/runbundle/runprogram/runbook with uncommitted changes: proceed with commit + push.

1. **Repo-Root Resolution**: Resolve the target repository root before any git operations.
   - Resolve `target_repo` from: explicit user scope → active artifact `repo` field → `.ai_ops/local/config.yaml` `workspace.work_repos` list.
   - **Explicit user scope**: an absolute path or workspace-relative path provided in the command invocation or active work context. Normalize to absolute path before passing to `git -C`.
   - **Unregistered repos**: if `target_repo` cannot be resolved from active artifacts or `work_repos`, require explicit user-provided path. Stop and ask if none given.
   - **Windows**: `git rev-parse --show-toplevel` returns POSIX-style paths (`/c/path/to/repo`). Normalize to forward-slash absolute path for all `git -C` calls.
   - Run `git -C <target_repo> rev-parse --show-toplevel` to confirm repo access and establish `repo_root`.
     - If it fails with `dubious ownership`: run `git config --global --add safe.directory <target_repo>` and
       re-run. Record `safe_directory_applied: true`. If the re-run also fails, stop and report.
     - On success: capture output as `repo_root`. Record `safe_directory_applied: false`.
   - All subsequent git commands MUST use `-C <repo_root>` or run from `<repo_root>`.
   - Emit `target_repo`, `repo_root`, `git_root`, `ops_stack_root`, `safe_directory_applied` in output.
2. **Git Preflight**: Verify repo state using confirmed `repo_root` from Step 1.
   - Run `git -C <repo_root> rev-parse --abbrev-ref HEAD`. If output is `HEAD`: emit `push_preflight: detached_head` — stop; a branch must be checked out before committing.
   - Run `git -C <repo_root> rev-parse --is-shallow-repository`. If `true`: emit `push_preflight: shallow_clone`. Warn: push may require `git fetch --unshallow` first. Record warning and proceed.
   - Run `git -C <repo_root> config --get commit.gpgsign`. If `true`: emit `signed_commits_required: true` and verify a signing key is available before the commit step.
   - Record `push_preflight_result: clean | detached_head | shallow_clone` in output.
3. **Identify scope**: Run `git -C <repo_root> status` to confirm which files have changes.
   - `warning: unable to access '.../.config/git/ignore': Permission denied` is a non-blocking environment warning. Report it explicitly; do not treat ambiguous output as a clean tree.
   - If changed files include paths not covered by any artifact in `work_state.active_artifacts`, report `artifact_scope_drift: true` and `drift_paths: [...]`. Include drifted paths in the savepoint commit unless the requestor explicitly excludes them.
4. **Stage changes**: Never stage `.ai_ops/local/**` (always machine-local). Stage all tracked files in `<repo_root>` that are in scope, unless explicitly excluded by repo-level `.gitignore` or policy. Do NOT assume `90_Sandbox/` is gitignored — verify per target repo.
5. **Commit**: Create a commit with message `savepoint: <brief description of active work>`.
6. **Push**: Push the commit to the remote branch.
   - If push fails with `remote: error: GH006`, `protected branch`, or `remote rejected`: emit `push_escalation: pr_required` — create a PR against `<default_branch>` instead. Do not retry push.
   - If push fails with `does not have permission`, `authentication failed`, or `403`: emit `push_escalation: auth_failure` — stop and report credentials issue.
   - If push fails for any other reason: record exit code and first 10 lines of stderr as `push_escalation: unknown` — stop and report.
   - On success: record `push_escalation: none`.
7. **Report**: Confirm commit hash, branch, push status, and any warnings.
8. **End session**: Work context in `.ai_ops/local/work_state.yaml` persists
   (artifacts remain in_progress). Note how to resume.

- Multiple active artifacts: ask which context to include in the savepoint message; then proceed.
  - **Default**: Savepoint **All Active** contexts in a single commit.

### Steps: Governed Mode

- No active artifacts and `--no-commit` not passed: end the session with no commit.
- `--no-commit` flag present: end session without committing.
- Active user artifacts: proceed with steps below.

1. **Repo-Root Resolution**: Same as Direct Mode Step 1.
2. **Git Preflight**: Same as Direct Mode Step 2.
3. **Validator Contract**: Read `governed_repo_validation` block from `context_routing.yaml`.
   - Read per-repo override from `.ai_ops/local/config.yaml`: find the entry in
     `workspace.work_repos` whose `path`, when resolved relative to the workspace root
     (parent directory of the ai_ops repo), matches the normalized `<target_repo>`.
     Absolute `path` values are compared directly; relative values (e.g. `my_project/`)
     are joined with the workspace root before comparing. Read its `savepoint_validation` key.
     If no matching entry exists, record `validation_commands_run: []` and proceed.
   - Run `minimum_commands` sequentially against `<repo_root>`.
   - For commands in `network_sensitive_commands`: if a network/sandbox error occurs,
     retry once; if still failing, record `validation_skipped_reason` and skip
     if `allow_partial_on_network_failure: true`. Record `validation_escalated: true`.
   - Record `validation_commands_run` in output.
4. Proceed with Direct Mode Steps 3–8 (Identify scope through End session).

### Steps: Standalone Mode

1. Confirm which context (if any) should be saved.
2. If `--no-commit` is not passed, commit + push with `savepoint:` prefix.
3. End the session and note how to resume.

## Outputs

- Savepoint confirmation; include commit hash, branch, and push status.
- If `--no-commit` was passed, report session end only.
- Report exactly which artifact(s) were included in the savepoint message.
- Output metadata fields: `target_repo`, `repo_root`, `git_root`,
  `safe_directory_applied`, `push_preflight_result`, `signed_commits_required`,
  `validation_commands_run`, `validation_escalated`, `artifact_scope_drift`,
  `push_escalation`.

## State Behavior

- `work_context.active_artifacts` in `.ai_ops/local/work_state.yaml` persists after
  savepoint (like leaving work on your desk).
- The session ends, but artifacts remain available for the next `/work` invocation.
- No automatic cleanup or state clearing occurs.

## Resources

- `00_Admin/guides/ai_operations/guide_ai_operations_stack.md`
- Active workbundle/workbook checkpoint section
- Compacted context for the selected artifact (if any)

## Lane

Default lane: Executor (savepoint writer).

## Risks and Limits

- Pauses ai_ops guidance until /work or /work_status is invoked again.
- Do not change scope or start new work.
- Do not assume command folders exist; if missing, read `.ai_ops/workflows/work_savepoint.md` manually.
