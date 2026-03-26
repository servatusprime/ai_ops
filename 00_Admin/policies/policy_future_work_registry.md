---
title: Future Work Registry Policy
version: 0.1.0
status: active
license: Apache-2.0
updated: 2026-02-01
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

The registry is for pending work only. Completed items MUST be removed to keep it lean. Completion is defined as any
entry that meets either condition:

- `source_workbook` appears in `00_Admin/logs/log_workbook_run.md`, or
- `notes` indicates the workbook was trashed (e.g., "Trashed via sandbox cleanup manifest.").

When either condition is true, delete the registry entry and rely on the run log for history.

During `/harvest` or closeout, remove or archive completed items as part of pruning.

## Entry Quality

- Do not keep placeholder items beyond the first template entry.
- New entries MUST include `source_workbook`, `scope`, `priority`, and `created`.

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
