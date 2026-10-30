---
description: Prepare a read-only closeout packet, then publish through exact approval-gated commit, push, and PR-merge steps.
name: closeout
kind: workflow
version: 0.8.1
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
    short-description: Prepare a read-only closeout packet, then publish through one structured approval turn covering clerical work, commit, push, and PR merge.
  interface:
    display_name: closeout
    short_description: Prepare a read-only closeout packet, then publish through one structured approval turn covering clerical work, commit, push, and PR merge.
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

Prepare a closeout without mutation, then publish only after the exact commit,
push, and final PR merge gates pass when a PR flow is required. When completed
workbook/workbundle artifacts are selected for relocation, they must be moved
from `90_Sandbox/` to a recoverable `99_Trash/` destination first; an ordinary
scoped closeout records `archive_gate: not_applicable` instead of inventing an
archive operation. Read-only preparation must not stage, commit, push,
create/update a PR, merge, archive, delete, or repair content. Content
remediation routes to `/work`.

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

### Run-Family Graph Hook

For run-family changes, load the identity/composition specs and generated
registry on demand. Closeout MUST confirm registry and graph parity, generated-
view non-authority, exact run-instance lock/receipt linkage, and a validation
receipt or operator-approved disposition for every affected declared consumer.
Missing fan-out evidence blocks completion and returns the lane to `/work`.

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

### Read-only Preparation Boundary

The first closeout leg is deterministic and read-only. Resolve the active
artifact and repository, capture the complete dirty-tree baseline, classify
`include`, `related_scope_requires_confirmation`, `exclude`, and
`ignored_unpublished`, run configured validation and the applicable security
pre-pass, and project the proposed mutation plan, commit message, remote, and
branch, proposed PR/merge method when a PR flow is required, and the exact
clerical operations in scope. Emit
`bootstrap_path`, `resume_basis`, `reads_applied`, the scope echo, validation
results, and security applicability. Do not stage, write a receipt to the
repository, archive, delete, fix content, commit, push, create/update a PR, or
merge during this leg.

If preparation finds a content defect, return to `/work`. If it finds a cost,
authority, policy, scope, tree, or stale-context change, emit `PARK` with the
owner and exact resume point. A security outcome of `deterministic_admission`
is not a `pass`; it is permitted only for a governed repository whose target
policy or hook is absent and must be presented in the combined approval turn's
commit row.
For an external governed repository, resolve the target repository's policy and
installed hook before selecting the admission mode. If either is present, use
reviewer-read admission against the target `HEAD`; deterministic admission is
not applicable. If both are absent, deterministic admission is eligible only
when the active ai_ops policy explicitly allows `policy_source=missing_target_policy`.
If that allowance is absent or disabled, emit `PARK` with
`security_admission: unavailable` and reference `fw_20261026_01`; do not use a
manual waiver, skip, or unrecorded bypass. Record the selected
`admission_mode`, `policy_source`, receipt path, and overall disposition in the
closeout packet. ai_ops itself remains reviewer-read against the target `HEAD`
policy and installed hook contract.

`/work_savepoint` is the WIP lane: its default invocation validates and records
a checkpoint only. It does not claim completion, archive authority, commit, or
push. Its `--commit` option is an explicit publication request and uses the
same structured approval turn covering clerical work, commit, push, and
optional PR merge; a savepoint that
stops before merge must report the PR as unmerged and remain active.

### Future-Work Applicability Gate

Classify future-work applicability before reading completion schemas, importing
`complete_future_work.py`, regenerating a scorecard, preparing a receipt, or
pruning a registry. Use the side-effect-free classifier:

```text
python 00_Admin/scripts/closeout_applicability.py --intent not_applicable
```

An ordinary scoped closeout MUST default to `not_applicable`. A registry title,
review mention, stale packet, or dependency reference MUST NOT promote that
state. The classifier's result is user-facing closeout evidence and controls
the allowed downstream actions:

| State | Required binding | Allowed behavior |
| --- | --- | --- |
| `not_applicable` | No completion transaction | Do not load completion logic, regenerate the scorecard, or mutate/prune the registry. Emit `future_work: not_applicable`. |
| `linked_only` | One or more explicitly linked unfinished IDs | Read dependency context only. Do not prepare a receipt, regenerate the scorecard, or mutate the registry. |
| `completion_handoff` | Exactly one registry ID, `execution_status: completed`, `completion_state: ready_for_receipt`, and a non-empty artifact set | Run the receipt handoff for that ID only. Do not delete the registry row in this phase. |
| `registry_sync` | Exactly one registry ID, non-empty artifact set, and a verified success receipt | Run only the exact receipt-backed registry/scorecard/run-log synchronization transaction, then verify ID and HEAD parity. |

For `completion_handoff` and `registry_sync`, a missing ID, ambiguous artifact
set, stale receipt, or failed receipt is a stop condition. Failed, pending, or
stale outcomes preserve the registry entry. Applicability is independent from
security admission and projected-tree validation; report each result separately.

### Projected-Tree Validation Boundary

Closeout MUST keep these trees distinct:

1. `current HEAD`: the committed baseline used for policy, hook, and receipt
   binding;
2. `projected include tree`: `HEAD` plus only the frozen approved include set;
3. `dirty worktree`: every unrelated tracked change, excluded untracked path,
   ignored artifact, and other local state.

Before configured validators run, produce the read-only scope report:

```text
python 00_Admin/scripts/closeout_scope.py --repo-root <repo> \
  --include <approved-path> [--validator-input <path> ...]
```

The report MUST identify `include`,
`related_scope_requires_confirmation`, `exclude`, and `ignored_unpublished`.
Validators run against the projected include tree when their inputs permit it.
If a validator input intersects an excluded or ignored path, stop with
`excluded_scope_conflict`, identify the path and owning scope, and do not stage
the excluded file. A dirty worktree is not evidence that the approved include
set failed. The packet builder preserves excluded nonignored paths in its
scope manifest; it never widens the include set to make validation pass.

### Publication Command Registry

Closeout may describe publication commands during a dry run, but it may
execute them only after the explicit approval and scope gates below pass:

| Action | Fixed form | Required gate |
| --- | --- | --- |
| stage | `git -C <repo> add -- <approved include paths>` | scope manifest and current-turn approval |
| commit | `git -C <repo> commit -m <approved summary>` | combined approval turn's commit row naming the include set |
| push | `git -C <repo> push <approved remote> <approved branch>` | combined approval turn's push row |
| create/update PR | GitHub provider action for the approved repository, head, and base | combined approval turn's PR/merge row |
| merge PR | GitHub provider action with the approved PR, expected head SHA, and method (`squash` preferred when approved) | combined approval turn's merge row |

### Tree-Bound Approval Packet Route

When the target is `ai_ops` or another repository with the packet scripts
available, use the packet route to reduce repeated scope reconstruction:

1. During read-only preparation, run
   `python 00_Admin/scripts/build_closeout_packet.py --repo-root <repo> --include
   <approved-path> --message <approved-summary>` once for the complete include
   set. The builder writes only to the machine-local packet root
   `90_Sandbox/ai_workbooks/_closeout_packets/<repo>/<run_id>/` and never stages,
   commits, pushes, or edits target content. If the include set contains a
   tracked deletion under `90_Sandbox/`, pass `--archive-gate <repo-contained
   receipt>`. Otherwise the builder records `archive_gate: not_applicable`
   automatically; do not manufacture an archive receipt for an ordinary
   scoped closeout.
2. Present the packet's `run_id`, `prepared_packet_sha256`, HEAD, branch,
   include-set hash, mutation-plan hash, projected tree hash, and cost result
   for approval. A
   `PARKED` packet stops until its named limit is resolved; it cannot be
   widened silently.
3. After the combined approval turn approves the commit row, the operator writes an approval file with
   `decision: approve`, a non-placeholder `approved_by`, `approved_at`, and
   `approval_ref`, bound to the exact run ID, prepared packet hash, HEAD,
   branch, include-set hash, mutation-plan hash, and projected-tree hash using
   `00_Admin/configs/validator/schema_closeout_approval.yaml`, then run
   `python 00_Admin/scripts/apply_closeout_packet.py --packet <packet> --approval-file <approval-file>`.
   The applier stages only the packet paths, commits with `git commit --only`,
   rechecks the packet digest, independently recomputed cost stop, routing
   contract, full index fingerprint, staged blob/mode entries, runs the frozen
   pre-commit hook as a preflight, and verifies the resulting
   `HEAD^{tree}`, commit parent/message, and included worktree bytes.
4. A divergence, hook change, policy change, index change, or failed commit
   preserves or fails the packet and makes it not push-ready. Before any push,
   run `python 00_Admin/scripts/apply_closeout_packet.py --verify-push
   --packet <packet>` and include the returned commit SHA, remote, and branch
   in the combined approval turn's push row.

Resolve the repository, remote, branch, and include paths before invocation.
Reject shell metacharacters, force/delete options, any `--no-verify`, reparse paths,
detached heads, and any command assembled from free-form workflow text. The fixed
packet applier runs the frozen pre-commit hook against an isolated approved-scope
index and then against the actual staged index immediately before commit. It
uses the installed native hook path for the ordinary commit after the isolated
and real-index preflights; pre-commit and commit-msg remain enforced at the
commit boundary. A disposable-clone dry run against the real ai_ops shims
passed on 2026-10-23 after supplying the ignored generated wrapper outputs
that the export-drift hook requires. The applier also verifies the resulting
tree/worktree, so a late hook or post-commit drift fails closed and is not
push-ready.
A closeout state, hook, or generated wrapper cannot substitute for the operator approval.
The packet route is one approved script invocation, but host permission prompts are
platform-dependent: the workflow makes no allowlist or prompt-reduction claim. If the
host still prompts, continue with the same explicit approval boundary or stop and use
the documented manual closeout path; do not broaden settings or change command forms
implicitly. The packet route requires the target repository's
`00_Admin/configs/context_routing.yaml` to contain the `closeout_packet`
contract, and the packet and approval files must remain inside that target
repository's configured packet root.
The packet's HEAD-bound policy snapshot is a cheap change tripwire; the exact
HEAD binding remains the authoritative base-repository check.

### Manual Closeout Fallback

Use this path only when packet preparation or application fails and the exact
approved scope is still known. Preserve the failed packet and its evidence;
do not widen the scope or use `--no-verify`.

1. Re-read the failed packet's `include` set and verify the current branch,
   HEAD, remote and dirty-tree boundary. Unstage only paths from the approved
   set if cleanup is required.
2. Run the required validators, then stage only the approved paths with
   `git -C <repo> add -- <approved paths>` and verify that
   `git -C <repo> diff --cached --name-only` is exactly that set.
3. With the combined approval turn's approved commit row, create one exact commit using the approved
   normalized message. Do not use broad staging, `--no-verify`, force options,
   or a new free-form command shape.
4. Verify the new commit's SHA, parent, tree, message, worktree bytes and
   unrelated index projection. The combined approval turn's push row names that
   SHA, remote, and branch.

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
6. If a workbundle README contains a `durable_outputs` register, reconcile
   every row against current files before continuing. No row may remain
   unresolved (`promoted`, `retained`, or an explicitly approved follow-on
   disposition is required) before archival or closeout.
7. When promotion or pruning is in scope, require the applicable templates:
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
8. Run workbook boundary check before validation/commit:
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
   - run `closeout_scope.py` before validators and record the separate
     `ignored_unpublished` bucket plus the `current_head`,
     `projected_include_tree`, and dirty-worktree paths
   - if a validator input intersects an excluded or ignored path, stop with
     `excluded_scope_conflict`; identify the path and owner and do not stage it
   - validators must bind to the projected include tree when supported; a
     validator result from the full dirty worktree is not a projected-tree pass
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

9. Verify completion-claim parity before status changes:
   - claim only the level actually closed (task, workbook, milestone,
     workbundle, workprogram, or program)
   - do not write a program-complete claim from a milestone closeout unless a
     program-closeout lane ran
   - synchronize required mirror surfaces in the same pass or mark the mirror
     debt as pending with owner and next surface

10. Verify promotion-record parity when canonical promotion occurred:
   write a promotion record for each promoted batch/artifact, update the
   required mirror set in the same leg, and if incomplete record
   `record_pending` or `mirrors_pending` with affected paths, owner, and retry
   surface.

11. Freeze `future_work` applicability before any registry-specific action.
    For `not_applicable`, do not load completion logic, build a future-work
    receipt, regenerate the scorecard, or prune the registry. For `linked_only`,
    read dependency context only. Continue to the receipt handoff below only
    for `completion_handoff` or `registry_sync` returned by
    `closeout_applicability.py` with the required exact binding.
12. If a future-work item is being completed, prepare the execution workbook
    for the receipt handoff before the first publication commit. The workbook
    may remain `status: active` only when it has
    `execution_status: completed` and
    `completion_state: ready_for_receipt`, with a matching
    `checklist_allowance.kind: forward_handoff` for the receipt/finalization
    items. Do not run the success completion command in this pre-commit leg:
    its HEAD-binding check must see the registry binding in an already-created
    commit. Failed, pending, and stale receipts preserve the registry entry.
    For registry edits outside the completion command, regenerate the scorecard
    with `python ai_ops/00_Admin/scripts/generate_future_work_scorecard.py`.

13. Run configured validation checks in this order:
   repo-defined validators/checks from the active closeout contract, then
   configured linters (markdownlint, yamllint, ruff, pre-commit) if present.
   When local work artifacts under ignored `90_Sandbox/**` or `99_Trash/**`
   paths are in scope, run equivalent direct lint via temp copy, stdin, or an
   explicit ignore override and record the strategy in closeout evidence.
   For ai_ops-owned workflow, packet, or validator changes, run the focused
   contract tests during iteration, then run the full repository regression
   suite once after the final edits and before publication. The full suite is
   a broad regression gate for routing, packet application, validators,
   generated surfaces, future-work receipts, and release quality; its test
   count is inventory, not a required number to reproduce in every savepoint.
   Do not repeat the full suite for every intermediate edit when focused tests
   and configured checks are unchanged.

14. For Level 3+ completed workbooks, run a divergence audit before commit:
    compare the latest crosscheck, current output state, and later review
    artifacts. Re-run every prior crosscheck finding against current state, not
    only the latest summary. If acceptance was overturned, return to `/work`,
    resolve the defect, and rerun completion crosscheck.
15. Verify every operator decision row has decision, rationale, date, and actor;
    pending rows block closeout and convergence claims.
16. **Container completion check (Workbundle/Workprogram):**

    - **If inside a Workbundle:**
      - Check if all workbooks in the workbundle are `completed`.
      - If yes, prompt: "All workbooks in this workbundle are complete. Archive the entire workbundle to 99_Trash?"
      - If no, report which workbooks remain incomplete.
    - **If inside a Workprogram:**
      - Check if all child workbundles/workbooks are `completed` or `archived`.
      - If yes, prompt: "All items in this workprogram are complete. Archive the entire workprogram to 99_Trash?"

### Archive Applicability Boundary

17. Determine archive applicability before staging and establish the archive
    publication gate only when applicable:
    - The ordinary scoped closeout default is `archive_gate: not_applicable`.
      It applies when the frozen include set has no tracked deletion under
      `90_Sandbox/` and no completed `90_Sandbox/` artifact is selected for
      relocation. In this state, do not load completion/cleanup logic, prompt
      for an archive move, regenerate a registry scorecard, or block closeout
      on an unrelated dirty sandbox path.
    - If a completed `90_Sandbox/` artifact is selected for relocation, or the
      approved include set contains a tracked `90_Sandbox/` deletion, archive
      applicability is required. The packet must bind a passed archive receipt
      and the exact tracked deletions; `--archive-gate-not-applicable` cannot
      waive this requirement.
    - Before any move, record each source's tracked state with
      `git ls-files --error-unmatch -- <path>`, ignore evidence with
      `git check-ignore -v -- <path>` (or `not_ignored`), source SHA-256,
      collision result, active-reference result, retention class, approval,
      recovery owner, and cleanup dependency in the cleanup manifest.
    - If a tracked source would become local-only under an ignored destination,
      PARK before moving it. The approved mutation plan must explicitly include
      the tracked deletion or a tracked archive destination; an ignored trash
      folder is not evidence of publication.
    - If a future-work receipt handoff is active, defer this archive decision
      until after the receipt-sync phase and final workbook status change. A
      workbook in `ready_for_receipt` handoff state remains active and must not
      be archived.
    - **Archive completed work artifacts to `99_Trash/` when applicable** before
      publication.
    - Completed solitary workbook → move to Trash
    - Completed workbundle (all workbooks complete, user confirmed) → move workbundle folder to Trash
    - Completed workprogram (all workbundles complete) → move workprogram folder to Trash
    - Partially complete artifacts → leave in place
    - Record `archive_gate: passed` only when every completed source selected for
      publication is absent from `90_Sandbox/`, present at the named recoverable
      `99_Trash/` destination, and its cleanup manifest is `status: completed`
      with every move row marked `executed`.
    - If a selected completed source remains under `90_Sandbox/`, the destination
      or manifest is missing, or the manifest is incomplete, stop with
      `archive_gate: unavailable`; do not stage, commit, push, create/update a
      PR, or merge. This gate applies even when the target repository has no
      tracked representation of the ignored workbook files. When the gate is
      not applicable, later publication gates consume the explicit
      `not_applicable` result instead of requiring a meaningless `passed` row.
18. After relocation/archive actions, run stale-reference checks on touched
    docs/indexes and fix or report broken references before staging.
19. Update approval/validation log evidence required by policy or the active
    workbook so the shipped commit contains the final archive paths and review
    gate traceability.
    Re-run the configured validation checks after all archive, stale-reference,
    and log mutations; the final security receipt is built only from that
    post-mutation state.
    When the closeout-security policy or validator itself is being upgraded,
    stage the canonical policy and validator together and run the explicit
    `--first-landing --config` gate against a separate first-landing receipt.
    The packet route validates the supplied reviewed receipt after staging and before
    the commit gate when invoked with `--first-landing-receipt
    <repo-contained path>`; the receipt must already exist and is never
    overwritten by the applier.
    Do not install that receipt at the hook's `latest.yaml` path and do not
    add a `Closeout-Security` trailer to this policy-upgrade commit: the
    unchanged trusted HEAD hook must see an ordinary commit and must never
    execute staged admission code. After the policy upgrade lands, regenerate
    the normal v0.2 receipt at `latest.yaml` for subsequent closeouts.
20. Run the closeout security admission gate only after `archive_gate: passed`
    when archive is applicable, or `archive_gate: not_applicable` otherwise:
    - Freeze the final include set after archive and stale-reference updates.
    - Run the configured security pre-pass, freeze its scope lock, and review
      every included row using its deterministic review basis. Full-content
      rows are read in full; deleted binary rows may use only the explicit
      hash-only deletion basis with hash-bound reference and recovery evidence
      artifacts; large deleted structured CSV/GeoJSON rows may use the
      policy-bound structural basis only with actual recovery, dependency,
      and affirmative frozen-scope approval evidence; live
      binary/generated rows require digest plus generator, parser, or render
      evidence. Use bounded review batches within both the configured
      per-session and total-receipt token caps; stop before reviewer admission
      when the total cap would be exceeded, then split the explicit include set
      or apply an eligible bounded structural basis. Record the reviewer
      packets and machine-local receipt. The default policy keeps reviewer
      packets at 20,000 estimated tokens and raises the aggregate
      session/receipt ceiling to 200,000; do not split a scope merely because
      it exceeds the retired 120,000 ceiling. Split only when the active cap,
      packet cap, evidence tier, or an unresolved candidate requires it.
    - Do not stage until the combined approval turn names the final include set
      in its commit row. After approval, stage only that set and run the receipt validator
      against staged blobs. A missing row, hash drift, stale scope lock,
      incomplete coverage, unresolved candidate, unsupported review-basis
      downgrade, or non-pass disposition blocks closeout.
    - Include the validated `Closeout-Security` result in the commit message;
      the installed pre-commit and commit-msg hooks recheck the staged bytes.
21. Evaluate commit gate explicitly:

    - If required configured checks exist, all must pass before commit.
    - The commit gate is ineligible unless the recorded archive result is
      `archive_gate: passed` when archive is applicable, or
      `archive_gate: not_applicable` when it is not. Approval cannot waive an
      incomplete or missing move to `99_Trash/`.
    - Require one explicit operator approval turn before mutation. The approval
      packet must list separate decision rows for all eligible clerical
      operations; the final `include` set and change summary/commit; push of
      the packet-bound commit, remote, and branch; and PR creation/update plus
      merge with the PR (or proposed head/base pair before PR creation), current
      head SHA, base branch, and merge method. Each row must be explicitly
      approved or declined; a single turn reduces interaction count but is not
      an unbounded blanket authorization.
    - Revalidate the bound scope, commit SHA, remote, branch, PR head, and
      required checks before each mutation. If any bound value changes, stop
      and request a new approval turn.
    - If no checks are configured, record that fact in the approval packet;
      absence of checks never relaxes the approval requirement.
    - If any required check fails, stop closeout and transition to `/work` for
      remediation.

22. If a tree-bound approval packet was prepared, use its applier after the
    commit gate. When the packet includes a closeout-security policy upgrade,
    pass `--first-landing-receipt` so the applier validates the supplied
    separate staged receipt before the commit gate. Otherwise stage the frozen
    include set and generate the commit message summary using the fixed
    commands above.
23. Commit only after the commit gate passed, the archive result is
    `archive_gate: passed` when required or `archive_gate: not_applicable`
    otherwise, and the operator approved the frozen include set and exact commit
    action. Turbo markers and workflow
    metadata never substitute for that approval. The packet applier's
    post-commit tree binding is required when the packet route is used.
24. When a future-work receipt handoff is in scope, verify the first commit's
    exact HEAD binding, then run `complete_future_work.py` once per registry ID
    with the receipt-ready workbook, exact artifact set, actor, and retained
    review references. Run `--verify` for every resulting receipt. Do not
    manually delete registry rows or infer completion from a log mention.
25. Finalize the workbook to `status: completed`, close the receipt-handoff
    checklist items, synchronize the registry/scorecard/run-log/workbook
    surfaces, and run the final validators. Build a second closeout packet for
    these receipt-sync/finalization changes and obtain a new exact commit
    approval before publishing the second commit. A failed receipt or failed
    final validation keeps the workbook active and preserves the registry row.
26. Push only after the combined approval turn's push row is approved, the
    archive gate remains `passed` when applicable or `not_applicable` otherwise,
    and the row names the packet-bound final
    commit, remote, and branch; record and verify the
    resulting SHA immediately before push. A failed push is reported
    and preserved; do not create a PR, merge, or broaden the push command
    automatically.
27. After the final push, execute the merge phase only when the combined
    approval turn's PR/merge row is approved and the archive gate remains
    `passed` when applicable or `not_applicable` otherwise. Re-read the remote
    head and PR state; create or update
    the approved PR if needed, verify the PR head still equals the approved
    commit, verify required checks/reviews are satisfied, and merge using the
    approved method (squash when selected). Do not fall back to another merge
    method or merge a changed head. If merge approval is absent or merge fails,
    report the pushed PR as pending/unmerged and preserve the closeout evidence.
28. Confirm closeout complete with summary of all commits, receipts, PR state,
    and merge result.

### External Repo (User)

1. Apply bootstrap guard BRG-01 before lane steps.
2. **Repo-Root Resolution**: Resolve the target repository root before any git operations.
   - Resolve `target_repo` from: explicit user scope → active artifact `repo` field → `.ai_ops/local/config.yaml` `workspace.work_repos` list.
   - **Explicit user scope**: an absolute path or workspace-relative path. Normalize to absolute path before passing to `git -C`.
   - **Unregistered repos**: if `target_repo` cannot be resolved, require explicit user-provided path. Stop and ask if none given.
   - **Windows**: normalize to forward-slash absolute path for all `git -C` calls.
   - Run `git -C <target_repo> rev-parse --show-toplevel` to confirm repo access and establish `repo_root`.
     - If it fails with `dubious ownership`, stop and request an explicit
       operator-directed trust repair. Do not run `git config --global` from
       the closeout lane. Record `safe_directory_applied: false`.
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
   - If `governed_mode: ai_ops`: first run `python <ai_ops_root>/00_Admin/scripts/op_validate_config.py <ai_ops_root>/.ai_ops/local/config.yaml` and stop if it fails. Treat each `minimum_commands` entry as a validated argv array, never a shell string; execute it sequentially with `shell=False`, `cwd=<repo_root>`, and no command interpolation. Use the same trusted Python runtime that passed validation; never re-resolve a bare executable through a changed `PATH`. Reject an entry containing shell metacharacters, an unapproved executable, or a path outside `<repo_root>` / the workspace.
     For commands in `network_sensitive_commands`: retry once on network/sandbox error; if still failing,
     record `validation_skipped_reason` and skip if `allow_partial_on_network_failure: true`.
     Record `validation_escalated: true` if any command was skipped.
   - If `governed_mode: repo_native`: detect repo-native linters (`.markdownlint.json`, `.yamllint`,
     pre-commit hooks) and run them. If none configured, offer to run common linters.
   - Record `validation_commands_run` in output.
7. Freeze future-work applicability before reading the target registry or
   completion surfaces. Ordinary scoped closeout emits
   `future_work: not_applicable` and does not load `complete_future_work.py`,
   regenerate the target scorecard, or prune a registry. Use `linked_only` for
   dependency context, `completion_handoff` for one exact receipt-ready ID and
   artifact set, and `registry_sync` only after a verified success receipt.
8. Run `closeout_scope.py` against the target repository and the frozen include
   set before configured validators. Preserve the separate
   `include`, `related_scope_requires_confirmation`, `exclude`, and
   `ignored_unpublished` buckets. Validators use the projected include tree;
   if a validator input intersects an excluded or ignored path, stop with
   `excluded_scope_conflict` rather than staging the path or reporting an
   include-set failure.
9. Resolve and run the closeout security admission gate on the explicit
   external-repo include manifest:
   - Inspect the target repository's closeout-security policy and installed
     hook. If either exists, use reviewer-read admission against target `HEAD`.
     If both are absent, use deterministic admission only when the active
     ai_ops policy explicitly allows `policy_source=missing_target_policy`;
     otherwise emit `PARK` with `security_admission: unavailable`, reference
     `fw_20261026_01`, and stop before staging or publication.
   - Freeze the scope lock, apply each row's deterministic review basis, run
     bounded review batches within the configured per-session and total-receipt
     caps, write the machine-local receipt, stage only the manifest paths, and
     validate the staged blobs. If the total cap is exceeded, stop and split the
     explicit manifest rather than silently creating more batches.
   - Missing coverage, hash drift, a stale scope lock, unresolved candidates,
     an unsupported admission mode, or a non-pass disposition blocks closeout.
     The receipt's `admission_mode`, `policy_source`, and overall disposition
     must be included in the combined approval turn; a manual waiver is not a
     substitute for a command-supported disposition.
10. Require `archive_gate: passed` before staging when archive is applicable;
    otherwise require the explicit `archive_gate: not_applicable` result. A
    completed selected source remaining under `90_Sandbox/`, a missing
    `99_Trash/` destination, or an incomplete cleanup manifest stops the
    external-repo lane before staging, commit, push, PR creation/update, or
    merge. Then stage changes and generate the commit message summary,
    including the validated `Closeout-Security` trailer result.
11. **Push Preflight** (if push is planned): verify `push_preflight_result` from Step 3 is `clean` or `shallow_clone`. If `detached_head`, stop before commit.
12. Commit only with `archive_gate: passed` when archive is applicable, or
    `archive_gate: not_applicable` otherwise, and the approved exact include
    set.
13. **Push and failure handling**: Push to remote only with
    `archive_gate: passed` when archive is applicable, or
    `archive_gate: not_applicable` otherwise.
    - If push fails with `protected branch` or `remote rejected`: emit
      `push_escalation: pr_required` and stop. A PR requires a separate explicit
      request and approval; do not create one automatically.
    - If push fails with authentication error: emit `push_escalation: auth_failure` — stop and report.
    - If push fails for any other reason: record exit code and stderr as `push_escalation: unknown` — stop and report.
14. **PR and merge phase**: after a successful push and while the archive
    result is `passed` when applicable or `not_applicable` otherwise, use the combined approval
    turn's PR/merge row naming the PR (or proposed head/base pair), current head
    SHA, base branch, and merge method. Create or update the approved PR
    through the GitHub provider, re-read its head, verify required checks and
    reviews, and merge only when the head still equals the approved commit.
    Use the approved method, with squash when selected. If approval is absent
    or merge fails, report the pushed PR as pending/unmerged and stop; do not
    fall back to another method.
15. Summarize changes shipped, including PR and merge status.
16. If the target repo implements a future-work registry + scorecard pattern,
    run that repo's generator only when the target registry changed in approved scope.

## Outputs

- Summary of shipped changes and validation results.
- User-facing result fields MUST report these decisions separately: `future_work`
  applicability, projected-tree validation (`current_head`,
  `projected_include_tree`, `excluded_scope_conflict` when present), security
  admission (`admission_mode`, `policy_source`, receipt, and disposition), and
  publication approval state. Do not collapse a registry reference, a dirty
  worktree conflict, an unavailable target admission, or a declined publication
  row into another field.
- PR number, base branch, verified head SHA, requested merge method, merge
  result, and combined approval-turn record when a PR flow is used; an unmerged
  PR is reported as pending.
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

- Inside repo, turbo markers never bypass the exact clerical, commit, push, and
  merge approvals.
- Closeout is fast; mistakes can be costly if scope is wrong.
- Do not force push without explicit request.
- Do not skip linters (unless user explicitly requests).
- Do not commit sensitive files (.env, credentials, secrets).
- Do not delete scratchpad content without confirmation.
- Do not push without confirming in external repos.
- Do not assume command folders exist; if missing, read `.ai_ops/workflows/closeout.md` manually.
