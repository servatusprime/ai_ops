---
description: Prepare a read-only closeout packet, then publish through exact approval-gated commit, push, and PR-merge steps.
name: closeout
kind: workflow
version: 0.10.2
status: active
owner: ai_ops
license: Apache-2.0
claude:
  argument-hint: null
  disable-model-invocation: false
  user-invocable: true
  allowed-tools: null
  model: null
codex:
  metadata:
    short-description: Prepare a read-only closeout packet, approve applicable archive at the existing container-completion decision, then publish through one structured approval turn covering commit, push, and PR merge.
  interface:
    display_name: closeout
    short_description: Prepare a read-only closeout packet, approve applicable archive at the existing container-completion decision, then publish through one structured approval turn covering commit, push, and PR merge.
  policy:
    allow_implicit_invocation: false
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

Close the selected work context through a read-only preparation leg and one
structured publication approval. Closeout means completion and publication:
applicable completed artifacts move from `90_Sandbox/` to a recoverable
`99_Trash/` destination before packet construction and staging. An ordinary
scoped closeout records `archive_gate: not_applicable`; it never invents an
archive operation. Preparation never stages, commits, pushes, creates or
updates a PR, merges, archives, deletes, or repairs content. Remediation routes
to `/work`.

## Workflow graph

```text
bootstrap/context -> resolve scope -> future-work review (optional, read-only)
  -> archive applicability/rows -> existing container-completion decision
  -> approved archive move -> stale-reference check -> re-freeze scope
  -> publication-route/CI/finalization preflight -> projected-tree validation
  -> security admission -> packet/hash binding
  -> one publication approval turn
  -> exact commit -> approved push -> approved PR/merge -> final receipt/status
  -> terminal packet retention sweep
```

## Inputs and Preconditions

- Apply bootstrap guard BRG-01 before closeout steps.
- Confirm one active context and repository; insufficient or illogical input
  stops for clarification.

Selection terms are explicit: `BRG-01` is the bootstrap-required guard defined
in `00_Admin/configs/context_routing.yaml`; an `active artifact` is an entry in
`.ai_ops/local/work_state.yaml` under `work_context.active_artifacts` or the
single artifact named by the operator; `target_repo` is selected from explicit
scope first, then the active artifact, then the matching entry in
`.ai_ops/local/config.yaml` `workspace.work_repos`. A conflict between those
sources stops for clarification rather than being resolved by guessing.
Direct mode means `target_repo` is `ai_ops`; governed mode means `ai_ops`
governs a different selected target. Read the applicable mode contract:
`00_Admin/specs/spec_work_mode.md`.

A `preparation record` is the records-only closeout output written to the
active workbook's Execution Notes or an existing workbundle state surface. It
must name the selected `future_work` state. `not_applicable` carries no
registry or artifact binding; `linked_only` carries one or more linked IDs as
dependency context and no completion artifact set; `completion_handoff` and
`registry_sync` carry one exact ID and the frozen artifact set required by
their receipt contract. It is not selected content, a registry mutation, or
publication approval.

## Context Routing Hook

Use `00_Admin/configs/context_routing.yaml` as the canonical onboarding contract;
apply BRG-01 and resolve onboarding tiers in order:
`fresh_bootstrap`, `resume_same_scope`, `recenter` (fallback to
`fresh_bootstrap`). Load the configured `always_read` set, expand
`read_on_demand` only when needed, and emit
`bootstrap_path`, `resume_basis`, and `reads_applied`. Resolve one active
artifact and repository; with no changes report nothing to close; with multiple
active artifacts ask which one. A content defect routes to `/work`. A changed
authority, scope, policy, cost, tree, or stale-context condition emits `PARK`
with the owner and exact resume point.

For run-family changes, load the identity/composition specs and registry on
demand. Confirm registry/graph parity, generated-view non-authority, exact
run-instance lock/receipt linkage, and a validation receipt or approved
disposition for every affected consumer. Missing fan-out evidence blocks closeout.

### Run-Family Graph Hook

When closeout scope creates, changes, resolves, or migrates a runprogram,
runbundle, or runbook, load the identity/composition specs and generated
registry on demand. Verify affected consumers and retain a validation receipt or
operator-approved disposition for each one. Generated registry and graph views
are evidence only and never grant write authority.

## Steps

### Closeout evidence preflight

Before the archive decision, update the active status and checkpoint notes, harvest
the scratchpad with its placement checklist, and reconcile `durable_outputs` to
the frozen scope. Record the workbook boundary and closeout scope manifest before
presenting the approval rows. These are executable closeout checks, not optional
background notes. Pass status/checkpoint review only when the selected context has
an updated status note naming the evidence and remaining gate. Pass scratchpad
harvest only when every keeper is promoted, retained, or assigned an explicitly
approved follow-on; each stabilized lesson has a placement record containing the
stable rule, canonical target, enforcement target, documentation target, owner,
validation, follow-on state, and verified target path/section/version. Pass the
`durable_outputs` check only when every row is `promoted`, `retained`, or has an
explicitly approved follow-on disposition; an unresolved row blocks closeout.

These preflight updates are records-only: write them to the active workbook
Execution Notes or existing workbundle state surface, not to selected content or
the governed target. They do not authorize staging, archive movement, commit,
push, PR, or merge. If no permitted state surface exists, stop and route the
record update to `/work`.

### Repository and Validation Preflight

Resolve `target_repo` from explicit scope, the active artifact, or the configured
work-repo list; run `git -C <repo> rev-parse --show-toplevel` and record
`repo_root`, `git_root`, and `safe_directory_applied: false`. All later Git
commands use that root. A detached `HEAD` stops publication; a shallow clone is
reported; signed-commit configuration requires a usable signing key. On Windows
record `core.longpaths` and the longest changed path; when long paths are
disabled/unset, a changed path at or above 240 characters reports
`longpath_risk` and stops. Permission or ambiguous Git metadata errors are not
clean results. If Git reports `dubious ownership`, stop for an operator-directed
trust repair; never run `git config --global`, and record
`safe_directory_applied: false`.

In direct ai_ops mode, validate `.ai_ops/local/config.yaml` with
`00_Admin/scripts/op_validate_config.py` before running its
`savepoint_validation.minimum_commands`. In governed mode, run
`python 00_Admin/scripts/run_governed_repo_quality_gate.py --repo-root <repo_root>
-workspace-root <workspace_root>`; it resolves the target registration,
validates the configured argv arrays, uses the trusted interpreter with
`shell=False`, and executes with the selected repo as `cwd`. The target may be
named as `<governed_repo>` from the workspace root or passed as an absolute path; do
not require the caller to be inside `ai_ops`. A target with no configured
minimum commands reports `validation: unavailable`, not pass. Retry a
configured network-sensitive command once, then record a permitted partial
result and `validation_escalated: true`; never silently skip a required check.

### Publication Route and Finalization Preflight

Before staging or requesting publication approval, resolve the publication route
from the provider and local repository state. Record `publication_route`
(`direct` or `pr_required`), the protected/default branch, required status checks,
the allowed merge methods, the selected remote, and `hook_runtime`. Do not probe
a protected branch with a direct push. Provider protection is `unknown` when
`gh` is unauthenticated or provider metadata is unavailable; unknown protection
selects the conservative `pr_required` route and must not be converted into a
direct push. Use the GitHub provider/connector or another authenticated
provider surface for branch-protection evidence; `gh` is not the only source
and its authentication failure is not proof that the branch is unprotected.
If provider metadata or the hook runtime cannot be verified, emit `PARK` with
the exact missing evidence and stop before mutation. When `pr_required` is
reported, create or select the publication branch before staging and bind its
head, base, and merge method to the packet and approval rows.

Publication preflight is an evidence record, not a prose assertion:
`build_closeout_packet.py --publication-preflight <path>` requires the route,
base/head, required checks, merge method, remote, and verified pre-commit and
commit-msg runtime evidence, and the approval packet schema binds that record
to the projected tree.

On Windows, if Git's MSYS hook launcher fails with the specific
`NtCreateDirectoryObject` error, the packet applier may retry the repository's
native `pre-commit` framework for both pre-commit and commit-message stages.
The retry preserves the staged index, uses the repository-local pre-commit
cache when no cache is configured, records the fallback in the packet result,
and never uses `--no-verify`; any other hook failure remains a hard stop. Before
running hooks, record the selected `PRE_COMMIT_HOME` and `pre-commit --version`.
To force a known cache, set `AI_OPS_PRE_COMMIT_HOME` before packet application;
the applier derives the effective `PRE_COMMIT_HOME` from that approved value.
Do not rely on an inherited `PRE_COMMIT_HOME` from the desktop session. Use
the cache selected by the target repository's local policy or the shared
workspace cache only when it is writable and within an operator-owned workspace,
user-profile, repository, or temporary root; do not silently reuse a
provider-specific cache. For remote-hook repositories, a cold-cache install is
permitted only after a read-only cache-path and runtime diagnostic; a
nodeenv/bootstrap failure is a hard hook failure, not a reason to skip hooks.
Record the effective cache path, whether it was warm, and the exact recovery
command if a retry was needed.

Run the canonical release-quality gate before publication approval when the
selected repository is `ai_ops`:
`python 00_Admin/scripts/run_release_quality_gate.py`. For another governed
repository, the target-repository gate above is the applicable quality route;
the ai_ops release gate is not silently substituted. Its lint result is the
CI-parity precondition for ai_ops, while a governed-target gate reports the
registered repository-native minimum checks. A failed or unavailable required
quality gate routes to `/work` and no commit or push is authorized.

Freeze the final records surface before security admission. This includes the
run log, future-work registry/scorecard, archive map, receipt references, and
generated views in the selected include set. Do not append clerical records or
repair receipt text after the receipt is admitted. When relocation is
applicable, the existing archive-gate receipt is the finalization proof: every
entry binds `source`, `destination`, `source_sha256`, and `destination_sha256`,
and the receipt proves `source_absent: true`, `collision_free: true`, and the
manifest hash. For future-work completion receipts, run
`complete_future_work.py --verify` after relocation and before packet
admission; it proves registry/receipt consistency, while the archive-gate
receipt proves source/destination bytes, source absence, and collision safety.
Never hand-edit a receipt to repair a moved path. Preserve the
receipt's reviewer references exactly. Re-running the pre-pass with the same
HEAD, source, bytes, and scope preserves passing reviewer attestations and
emits a baseline-bound delta packet for unchanged large text rows; it does not
erase the filled receipt. Changed bytes or changed scope invalidate only the
affected attestation and require review of that changed row. Use
`record_closeout_security_review.py --receipt <receipt> --updates-file <yaml>`
to apply reviewer records. An independent reviewer supplies a manifest with
`independent_reviewer` and one digest/mode/disposition/notes row per T2 file,
then runs `emit_closeout_security_snapshot.py --receipt <receipt>
--evidence-file <yaml> --output <snapshot>`; the emitter only validates and
serializes that evidence. Attach it with
`record_closeout_security_review.py --snapshot <snapshot>`; neither tool
manufactures independent evidence. Do not hand-edit receipt YAML. Any changed evidence
requires a new review and a new packet binding. If the archive gate or receipt verification
cannot produce a bound result, report `receipt_finalization: unavailable` and
stop.

The independent manifest is intentionally small and must be authored by the
independent reviewer, for example:

```yaml
independent_reviewer: Sol
rows:
  - path: <repo-relative-file>
    sha256: <receipt-bound-sha256>
    mode: "100644"
    reviewer: Sol
    disposition: pass
    review_notes: <what was independently checked>
```

## Future-Work Applicability Gate

Ordinary closeout defaults to `future_work: not_applicable` without invoking a
classifier. Do not load completion logic, regenerate a scorecard, prepare a
receipt, or prune a registry in that state. During preparation the operator may
request an explicit read-only residual-work review; record candidates and their
proposed handling, but do not mutate the registry. A referenced title, review,
stale packet, or dependency does not promote applicability.

The four states remain the contract for explicit flows:

| State | Binding | Allowed behavior |
| --- | --- | --- |
| `not_applicable` | No completion transaction | Report only; no completion or registry mutation. |
| `linked_only` | Explicit unfinished ID(s) | Read dependency context only; no receipt or mutation. |
| `completion_handoff` | One exact ID, completed state, ready-for-receipt state, artifact set | Run that receipt handoff only; keep the registry row. |
| `registry_sync` | One exact ID, artifact set, verified success receipt | Run the exact receipt-backed registry/scorecard/run-log sync and verify ID/HEAD parity. |

Missing or ambiguous IDs, artifacts, receipts, or bindings stop the explicit
flow. Failed, pending, or stale outcomes preserve the registry. Applicability,
projected validation, security admission, and publication approval are separate
user-facing fields. The `closeout_applicability.py` classifier and `complete_future_work.py` remain for
explicit registry flows and are not ordinary closeout prerequisites.

For a successful `complete_future_work.py` transaction, the exact completion
workbook is intentionally mandatory in the artifact set. This binds the
registry deletion and receipt to the control document rather than allowing a
supporting evidence file to close the registry item alone. The generated
scorecard is written with one final newline to satisfy Markdown consumers.

An explicit applicability flow exists only when the operator selects one of the
four states in the preparation record; a title, dependency, or referenced ID is
not a selection. In this contract, a `completion transaction` is the exact
receipt-backed completion operation; `ready-for-receipt state` means the selected
ID is complete and its artifact set is frozen; `receipt handoff` means running
that one completion receipt; and `artifact set` means the exact bound paths and
HEAD used by the receipt. If receipt synchronization defers archiving, resume by
rechecking the final workbook state and rerunning the archive decision; do not
reuse a stale archive row or approval.

## Projected-Tree Validation Boundary

Keep these trees distinct:

1. `current HEAD`: committed baseline for policy, hook, and receipt binding;
2. `projected include tree`: `HEAD` plus only the frozen approved include set;
3. `dirty worktree`: every unrelated tracked change, excluded untracked path,
   ignored artifact, and other local state.

Before validators, run:

```text
python 00_Admin/scripts/closeout_scope.py --repo-root <repo> \
  --include <approved-path> [--validator-input <path> ...]
```

Record `include`, `related_scope_requires_confirmation`, `exclude`,
`ignored_unpublished`, `current_head`, `projected_include_tree`, and dirty
paths. Write a closeout scope manifest before validation and staging. Validators use the projected tree when their inputs permit it. If an
input intersects an excluded or ignored path, stop with
`excluded_scope_conflict`; never stage an excluded file to make a check pass.

Classify `include` as the exact operator-approved paths; classify
`related_scope_requires_confirmation` as required dependency paths not yet
approved; classify `exclude` as discovered paths intentionally outside scope;
and classify `ignored_unpublished` as ignored local paths outside publication.
A validator qualifies for projected-tree execution only when its command accepts
the selected repo root or scope manifest and does not read outside the frozen
manifest. Otherwise report `excluded_scope_conflict` and do not claim that the
dirty-worktree result validates the approved set.
If `related_scope_requires_confirmation` is non-empty, stop with
`scope_pending_confirmation`; obtain operator confirmation, reclassify the paths,
and regenerate the frozen manifest before any validator can report
`projected_tree_ready` or any publication row can be approved.

## Archive and Completion Boundary

Archive is closeout-only. Determine applicability after scope is frozen and
before packet construction. Prepare exact source/destination rows and present
them as the clerical archive row and first step of one combined approval plan.
Present those rows in the existing container-completion decision and do not move
anything before that decision is accepted. This is the closeout clerical gate,
not a second publication approval turn. Packet and projected-tree hashes are
bound after the approved move and stale-reference recheck, not invented before
those bytes exist; a post-move scope or hash change invalidates the plan and
requires a new approval.

- `archive_gate: not_applicable` when no completed artifact is selected for
  relocation and the include set has no tracked deletion under `90_Sandbox/`;
- otherwise, after the clerical archive row is approved, execute the exact move
  set to `99_Trash/` before packet construction and staging.

For each move record tracked state, ignore evidence, SHA-256, collision and
active-reference checks, retention class, approval, recovery owner, and cleanup
dependency. If a tracked source would become local-only under an ignored
destination, stop before moving it. A future-work receipt handoff defers the
archive decision until receipt synchronization and final workbook status.

In this workflow, the `existing container-completion decision` is the decision
that completes the selected workbook or containing workbundle; it is separate
from publication. A `clerical archive row` is the exact source/destination row
presented in that decision. A workbook is the execution-control document, a
workbundle is its containing artifact folder, and a workprogram is the parent
collection when one is named. `99_Trash/` is the recoverable archive/reference
destination, not a deletion instruction.

Archive completed work artifacts to `99_Trash/` when applicable, only after the
approved clerical move row. A completed
solitary workbook moves to Trash; a completed workbundle or workprogram moves
only after all child items are complete and the operator confirms. Partial
artifacts remain in place. Record `archive_gate: passed` only when every
selected source is absent from `90_Sandbox/`, present at the named recoverable
destination, and its cleanup manifest is complete with every move executed.
If a selected source remains, a destination or manifest is missing, or a move
is incomplete, report `archive_gate: unavailable` and do not stage, commit,
push, create/update a PR, or merge. This rule applies even when the files are
ignored. After a move, run stale-reference checks and repair only through
`/work`; update the required archive and approval evidence before validation.

For maintainer work, reconcile `durable_outputs`, run the workbook boundary
check, and use `canonical_promotion_manifest_template.md` and
`artifact_cleanup_manifest_template.md` when promotion or cleanup is in scope.
Any promoted artifact consumed later in the same batch needs a
`promote_forward_contract:` block with artifact path, evidence, rollback,
actor, authority, and manifest-sync state. Verify completion-claim parity,
promotion-record parity, the Level 3+ divergence audit, operator decision rows,
and the container-completion prompt before publication.

Completion-claim parity means claiming only the level actually closed; a
milestone closeout must not claim the whole program complete. Promotion-record
parity means writing one promotion record per promoted batch or artifact and
updating its required mirrors, or recording `record_pending` or
`mirrors_pending` with affected paths, owner, retry and checks. The Level 3+
divergence audit re-runs every prior crosscheck finding against current state,
not only the latest summary. These rules are defined by the cross-surface and
infrastructure validation specifications; touching `.ai_ops/workflows/**`
requires a pre-change baseline, post-change validation, and rollback evidence.

### Completion Scope Modes

Record `completion_scope` explicitly in the preparation record and final report:

- `item` completes only the selected workbook or artifact;
- `milestone` completes the selected, fully executed child set while its parent
  workbundle remains active;
- `container` completes the named workbundle or workprogram and may trigger its
  approved archive decision.

An `item` or `milestone` closeout never claims or archives the still-active
parent. Every durable-output row that remains in the active parent must be
`promoted`, `retained`, or an approved follow-on with `owner`, `next_action`,
`target`, `registry_id` when applicable, and a due date or trigger. This is the
documented partial closeout route; it replaces improvised follow-on
dispositions. `/work_savepoint` remains a checkpoint and cannot claim any of
these completion states.

## Security Admission

For an external governed repository, resolve the target closeout-security policy
and installed hook against target `HEAD` before selecting admission:

The policy file is the target's `00_Admin/configs/closeout_security_tiers.yaml`
at `HEAD`. Discover the effective hook directory directly with
`git rev-parse --git-path hooks`; this avoids a `git config` read that may be
blocked by a user deny rule. Any Git error or empty returned path is
`security_admission: unavailable`; never fall back to a guessed `.git/hooks`
path. A Git error reading the target policy, an installed hook, or its
dispatcher configuration also yields
`security_admission: unavailable`. Inspect the target `.pre-commit-config.yaml` for the
`validate_closeout_security_head.py` or `ai-ops-closeout-security` marker. For direct ai_ops mode, “ai_ops itself” means
the selected ai_ops repository and the same HEAD-bound policy and hook checks.

- if either exists, use reviewer-read admission;
- if both are absent, deterministic admission is eligible only when active
  ai_ops policy explicitly allows `policy_source=missing_target_policy`;
- otherwise report `PARK` with `security_admission: unavailable`, reference
  `fw_20261026_01`, and stop before staging or publication.

ai_ops itself remains reviewer-read against its target `HEAD` policy and hook.
Follow `00_Admin/runbooks/rb_closeout_security_review_01.md` for the security
prepass, per-packet sizing, baseline/delta review route, receipt,
`Closeout-Security` trailer, and first-landing procedure. A receipt-sync-only
commit still requires a new HEAD-bound receipt. The baseline/delta route may
reduce re-reading within one HEAD for receipt/log/registry surfaces, but it is
not a cross-commit shortcut and cannot cover changed code, policy, workflow,
or hook bytes. Record
`admission_mode`, `policy_source`, receipt path, and disposition. A
manual waiver, skip, or unrecorded bypass is not an admission result.

## Publication Command Registry

Preparation may describe commands; mutation requires the approval rows below.

| Action | Fixed form | Gate |
| --- | --- | --- |
| stage | `git -C <repo> add -- <approved include paths>` | scope manifest and approval |
| commit | `git -C <repo> commit -m <approved summary>` | commit row naming exact include set |
| push | `git -C <repo> push <approved remote> <approved branch>` | push row naming packet-bound commit |
| create/update PR | GitHub provider action | PR/merge row |
| merge PR | provider action with approved PR, head, base, and method | merge row |
| packet retention | `python 00_Admin/scripts/prune_closeout_packets.py --repo-root <repo_root> --keep-run-id <final_run_id> [--apply]` | final merge verification and retention row |

Use argument arrays; reject shell metacharacters, reparse paths, detached heads,
force/delete options, `--no-verify`, and commands outside the selected repo.

## Packet and Approval Flow

When packet tooling exists, build one packet after the approved archive move,
stale-reference updates, projected-tree validation, and security admission with
`build_closeout_packet.py`. It writes only to the configured machine-local packet
root and records the archive result. Then issue one publication approval turn
with separate commit, push, PR, and merge rows. Bind its run ID, packet digest,
HEAD, branch, include-set hash, mutation-plan hash, projected-tree hash, cost
result, security disposition, and archive receipt to that turn. The clerical
archive row was decided before packet construction in the existing
container-completion decision and is not repeated. Any changed bound value
requires a new approval.
Each publication row names its exact scope or remote state; none implies
another. The approval file must bind the packet/tree hashes, HEAD, branch,
include set, mutation plan, projected tree, and archive receipt using the
approval schema. Apply only through `apply_closeout_packet.py`; it must recheck the
receipt, cost, policy, index, staged blobs, hooks, and post-commit tree.

If packet preparation/application fails, preserve the packet and use the manual
fallback only with the same exact include set and approval. Before manual staging,
rerun `closeout_scope.py` for the frozen projection and run
`closeout_security_prepass.py` to create the HEAD-bound receipt. Stage only the
exact approved include set; then run
`validate_closeout_security_receipt.py --gate --staged` against the staged blobs
and let the installed `validate_closeout_security_head.py` and commit-message
hook validate the same staged state before commit. If any step cannot produce a bound result, report
`security_admission: unavailable` and stop. A missing target policy or hook is
never repaired by this fallback; a first landing of either is a separate
governed change with a new admission. Never broaden scope, use broad staging, or
bypass hooks.

The fallback is a new approval binding whenever the rerun changes the receipt,
projected-tree, packet, scope, or security hashes. Stop before staging, present
the changed values, and obtain a new approval turn; only unchanged exact bindings
may reuse the prior approval.

For an ordinary reviewer-read receipt, use the supplied
`record_closeout_security_review.py` tool for reviewer disposition updates and
the T2 snapshot attachment. Use
`emit_closeout_security_snapshot.py` to serialize the independent reviewer's
manifest; its digest/mode checks prevent a stale or mismatched snapshot from
being attached. The update schema rejects out-of-scope paths and unknown
fields, and the pre-pass preserves matching attestations across record-only
reruns. This is the supported packet route for governed repositories; raw
receipt or snapshot YAML construction is not required.

## Closeout Packet Retention

Closeout packets are run-scoped verification evidence, not durable work
artifacts. Preserve every packet while the closeout is active so failed or
interrupted attempts remain diagnosable. After the final PR merge is verified,
identify the final successful packet by its run ID and run the retention sweep
in read-only mode:

```text
python 00_Admin/scripts/prune_closeout_packets.py \
  --repo-root <repo_root> --keep-run-id <final_run_id>
```

Review the plan, then add `--apply` to archive terminal non-final packets to
`99_Trash/closeout_packets/<repo_id>/<run_id>/`. The sweep preserves the
operator-selected final `APPLIED` packet, all `PENDING` and `APPROVED` packets,
malformed packets, unknown states, and directories that contain only a
future-work completion receipt. It never deletes evidence and never follows a
reparse point. An active or malformed packet requires explicit later
disposition; it is not silently pruned. If the sweep cannot complete, report
`packet_retention: unavailable` and retain the source packet root.

The final closeout report records `packet_retention` with the selected run ID,
planned/archive counts, protected active or unsafe counts, and every archive
destination. A packet retention sweep does not widen the publication include
set and does not change the already-verified commit, push, or merge result.

After packet retention, inspect the workspace temporary area named by the
repository policy (normally `C:\RE_Projects\tmp`). Delete or archive only
identified temporary outputs whose retention purpose has expired; retain files
explicitly referenced by an active packet, receipt, cache, or recovery plan.
Record the cleanup result in the final report. A stale temporary file is not a
durable work artifact and must not silently become part of a closeout include
set.

## Outputs

Commit only after required checks pass, the archive result is `passed` when
applicable or `not_applicable` otherwise, and the commit row is approved. Push
only after the push row is approved and the packet-bound commit, remote, and
branch are reverified. Create/update and merge only after the merge row is
approved; re-read the remote head and required checks, and report an unmerged PR
as pending rather than inferring completion. Do not force-push or change merge
method. After approval, rerun status and the safety preflight; stop if the
branch, remote, HEAD, include-set content, or dirty-tree scope changed. If a
push fails, preserve the local commit and report its exact hash, remote and
branch; emit `push_escalation: pr_required` for a protected-branch or remote
rejection, `push_escalation: auth_failure` for authentication, and never create
a PR, merge, retry with a wider command, or change the remote automatically.
The manual fallback must verify the resulting commit SHA, parent, tree, and
message before any push.

For `completion_handoff`, verify the first commit's HEAD binding, run
`complete_future_work.py` once for the exact ID and artifact set, verify its
receipt, then finalize workbook/registry/scorecard/run-log surfaces in a second
exact packet and approval. No registry row is deleted manually or from a log
mention. Run `complete_future_work.py --verify` before any archive or harvest
move of files cited in the receipt.

After publication completes and the final receipt exists, set the exact active
artifact to `completed` with `update_artifact_status.py --id <id> --status
completed --note "<receipt reference>"`, then run
`python 00_Admin/scripts/update_artifact_status.py --check --id <id>`; stop on a non-zero
exit and report it. Only then run `update_artifact_status.py --id <id> --remove`.
The removal command refuses `planned`, `stub`, or `active` entries and accepts
only `completed` or `deprecated`; exit 1 means the entry is already absent:
report it and continue; exit 2 means an ambiguous ID, ineligible status, or
another error: stop and report. A merge that lands after the session is handled
by the resumed closeout.

Report `target_repo`, `repo_root`, branch, HEAD, `publication_route`,
required checks, merge method, `hook_runtime`, `receipt_finalization`, scope buckets,
`future_work`, `projected_include_tree`, `excluded_scope_conflict` when present,
security admission fields, archive result, validation commands, approval state,
commit/push/PR/merge status, `packet_retention`, and all receipt paths. Keep work summaries and
active-state claims synchronized. Generated views remain non-authoritative.

## Review Capacity Boundary

Apply the `/crosscheck` Loop Control contract for review tiers and `PARK`;
closeout does not reset counters or authorize a new commit. There is no
aggregate token closeout ceiling. The pre-pass reports per-packet cost,
reuses passing attestations for unchanged large rows through a bound delta
packet, and requires a new full review only for changed bytes, scope, policy,
workflow, or hook surfaces. Closeout uses one final commit after the frozen
set; no commit is created merely to bypass review capacity.

## Validation and Limits

Run configured checks, linters, focused contract tests, and the full repository
regression suite once after final edits and before publication.
Do not repeat the full suite for every intermediate edit when focused checks are unchanged. A
failed required check, unresolved candidate, stale scope lock, hash drift,
unsupported admission mode, unresolved decision row, or cross-surface mismatch
stops closeout and routes remediation to `/work`.

## Resources

Read in this order: `00_Admin/configs/context_routing.yaml`; the applicable
direct/governed mode spec; `rb_commit_push_streamlining_01.md` for publication
sequencing; `rb_closeout_security_review_01.md` for security admission;
`policy_git_workflow_conventions.md` for Git rules;
`spec_cross_surface_coordination.md` and
`spec_infrastructure_change_validation_gate.md` for cross-surface and
validation gates; then the packet schemas. Each reference is authoritative only
for the contract named by its title; generated views are evidence, not authority.

## Lane

Default lane: Executor, with Linter for validation and Reviewer at the
crosscheck boundary.

## Risks and Limits

Closeout is fast but scope errors are costly. Never change scope, delete scratch
content, force-push, skip linters, or treat a prior approval, workflow metadata,
or turbo marker as a current mutation approval.
