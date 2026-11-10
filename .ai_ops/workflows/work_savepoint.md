---
description: Validate and record a scoped work-in-progress savepoint; publish through one structured approval turn covering commit, push, and optional PR merge.
name: work_savepoint
kind: workflow
version: 1.9.3
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
    short-description: Validate and record a scoped work-in-progress savepoint; publish through one structured approval turn covering commit, push, and optional PR merge.
  interface:
    display_name: work_savepoint
    short_description: Validate and record a scoped work-in-progress savepoint; publish through one structured approval turn covering commit, push, and optional PR merge.
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

Validate and record selected work-in-progress without claiming completion.
The default invocation is a read-only checkpoint; it does not stage, commit,
or push. Pass `--commit` to request publication. Pass `--no-commit` to state the read-only intent explicitly.
Publication uses one approval turn with
separate clerical, commit, push, PR, and merge decision rows; pushing never
implies merging. Published work remains active.

## Workflow graph

```text
bootstrap/context -> resolve scope -> projected-tree validation
  -> focused validation -> read-only checkpoint
  -> [--commit?] publication-route/CI preflight
  -> [--commit?] Publication Preview and Approval Gates
  -> exact commit -> approved push -> optional approved PR/merge
  -> active work remains in_progress
  -> [archive/completion needed?] route to /closeout and stop
```

## Inputs and Preconditions

Confirm one active artifact and repository. With no active target, report
nothing scoped to save; with multiple targets, require one repository and exact
artifact set.

An `active artifact` is an entry in `.ai_ops/local/work_state.yaml` under
`work_context.active_artifacts` or the single artifact named by the operator.
Select `target_repo` from explicit scope first, then the active artifact, then
the matching `.ai_ops/local/config.yaml` `workspace.work_repos` entry; a conflict
stops for clarification. `BRG-01` is the bootstrap-required guard in
`00_Admin/configs/context_routing.yaml`. Direct mode means the target is `ai_ops`;
governed mode means ai_ops governs a different target. Read the applicable
contract: `00_Admin/specs/spec_work_mode.md`.

A `checkpoint record` is the records-only savepoint output written to the
active workbook's Execution Notes or an existing workbundle state surface. It
must name the selected `future_work` state. `not_applicable` carries no
registry or artifact binding; `linked_only` carries one or more linked IDs as
dependency context and no completion artifact set; `completion_handoff` and
`registry_sync` carry one exact ID and the frozen artifact set required by
their receipt contract. It is not canonical content, a registry mutation, or
publication approval.

## Context Routing Hook

Use `00_Admin/configs/context_routing.yaml` as the canonical onboarding contract;
apply BRG-01 and resolve onboarding tiers in order:
`fresh_bootstrap`, `resume_same_scope`, `recenter` (fallback to
`fresh_bootstrap`). Load its configured `always_read` set, expand
`read_on_demand` only when needed, and emit
`bootstrap_path`, `resume_basis`, and `reads_applied`. Resolve one active
artifact and repository before entering the steps. This lane does not make
content or remediation edits; route requested changes to `/work`.

### Run-Family Graph Hook

For run-family scope, load the identity/composition specs and generated
registry on demand. Verify registry/graph parity, generated-view
non-authority, exact run-instance lock/receipt linkage, and a validation
receipt or approved disposition for every affected consumer. Missing fan-out
evidence blocks publication; generated graph content is evidence only and
never grants write authority.

## Steps and command boundary

### Repository and Validation Preflight

Resolve `target_repo` from explicit scope, the active artifact, or the configured
work-repo list; run `git -C <repo> rev-parse --show-toplevel` and record
`repo_root`, `git_root`, and `safe_directory_applied: false`. A detached `HEAD`
stops publication; a shallow clone is reported; signed-commit configuration
requires a usable signing key. On Windows record `core.longpaths` and the
longest changed path; when long paths are disabled/unset, a changed path at or
above 240 characters reports `longpath_risk` and stops. Permission or ambiguous
Git metadata errors are not clean results. If Git reports `dubious ownership`,
stop for an operator-directed trust repair; never run `git config --global`,
and record `safe_directory_applied: false`.

In direct ai_ops mode, validate `.ai_ops/local/config.yaml` with
`00_Admin/scripts/op_validate_config.py` before running its
`savepoint_validation.minimum_commands`. In governed mode, resolve the
`governed_repo_validation` contract and execute only validated argv arrays with
`shell=False`, the trusted interpreter, and the
selected repo as `cwd`; reject shell metacharacters, unapproved executables, and
paths outside the workspace. Retry a configured network-sensitive command once,
then record a permitted partial result and `validation_escalated: true`; never
silently skip a required check.

### Publication Route and CI Preflight

The default checkpoint is read-only and does not enter this publication lane.
Only when `--commit` is requested, before approval, resolve and record the
provider publication route:
`publication_route` (`direct` or `pr_required`), protected/default branch,
required status checks, allowed merge methods, selected remote, and
`hook_runtime`. Do not test a protected branch with a direct push. If provider
metadata or hook execution cannot be verified, emit `PARK` and stop before
staging. When `pr_required` applies, create or select the branch before staging
and bind its head, base, and merge method to the approval rows; a later push
rejection must not trigger a route change or force-push.

Publication preflight is an evidence record, not a prose assertion:
`build_closeout_packet.py --publication-preflight <path>` requires the route,
base/head, required checks, merge method, remote, and verified pre-commit and
commit-msg runtime evidence, and the approval packet schema binds that record
to the projected tree.

When workflow, validator, hook, or CI surfaces are in the savepoint include set,
run `python 00_Admin/scripts/run_release_quality_gate.py` before approval. The
canonical lint result is the CI-parity precondition; focused validation alone
does not establish release readiness. A failed quality gate routes to `/work`.

Freeze the active-work records surface before security admission. Do not append
clerical records or repair receipt text after admission. Savepoint receipts
must bind a stable artifact identity, the exact active path, and the active
`HEAD`; savepoint never relocates or archives an artifact. If an active
artifact is completed or relocated, route through `/closeout`, where the
existing archive-gate receipt and post-relocation
`complete_future_work.py --verify` provide registry/receipt consistency
evidence; the archive-gate receipt remains the proof of source/destination
bytes and source absence. When a durable YAML checkpoint receipt is produced,
validate it with `python 00_Admin/scripts/validate_work_savepoint_receipt.py
--repo-root <repo_root> --receipt <receipt> --head <HEAD> --branch <branch>`;
the bound CLI and schema enforce artifact identity, active path, HEAD, branch,
future-work state, and the exact include-set hash. Preserve
receipt reviewer references exactly; changed evidence requires a new review
and a new binding. If finalization cannot be proven in closeout, report
`receipt_finalization: unavailable` and stop.

Use fixed argument-array commands only. Resolve and validate `repo_root` before
Git operations; reject reparse paths, detached heads, shell metacharacters,
force/delete options, `--no-verify`, and commands outside the selected repo.
Never run reset, checkout, clean, stash, force-push, delete, or global Git
configuration changes from this lane.

| Action | Fixed form | Gate |
| --- | --- | --- |
| inspect | `git -C <repo> status --short`, `log`, `diff` | read-only |
| stage | `git -C <repo_root> add -- <approved include paths>` | final approval |
| inspect staged | `git diff --cached --name-only` | read-only |
| commit | `git -C <repo> commit -m <approved savepoint message>` | commit row |
| push | `git -C <repo> push <approved_remote> <approved_branch>` | push row |
| create/update PR | GitHub provider action | PR row |
| merge PR | provider action with approved PR, head, base, and method | merge row |

The first leg is always read-only. Before any mutation, show the selected
artifact, exact repo-relative `include`, `related_scope_requires_confirmation`,
`exclude`, and `ignored_unpublished` buckets; validation results; proposed
`savepoint: <brief description>` message; branch, remote, PR/base/method if
applicable; and eligible clerical operations. Stop and ask once for approval of
the separate decision rows. `--commit`, prior approval, workflow state, or the
initial invocation cannot substitute for this combined approval. If merge is
declined, report the PR as unmerged and leave the work active.

## Governed-Repository Security Admission

Governed-mode savepoints use the same target-repository security admission
decision as `/closeout`; a savepoint is never a lower-gate publication lane.
Resolve target policy and hook against target `HEAD` before a `--commit` preview:

The policy file is the target's `00_Admin/configs/closeout_security_tiers.yaml`
at `HEAD`. Discover the installed hook with `git config --get core.hooksPath`;
when it is unset, require a successful `git rev-parse --git-path hooks` and
inspect the returned directory. Any Git error or empty returned path is
`security_admission: unavailable`; never fall back to a guessed `.git/hooks`
path. A Git error reading the target policy, an installed hook, or its
dispatcher configuration also yields
`security_admission: unavailable`. Inspect the target `.pre-commit-config.yaml` for the
`validate_closeout_security_head.py` or `ai-ops-closeout-security` marker. For direct ai_ops mode, “ai_ops itself” means
the selected ai_ops repository and the same HEAD-bound policy and hook checks.

- if either target policy or hook is present, use reviewer-read admission;
- if both are absent, deterministic admission is eligible only when active
  ai_ops policy explicitly allows `policy_source=missing_target_policy`;
- otherwise emit `PARK` with `security_admission: unavailable`, reference
  `fw_20261026_01`, and stop before staging, commit, push, or PR actions.

Record `admission_mode`, `policy_source`, receipt path, and disposition. A
manual waiver, skip, or unrecorded bypass is not a savepoint disposition. For a
read-only checkpoint, report applicability without Git mutation; for `--commit`,
an eligible admission and valid receipt are required before approval. Follow
`00_Admin/runbooks/rb_closeout_security_review_01.md` for the security prepass,
review caps, receipt, `Closeout-Security` trailer, and first-landing procedure.

## Future-Work Applicability Gate

The default savepoint reports `future_work: not_applicable` and does not load
completion logic, regenerate a scorecard, or mutate a registry. A referenced
registry ID is context only. An operator may explicitly request `linked_only`
context; then use the side-effect-free `closeout_applicability.py` contract and
`policy_future_work_registry.md`. An explicit `completion_handoff` or
`registry_sync` request is reported and routed to `/closeout`; savepoint does
not run completion receipts, scorecard generation, or registry synchronization.
The four states are `not_applicable`, `linked_only`, `completion_handoff`, and
`registry_sync`; missing IDs, ambiguous artifact sets, stale receipts, and
failed bindings stop explicit flows. Savepoint never claims registry or task
completion.

An explicit applicability flow exists only when the operator selects the state
in the checkpoint record; a referenced ID alone is context. A `completion
transaction` is the exact receipt-backed completion operation; a `ready-for-receipt
state` is a completed selected ID with a frozen artifact set; a `receipt handoff`
is that one completion receipt; and an `artifact set` is the exact bound paths and
HEAD. Savepoint reports these states and routes completion work to `/closeout`;
it does not resume a deferred receipt or reuse a stale binding.

## Closeout Boundary

Savepoint is an active-work checkpoint and has no archive step. Its read-only
leg may write only the checkpoint record to the permitted workbook/workbundle
state surface; that records-only output is not a content mutation or approval
for Git operations. Clerical updates in the `--commit` decision rows are
approval-dependent and do not change this boundary. It never moves work from
`90_Sandbox/` to `99_Trash/`, prepares an archive receipt, or claims
completion. If the approved set contains a tracked deletion under `90_Sandbox/`
or otherwise requires relocating a completed artifact, stop before packet
creation, route the work through `/closeout`, and do not substitute a savepoint
publication. The packet route is for active-work paths that do not require
archival; artifacts remain `in_progress`.

## Projected-Tree Validation Boundary

Keep these trees distinct:

1. `current HEAD`: committed baseline used for policy, hook, and receipt binding;
2. `projected include tree`: `HEAD` plus only the frozen approved include set;
3. `dirty worktree`: unrelated tracked changes, excluded untracked paths,
   ignored artifacts, and other local state.

Before configured validators, run:

```text
python 00_Admin/scripts/closeout_scope.py --repo-root <repo> \
  --include <approved-path> [--validator-input <path> ...]
```

Record the four scope buckets and the projected-tree manifest. Validators use
the projected tree when inputs permit it. If a validator input intersects an
excluded or ignored path, stop with `excluded_scope_conflict`; never stage the
excluded file to make validation pass. Never use `git add -f`. Never silently
widen or substitute the approved set. A dirty worktree is not evidence that the
approved include set failed.

Classify `include` as exact approved paths;
`related_scope_requires_confirmation` as required but unapproved dependencies;
`exclude` as discovered paths outside scope; and `ignored_unpublished` as
ignored local paths outside publication. A validator may use the projected tree
only when its command accepts the selected repo root or scope manifest and does
not read outside that manifest. Otherwise report `excluded_scope_conflict` and
do not claim validation of the approved set. If
`related_scope_requires_confirmation` is non-empty, stop with
`scope_pending_confirmation`; obtain operator confirmation, reclassify the paths,
and regenerate the frozen manifest before reporting `projected_tree_ready` or
requesting publication approval.

## Validation Scope

Run the target repository's configured savepoint minimum commands, focused
contract tests for touched workflow or packet surfaces, and applicable hooks or
linters. Do not require the full ai_ops test suite for each savepoint iteration;
the full repository regression suite belongs to the final `/closeout` publication
gate. On Windows record `core.longpaths`, the longest changed path, and
`longpath_risk` when the configured path limit could block publication. Record
all validation commands and any permitted network skip as partial evidence.

## Review Capacity Boundary

Apply the `/crosscheck` Loop Control contract for review tiers, caps, budgets, and
`PARK`; a savepoint does not reset counters or authorize a new commit. A savepoint
remains a records-only checkpoint by default; route a capacity stop to `/work` or
`/closeout` and preserve the receipt and manifest hashes.

## Publication Preview and Approval Gates

For `--commit`, re-read branch, HEAD, remote, dirty-tree scope, security
admission, and projected-tree results. Show the exact include set and proposed
clerical operations, then issue one combined approval request with separate rows
for clerical updates, commit, push, PR creation/update, and merge. The approval
binds the packet/tree hashes, HEAD, branch, include set, mutation plan, remote,
PR base/head, and merge method. Re-run status and the safety preflight after
approval; stop if the branch, remote, HEAD, include-set content, or dirty-tree
scope changed. Never silently widen or substitute the approved set; a changed
bound value requires a new approval.

Prefer `build_closeout_packet.py` and `apply_closeout_packet.py` for a stable
active-work set with no archival need. The packet applier stages only approved
paths, preserves unrelated index entries, runs isolated and real-index hooks,
and verifies the resulting tree. Before push, run its `--verify-push` mode. If
packet tooling fails, preserve the evidence and use the exact manual fallback;
do not broaden scope or bypass hooks.

Without packet tooling, after staging run `git diff --cached --name-only` and
stop before commit unless it equals the approved include set exactly. Commit only
after the approved commit row and all required checks pass. Push only after the
approved push row names the packet-bound commit, remote, and branch. If push
fails, preserve the local commit and report its exact hash, remote and branch;
emit `push_escalation: pr_required` for a protected-branch or remote rejection,
`push_escalation: auth_failure` for authentication, and never create a PR, merge,
retry with a wider command, or change the remote automatically.
The manual fallback must verify the resulting commit SHA, parent, tree, and
message before any push.

The fallback requires a new approval whenever rerun scope, security, projected
tree, packet, or receipt hashes change. Stop before staging, present the changed
values, and do not reuse the prior approval; unchanged exact bindings may reuse
it.
Create or update the PR through the GitHub provider only after its row is approved;
re-read the head and required checks before merging. Do not force, change the
remote, or change the merge method. A pushed but unmerged savepoint remains active.

## Outputs

Report `target_repo`, `repo_root`, `git_root`, `safe_directory_applied`,
`publication_route`, required checks, merge method, `hook_runtime`, branch,
HEAD, `push_preflight_result`, `core_longpaths`, `longest_changed_path_length`,
`longpath_risk_path`, validation commands, security admission fields, the four
scope buckets, `projected_include_tree`, `artifact_scope_drift`, approval state, commit/push/PR/merge
status, and receipt paths. Preserve `work_context.active_artifacts`; do not
clear active work, mark a workbook completed, or replace `/closeout`.

## Resources

Resources: `00_Admin/configs/context_routing.yaml`, the selected
workbook/workbundle, packet schemas, `spec_work_mode.md`, `spec_cross_surface_coordination.md`,
`policy_git_workflow_conventions.md`, and `rb_closeout_security_review_01.md`.
Read them in that order as applicable: context routing, selected artifact and
packet schemas, mode spec, cross-surface and Git policies, then the security
runbook. Each reference governs only the contract named by its title; generated
views are evidence, not authority.

## Lane

Default lane: Executor; Linter validates the checkpoint. Do not change scope,
start unrelated work, delete scratch content, or treat a prior approval or
workflow flag as the combined clerical/commit/push/PR/merge approval.

## Risks and Limits

Savepoint is a cheap checkpoint, not a completion lane. Never archive, clear
active work, widen scope, bypass hooks, force-push, or infer publication from a
flag or prior approval.
