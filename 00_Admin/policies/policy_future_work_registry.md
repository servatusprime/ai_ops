---
title: Future Work Registry Policy
version: 0.5.0
status: active
license: Apache-2.0
updated: 2026-10-24
---
<!-- markdownlint-disable-next-line MD025 -->
# Future Work Registry Policy

## Purpose

Define how the `00_Admin/backlog/future_work_registry.yaml` is maintained.

## Status Values

Valid `status` values for registry entries:

- `planned` — Work is identified and scoped but not yet started.
- `active` — Work is currently in progress.
- `deferred` — Work is postponed; see `activation_trigger` for conditions to re-open.
- `recurring` — Task recurs on a schedule or when a trigger condition is met. Use `recurrence_trigger` field
  to document when to re-open.

## Completion and Deletion Rule

The registry is for pending work only. Completed items MUST be removed to keep
it lean.

- `source_workbook` records provenance only. Completion or archival of that
  workbook MUST NOT be interpreted as completion of the future-work item.
- Every entry MUST include both `proposed_workbook` and `completion_workbook`.
  Use `null` while the item is pending. The completion command binds the
  execution workbook to the entry's repo-relative `proposed_workbook` value;
  the caller's `completion_workbook` argument must match that value. Keep
  `completion_workbook` as the historical/legacy field, but do not treat it as
  authority unless it is explicitly synchronized with `proposed_workbook`.
  For a `success` outcome, the same non-null binding must already exist in the
  registry at `HEAD`; editing the working-tree row immediately before
  completion cannot create its own authority.
- An item is complete only when the completion command writes a successful,
  schema-valid receipt for the exact registry ID and appends its exact
  structured success marker to `00_Admin/logs/log_workbook_run.md`. A workbook
  path is an evidence reference, not completion authority by itself.

When the completion condition is true, delete the registry entry in the same
closeout change and rely on the run log for history. Trashing an originating or
intake workbook is not completion evidence by itself.

### Receipt-Backed Completion Command

Use `00_Admin/scripts/complete_future_work.py` for completion outcomes. The
command writes an exclusive-created receipt under
`90_Sandbox/ai_workbooks/_closeout_packets/<repo>/<run_id>/` and appends a
structured `future_work_completion` marker to the run log. Its receipt binds the
registry entry scope, completion-artifact hashes, point-in-time run-log hash,
run-log marker hash, scorecard source hash, actor, timestamps, and provenance
references.

- `success` requires either a real completion workbook with `status: completed`
  or an explicit receipt handoff with `status: active`,
  `execution_status: completed`, and `completion_state: ready_for_receipt`.
  The latter state means implementation is complete but the receipt-backed
  registry transaction and final workbook synchronization are still pending;
  it is not a substitute for final workbook closeout. Both forms require exit
  code `0`, hashable completion artifacts, and at least one retained
  non-blocking crosscheck or review reference. The command regenerates the
  scorecard, verifies exact registry-ID parity after removing only the target
  ID, and only then deletes that entry.
- `failed`, `pending`, and `stale` write evidence but preserve the registry
  entry and identify the outcome for the next `/work` or `/closeout` pass.
- A text-only `completion_workbook` mention, a workbook filename in a log, or a
  generated scorecard without a matching receipt is never completion evidence.
  Receipt artifact hashes are point-in-time facts; `--verify` checks the
  exclusive-created receipt's self-digest, its structured run-log marker and
  marker hash, its retained review references, and the registry state. The
  durable audit link is the structured run-log marker, not a claim that later
  edits to the referenced workbook are retroactively invalid.
- Registry deletion is a journaled local filesystem transaction: canonical
  writes use same-directory atomic replacement, a recovery journal and
  pre-mutation backups are written first, and a failed verification restores
  the prior canonical files. An unfinished journal parks the next attempt for
  explicit recovery; it never silently deletes the item.

### HEAD-Binding and Receipt Sequence

When a future-work row is being completed in the same change set that binds its
`proposed_workbook`, use two publication phases:

1. Prepare the workbook as an explicit `ready_for_receipt` handoff, freeze the
   implementation scope, and commit the registry binding and implementation
   through the normal closeout approval gate. Do not run a success completion
   receipt before this commit; the command intentionally reads the registry
   from `HEAD`, not only from the working tree.
2. After the binding commit is verified at `HEAD`, run
   `complete_future_work.py` once per registry ID and verify each exclusive
   receipt. The command's registry, scorecard, and run-log mutations are the
   receipt-sync scope. Then set the workbook to `status: completed`, close the
   handoff items, and publish those final mirror changes through a second
   approval-gated closeout commit.

Receipt artifact hashes are point-in-time evidence. Finalizing the workbook
after receipt creation does not rewrite the historical receipt; the second
commit is required to make the final workbook state and companion surfaces
converge.

During `/harvest` or closeout, remove or archive completed items as part of pruning.

Before any archive or completion claim, record the candidate's tracked or
ignored state, source hash, collision result, active-reference result, retention
class, approval, recovery owner, and row-level outcome in the cleanup manifest.
If the registry, run log, scorecard, or completion evidence is not in the same
approved mutation plan, the item remains pending; a text occurrence of a
workbook name is not completion evidence. A failed or partial cleanup parks the
row with its exact resume point rather than silently skipping it.

## Entry Quality

- Do not keep placeholder items beyond the first template entry.
- New entries MUST include `source_workbook`, `proposed_workbook`,
  `completion_workbook`, `scope`, `priority`, and `created`.

## Promotion Hook (Manual)

Future work items noted in `00_Admin/logs/log_workbook_run.md` are promoted during active
`/harvest` and `/closeout` workflows. Use the latest relevant run entry as the cutoff for each sweep.

## Dynamic Scorecard Sync (Required)

The registry has a generated scorecard at:

- `00_Admin/backlog/future_work_scorecard.md`

After any edit to `00_Admin/backlog/future_work_registry.yaml`, regenerate the scorecard in the same change:

```powershell
python ai_ops/00_Admin/scripts/generate_future_work_scorecard.py
```

The scorecard file should contain only the matrix view and brief generation notes.
