---
description: Validate, commit, and push a scoped work-in-progress savepoint after explicit final approval.
name: work_savepoint
kind: workflow
version: 1.3.0
status: active
owner: ai_ops
license: Apache-2.0
claude:
  argument-hint: "[--commit] [--no-commit]"
  disable-model-invocation: true
  user-invocable: true
  allowed-tools: null
  model: null
codex:
  metadata:
    short-description: Validate, commit, and push a scoped work-in-progress savepoint after explicit final approval.
  interface:
    display_name: work_savepoint
    short_description: Validate, commit, and push a scoped work-in-progress savepoint after explicit final approval.
  policy:
    allow_implicit_invocation: false
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

Save selected work-in-progress to the repository and its configured Git remote,
then end the ai_ops session without claiming completion. Invocation expresses
save intent. The workflow first validates and previews the exact scope, commit
message, remote, and branch, then waits for explicit final requestor approval
before it stages, commits, or pushes.

Pass `--no-commit` to create a read-only checkpoint. `--commit` is accepted as
an explicit spelling of the default save intent, but it never bypasses the
final approval gate.

## Inputs and Preconditions

- Active work context and one target repository/artifact should exist or be
  confirmed.
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
6. Do not make content or remediation edits from `/work_savepoint`; transition
   to `/work` for requested changes. Git publication may run only through the
   approval-gated steps below.

## Steps

### Command Registry and Approval Boundary

Savepoint preflight uses fixed, argument-array Git commands only:

| Purpose | Allowed form | Mutation |
| --- | --- | --- |
| branch/head | `git -C <resolved_repo> rev-parse ...` | none |
| repository state | `git -C <resolved_repo> status --short` | none |
| history/diff | `git -C <resolved_repo> log ...`, `git -C <resolved_repo> diff ...` | none |
| configured validation | exact `minimum_commands` after path/owner validation | governed by the target contract |
| stage approved paths | `git -C <resolved_repo> add -- <approved_paths...>` | after final approval only |
| inspect staged paths | `git -C <resolved_repo> diff --cached ...` | none |
| commit | `git -C <resolved_repo> commit -m <approved_message>` | after final approval only |
| push | `git -C <resolved_repo> push <approved_remote> <approved_branch>` | after final approval only |

Never concatenate a user-supplied branch, path, message, remote, or option into
a shell command. Pass arguments as arrays and reject a target that resolves
outside the selected repository or through a reparse point. Never run reset,
checkout, clean, stash, force-push, delete, or global Git configuration changes
from this lane.

The first leg is always read-only. Before any mutation, show the exact include
set, exclusions, validation results, proposed `savepoint:` message, remote, and
branch. Then stop and wait for an explicit requestor go-ahead covering both the
commit and push. Workflow state, a prior approval, `--commit`, or the initial
invocation cannot substitute for this final approval.

### Direct Mode

- No active artifact or explicit target: report that there is nothing scoped
  to save and stop without Git mutation.
- `--no-commit`: prepare the checkpoint summary and resume instructions, then
  stop without asking for publication approval.
- Active work with changes: prepare the scoped publication proposal and final
  approval gate below.

1. **Repo-Root Resolution**: Resolve the target repository root before any git operations.
   - Resolve `target_repo` from: explicit user scope → active artifact `repo` field → `.ai_ops/local/config.yaml` `workspace.work_repos` list.
   - **Explicit user scope**: an absolute path or workspace-relative path provided in the command invocation or active work context. Normalize to absolute path before passing to `git -C`.
   - **Unregistered repos**: if `target_repo` cannot be resolved from active artifacts or `work_repos`, require explicit user-provided path. Stop and ask if none given.
   - **Windows**: `git rev-parse --show-toplevel` returns POSIX-style paths (`/c/path/to/repo`). Normalize to forward-slash absolute path for all `git -C` calls.
   - Run `git -C <target_repo> rev-parse --show-toplevel` to confirm repo access and establish `repo_root`.
     - If it fails with `dubious ownership`, stop and request explicit approval
       for any machine-global trust change. Do not run `git config --global`
       from a savepoint flow.
     - On success: capture output as `repo_root`. Record `safe_directory_applied: false`.
   - All subsequent git commands MUST use `-C <repo_root>` or run from `<repo_root>`.
   - Emit `target_repo`, `repo_root`, `git_root`, `ops_stack_root`, `safe_directory_applied` in output.
2. **Git Preflight**: Verify repo state using confirmed `repo_root` from Step 1.
   - Run `git -C <repo_root> rev-parse --abbrev-ref HEAD`. If output is `HEAD`: emit `push_preflight: detached_head` — stop; a branch must be checked out before committing.
   - Run `git -C <repo_root> rev-parse --is-shallow-repository`. If `true`: emit `push_preflight: shallow_clone`. Warn: push may require `git fetch --unshallow` first. Record warning and proceed.
   - Run `git -C <repo_root> config --get commit.gpgsign`. If `true`: emit `signed_commits_required: true` and verify a signing key is available before the commit step.
   - Record `push_preflight_result: clean | detached_head | shallow_clone |
     longpath_risk | permission_blocked` in output.
   - On Windows, run `git -C <repo_root> config --get core.longpaths` and
     record `core_longpaths: true | false | unset`. Measure the longest changed
     repo-relative path. If long paths are disabled/unset and a changed path is
     240 characters or longer, stop before staging and report
     `push_preflight: longpath_risk` with the path; do not silently change Git
     configuration.
   - Treat Git metadata permission errors as a bounded escalation: report the
     failing path and operation, retry only after an approved permission repair,
     and never interpret ambiguous or permission-denied status output as clean.
3. **Identify scope**: Run `git -C <repo_root> status --porcelain=v1
   --untracked-files=all` to capture the complete candidate set.
   - `warning: unable to access '.../.config/git/ignore': Permission denied` is a non-blocking environment warning. Report it explicitly; do not treat ambiguous output as a clean tree.
   - Classify every path as `include`, `related_scope_requires_confirmation`,
     `exclude`, or `ignored_unpublished`.
   - Include only paths attributable to the selected active artifact and current
     savepoint. Do not include drift, unrelated changes, local state, secrets,
     credentials, or generated/transient files without an authored inclusion
     basis.
   - Use `git check-ignore -v -- <path>` when ignore status is uncertain.
     Never use `git add -f` in this workflow. Report ignored evidence as not
     publishable by ordinary savepoint and route any policy change to `/work`.
   - If changed files are not covered by the selected artifact, emit
     `artifact_scope_drift: true` and list `drift_paths`; keep them excluded.
4. **Validation**: Run the configured savepoint validation for the target repo.
   All required checks must pass. A skipped network-sensitive check is allowed
   only when the configured contract explicitly permits it and the preview
   labels the result partial.
5. **Publication Preview and Final Approval Gate**: Show:
   - selected artifact and repository;
   - exact repo-relative `include`, `related_scope_requires_confirmation`,
     `exclude`, and `ignored_unpublished` lists;
   - validation commands and results;
   - proposed `savepoint: <brief description>` commit message;
   - current branch and exact push remote;
   - a statement that active work remains in progress and no closeout/archive
     claim will be made.

   Stop and ask for explicit approval to stage the displayed include set,
   create the displayed commit, and push it to the displayed remote/branch.
   Do not mutate Git until that answer is received. If `--no-commit` was used,
   emit the same scope summary without a publication request and proceed to
   Step 10.
6. **Revalidation After Approval**: Re-run status and the safety preflight.
   Stop if the branch, remote, HEAD, include-set content, or dirty-tree scope
   changed since the preview. Never silently widen or substitute the approved
   set.
7. **Stage Exact Paths**: Run `git -C <repo_root> add --
   <approved_include_paths...>`. Verify `git diff --cached --name-only` equals
   the approved include set exactly. Stop before commit on any mismatch.
8. **Commit**: Commit with the approved `savepoint:` message. If commit fails,
   report the staged state and stop without reset or cleanup.
9. **Push**: Push the new commit to the approved remote and branch. Do not
   force, create a PR, change the remote, or retry with a wider command. If the
   push fails, preserve and report the local commit hash and exact failure.
10. **End session**: Report the checkpoint or published savepoint. Work context
    in `.ai_ops/local/work_state.yaml` persists and artifacts remain
    `in_progress`; note how to resume.

- Multiple active artifacts: require selection of one repository and an exact
  artifact set before building the preview. Never default to "all active."

### Governed Mode

- No active artifact or explicit target: report that there is nothing scoped
  to save and stop.
- `--no-commit`: run the read-only checkpoint path.
- Active user artifacts: proceed with the approval-gated savepoint path.

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
4. Proceed with Direct Mode Steps 3–10 (Identify scope through End session).

### Standalone Mode

1. Confirm the target repository and exact work scope.
2. Apply the same repo-root, safety preflight, four-bucket scope
   classification, validation, preview, final approval, revalidation,
   exact-path staging, commit, push, and state-preservation contract used in
   Direct Mode.
3. `--no-commit` selects the read-only checkpoint path. `--commit` states save
   intent but does not bypass the preview and final approval gate.

## Outputs

- Publication preview with exact scope, validation results, proposed commit
  message, remote, branch, and a pending final-approval state.
- Published savepoint confirmation with commit hash, branch, remote, and push
  status after approval and successful execution.
- Read-only checkpoint confirmation when `--no-commit` is passed.
- Report exactly which artifact(s) were included in the savepoint message.
- Output metadata fields: `target_repo`, `repo_root`, `git_root`,
  `safe_directory_applied`, `push_preflight_result`, `core_longpaths`,
  `longest_changed_path_length`, `longpath_risk_path`, `signed_commits_required`,
  `validation_commands_run`, `validation_escalated`, `artifact_scope_drift`,
  `include`, `related_scope_requires_confirmation`, `exclude`,
  `ignored_unpublished`, `approval_state`, `commit_hash`, `push_status`, and
  `push_escalation`.

## State Behavior

- `work_context.active_artifacts` in `.ai_ops/local/work_state.yaml` persists after
  savepoint (like leaving work on your desk).
- The session ends, but artifacts remain available for the next `/work` invocation.
- No automatic cleanup or state clearing occurs.
- Savepoint publication does not mark a task, workbook, workbundle, or program
  complete and does not replace `/closeout`.

## Resources

- `00_Admin/guides/ai_operations/guide_ai_operations_stack.md`
- Active workbundle/workbook checkpoint section
- Compacted context for the selected artifact (if any)

## Lane

Default lane: Executor (savepoint writer).

## Risks and Limits

- Pauses ai_ops guidance until `/work` or `/work_status` is invoked again.
- Do not change scope or start new work.
- Never treat the initial invocation, `--commit`, earlier approval, or workflow
  metadata as the final commit/push approval.
- Never stage unrelated paths, ignored evidence, machine-local state, secrets,
  or credentials.
- Do not assume command folders exist; if missing, read `.ai_ops/workflows/work_savepoint.md` manually.
