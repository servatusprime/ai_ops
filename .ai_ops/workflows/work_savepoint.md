---
description: Validate and record a scoped work-in-progress savepoint; publish through one structured approval turn covering clerical work, commit, push, and optional PR merge.
name: work_savepoint
kind: workflow
version: 1.7.0
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
    short-description: Validate and record a scoped work-in-progress savepoint; publish through one structured approval turn covering clerical work, commit, push, and optional PR merge.
  interface:
    display_name: work_savepoint
    short_description: Validate and record a scoped work-in-progress savepoint; publish through one structured approval turn covering clerical work, commit, push, and optional PR merge.
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

Validate and record selected work-in-progress, then end the ai_ops session
without claiming completion. The default invocation is a read-only checkpoint;
it does not stage, commit, or push. Pass `--commit` to request publication.
Publication still requires one structured approval turn below. That turn must
list the eligible clerical operations, commit, push, and (when a PR flow is
used) merge as separate decision rows. The merge row must name the PR, base
branch, current head SHA, and merge method; pushing never implies merging.
Pass `--no-commit` to state the read-only intent explicitly.

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
   approval-gated steps below. When the packet route is used, the approval
   binds the prepared packet hash, base HEAD, branch, include set, mutation
   plan, and projected tree; a parked or cost-exceeded packet cannot be
   released by editing and rehashing its state.

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
| commit | `git -C <resolved_repo> commit -m <approved_message>` | combined approval turn's commit row |
| push | `git -C <resolved_repo> push <approved_remote> <approved_branch>` | combined approval turn's push row |
| create/update PR | GitHub provider action for the approved repository, head, and base | after the combined approval turn's PR/merge row is approved |
| merge PR | GitHub provider action with the approved PR, expected head SHA, and method (`squash` preferred when approved) | after the combined approval turn's merge row is approved |

Never concatenate a user-supplied branch, path, message, remote, or option into
a shell command. Pass arguments as arrays and reject a target that resolves
outside the selected repository or through a reparse point. Never run reset,
checkout, clean, stash, force-push, delete, or global Git configuration changes
from this lane.

The first leg is always read-only. Before any mutation, show the exact include
set, exclusions, validation results, proposed `savepoint:` message, remote,
branch, whether a PR/merge phase is proposed, and all eligible clerical
operations. Then issue one combined approval request with separate decision
rows for: clerical updates; commit naming the include set and message; push
naming the packet-bound commit plan, remote, and branch; and PR creation/update plus
merge naming the PR (or proposed head/base pair before PR creation), current
head SHA, and method. The operator may approve or decline each row in that one
turn. Workflow state, a prior approval, `--commit`, or the initial invocation
cannot substitute for the combined approval. If the merge row is declined, the
savepoint may end after a successful push and must report the PR as unmerged
rather than inferring completion.

### Governed-Repository Security Admission

Governed-mode savepoints use the same target-repository security admission
decision as `/closeout`; a savepoint must not become a lower-gate publication
lane. Resolve the target repository's closeout-security policy and installed
hook against the confirmed `repo_root` before a `--commit` preview:

- If either the target policy or hook is present, use reviewer-read admission
  against target `HEAD`. Deterministic admission is not applicable.
- If both are absent, deterministic admission is eligible only when the active
  ai_ops policy explicitly allows `policy_source=missing_target_policy`.
  Otherwise emit `PARK` with `security_admission: unavailable`, reference
  `fw_20261026_01`, and stop before staging, commit, push, or PR actions.
- Record `admission_mode`, `policy_source`, receipt path, and overall
  disposition in the checkpoint or publication preview. A manual waiver, skip,
  or unrecorded bypass is not a savepoint disposition; the future-work item
  remains open until a first-class route is implemented.
- For the default or `--no-commit` checkpoint, report security applicability and
  any parked disposition without mutating Git. For `--commit`, a valid receipt
  and eligible disposition are required before the combined approval turn.

### Future-Work Applicability Gate

Freeze future-work applicability before reading completion schemas, importing
`complete_future_work.py`, regenerating a scorecard, preparing a receipt, or
pruning a registry. Use the side-effect-free classifier:

```text
python 00_Admin/scripts/closeout_applicability.py --intent not_applicable
```

The default savepoint is `future_work: not_applicable`: it records no registry
completion claim, does not load completion logic, and does not mutate a target
registry or scorecard. A referenced registry ID is context only and does not
promote applicability. Use `linked_only` for dependency context,
`completion_handoff` for one exact receipt-ready ID and artifact set, and
`registry_sync` only after a verified success receipt. Failure, pending, and
stale states preserve the registry and remain separate from security admission
and projected-tree validation.

### Closeout Boundary

Savepoint is an active-work checkpoint and has no archive step. It never moves
work from `90_Sandbox/` to `99_Trash/`, prepares an archive receipt, or claims
completion. If the approved savepoint include set contains a tracked deletion
under `90_Sandbox/` or otherwise requires relocating a completed artifact, stop
before packet creation and route the work through `/closeout`. The savepoint
packet route is for active-work paths that do not require archival.

### Projected-Tree Validation Boundary

Savepoint validation MUST keep these trees distinct:

1. `current HEAD`: the committed baseline used for policy, hook, and receipt
   binding;
2. `projected include tree`: `HEAD` plus only the frozen approved include set;
3. `dirty worktree`: every unrelated tracked change, excluded untracked path,
   ignored artifact, and other local state.

Before configured validators, run:

```text
python 00_Admin/scripts/closeout_scope.py --repo-root <repo> \
  --include <approved-path> [--validator-input <path> ...]
```

Record the separate `include`, `related_scope_requires_confirmation`, `exclude`,
and `ignored_unpublished` buckets, including the `projected_include_tree`
manifest. Validators must use the projected include tree when their inputs
permit it. If a validator input intersects an excluded
or ignored path, stop with `excluded_scope_conflict`, identify the path and
owning scope, and do not stage the excluded file. A dirty worktree is not
evidence that the approved include set failed.

### Direct Mode

- No active artifact or explicit target: report that there is nothing scoped
  to save and stop without Git mutation.
- no flag or `--no-commit`: prepare the checkpoint summary and resume
  instructions, then stop without asking for publication approval.
- `--commit`: prepare the scoped publication and optional PR/merge proposal,
  then enter the combined approval turn below.

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
5. **Publication Preview and Approval Gates** (`--commit` only): Show:
   - selected artifact and repository;
   - exact repo-relative `include`, `related_scope_requires_confirmation`,
     `exclude`, and `ignored_unpublished` lists;
   - validation commands and results;
   - proposed `savepoint: <brief description>` commit message;
   - current branch and exact push remote;
   - proposed PR base/head and merge method, when a PR flow is applicable;
   - the exact clerical operations to be performed within the savepoint scope;
   - a statement that active work remains in progress and no closeout/archive
     claim will be made.

   Stop and ask once for approval of the displayed decision rows: clerical
   updates, commit, push, and PR creation/update plus merge when applicable.
   The approval binds the exact scope, commit, remote, branch, PR base/head,
   and merge method. Do not mutate Git or the remote until the combined
   approval is received. If no flag or `--no-commit` was used, emit the scope
   summary without a publication request and proceed to Step 10.
6. **Revalidation After Approval**: Re-run status and the safety preflight.
   Stop if the branch, remote, HEAD, include-set content, or dirty-tree scope
   changed since the preview. Never silently widen or substitute the approved
   set.
7. **Stage Exact Paths**: Prefer the shared tree-bound packet route when the
    savepoint has a stable active-work include set with no `90_Sandbox/`
    deletion: build a packet with
    `00_Admin/scripts/build_closeout_packet.py`, obtain an approval file that
    validates against `00_Admin/configs/validator/schema_closeout_approval.yaml`
    and binds its packet/tree hashes, and apply it with
    `00_Admin/scripts/apply_closeout_packet.py`. If archival is needed, stop
    and route to `/closeout` before building the packet. The applier uses
     an isolated approved-scope pre-commit preflight followed by a second
     run against the actual staged index immediately before an ordinary exact
     `git commit --only`. The installed native pre-commit and commit-msg hooks
     remain enabled for the commit; a disposable-clone dry run against the
     real ai_ops shims passed on 2026-10-23. It preserves unrelated staged entries and
     fails closed on index, hook, policy, projection, cost, or post-commit tree
     drift. Before any push, verify the packet with
     `apply_closeout_packet.py --verify-push` and include the returned commit
     SHA, remote, and branch in the combined approval turn's push row.
     Without a
    packet, run `git -C <repo_root> add -- <approved_include_paths...>` and
    verify `git diff --cached --name-only` equals the approved include set
    exactly. Stop before commit on any mismatch. If packet tooling fails, use
    the canonical manual fallback in `.ai_ops/workflows/closeout.md`; preserve
    the packet and do not widen the scope or bypass hooks.
8. **Commit**: Commit with the approved `savepoint:` message. If staging,
     hook preflight, or commit fails, the packet route attempts to unstage only
     its included paths, records whether cleanup succeeded, and parks the
     packet for inspection; unrelated staged entries remain preserved. The
     packet route never pushes.
     The fixed packet invocation is intended to reduce command-boundary
     ceremony, not to change host permission policy. Prompt behavior remains
     platform-dependent; if a prompt or tooling failure persists, stop at the
     same approval gate and use the manual path rather than widening an
     allowlist or silently retrying with a different command form.
9. **Push**: Push the new commit to the approved remote and branch. Do not
   force, change the remote, or retry with a wider command. If the push fails,
   preserve and report the local commit hash and exact failure.
10. **PR and merge phase** (`--commit` only, when approved): After a successful
    push, use the approved PR/merge decision row. Create or update the PR through the GitHub
    provider, re-read its current head, verify required checks/reviews, and
    merge only when the current head still equals the approved commit. Use the
    approved method, with squash when selected; do not fall back to another
    method. If merge approval is absent or merge fails, report the pushed PR as
    pending/unmerged. A merged savepoint remains an active work context and
    does not claim workbook or program completion.
11. **End session**: Report the checkpoint or published savepoint. Work context
    in `.ai_ops/local/work_state.yaml` persists and artifacts remain
    `in_progress`; note how to resume.

- Multiple active artifacts: require selection of one repository and an exact
  artifact set before building the preview. Never default to "all active."

### Governed Mode

- No active artifact or explicit target: report that there is nothing scoped
  to save and stop.
- no flag or `--no-commit`: run the read-only checkpoint path.
- `--commit`: proceed with the approval-gated savepoint path.

1. **Repo-Root Resolution**: Same as Direct Mode Step 1.
2. **Git Preflight**: Same as Direct Mode Step 2.
3. **Validator Contract**: Read `governed_repo_validation` block from `context_routing.yaml`.
   - Read per-repo override from `.ai_ops/local/config.yaml`: find the entry in
     `workspace.work_repos` whose `path`, when resolved relative to the workspace root
     (parent directory of the ai_ops repo), matches the normalized `<target_repo>`.
     Absolute `path` values are compared directly; relative values (e.g. `my_project/`)
     are joined with the workspace root before comparing. Read its `savepoint_validation` key.
     If no matching entry exists, record `validation_commands_run: []` and proceed.
   - First run `python <ai_ops_root>/00_Admin/scripts/op_validate_config.py <ai_ops_root>/.ai_ops/local/config.yaml` and stop if it fails. Treat each `minimum_commands` entry as a validated argv array, never a shell string; execute it sequentially with `shell=False`, `cwd=<repo_root>`, and no command interpolation. Use the same trusted Python runtime that passed validation; never re-resolve a bare executable through a changed `PATH`. Reject an entry containing shell metacharacters, an unapproved executable, or a path outside `<repo_root>` / the workspace.
   - For commands in `network_sensitive_commands`: if a network/sandbox error occurs,
     retry once; if still failing, record `validation_skipped_reason` and skip
     if `allow_partial_on_network_failure: true`. Record `validation_escalated: true`.
   - Record `validation_commands_run` in output.
4. Proceed with Direct Mode Step 3 (Identify scope), apply the
   Governed-Repository Security Admission contract to that frozen candidate
   include set, and complete Direct Mode Step 4 (Validation). A parked security
   outcome stops the savepoint before its publication preview.
5. Proceed with Direct Mode Steps 5–11 (publication preview through End
   session); only `--commit` enters the publication preview and approval gate.

### Standalone Mode

1. Confirm the target repository and exact work scope.
2. Apply the same repo-root, safety preflight, four-bucket scope
   classification, validation, preview, combined approval, revalidation,
   exact-path staging, commit, push, and state-preservation contract used in
   Direct Mode.
3. No flag or `--no-commit` selects the read-only checkpoint path. `--commit`
   requests publication but does not bypass the preview and combined approval
   gate.

## Outputs

- Publication preview with exact scope, validation results, proposed commit
  message, remote, branch, and a pending final-approval state.
- Published savepoint confirmation with commit hash, branch, remote, and push
  status after the single combined approval turn and successful execution, plus PR and merge status when
  a PR flow was requested.
- Read-only checkpoint confirmation when no flag or `--no-commit` is passed.
- Report exactly which artifact(s) were included in the savepoint message.
- Output metadata fields: `target_repo`, `repo_root`, `git_root`,
  `safe_directory_applied`, `push_preflight_result`, `core_longpaths`,
  `longest_changed_path_length`, `longpath_risk_path`, `signed_commits_required`,
  `validation_commands_run`, `validation_escalated`, `artifact_scope_drift`,
  `include`, `related_scope_requires_confirmation`, `exclude`,
  `ignored_unpublished`, `approval_state`, `commit_hash`, `push_status`,
  `push_escalation`, `pr_number`, `pr_status`, `merge_method`, `merge_status`,
  `approval_turn_id`, `security_admission`, `security_admission_mode`,
  `security_policy_source`, `security_receipt`, and `security_disposition`.

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
  metadata as the combined clerical, commit, push, PR, or merge approval.
- Never stage unrelated paths, ignored evidence, machine-local state, secrets,
  or credentials.
- Do not assume command folders exist; if missing, read `.ai_ops/workflows/work_savepoint.md` manually.
