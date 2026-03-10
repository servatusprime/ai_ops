---
title: Workprogram README Template
version: 0.2.2
status: active
license: Apache-2.0
created: 2026-02-01
updated: 2026-03-06
owner: ai_ops
related:
  - 00_Admin/guides/ai_operations/guide_workflows.md
  - 00_Admin/guides/ai_operations/guide_ai_ops_vocabulary.md
description: Template for workprogram README files.
---

# Workprogram: <workprogram_title>

## Purpose

Briefly describe why this workprogram exists and what it coordinates.

## Scope

- **Target**: <repo or module>
- **Focus areas**: <bullets>

## Workbundles

| Workbundle | Purpose | Status |
| --- | --- | --- |
| `wb_<topic>_<nn>_<YYYY-MM-DD>/` | <short description> | <status> |

## Execution Strategy

| Artifact | Mode | Model Tier | Isolation | Actor | Notes |
| --- | --- | --- | --- | --- | --- |
| `wb_<workbundle_01>` | subagent | low (haiku) | none | executor | read-only, bounded |
| `wb_<workbundle_02>` | subagent | medium (sonnet) | worktree | executor | canonical writes |
| `Manual step` | operator | n/a | n/a | requestor | human-only gate |

**Modes:** `direct` (current session), `subagent` (spawned agent), `operator` (human action)

**Model tiers:** `low` (haiku-class), `medium` (sonnet-class), `high` (opus-class)

**Isolation:** `none`, `worktree` (isolated git worktree), `venv`, `container`

**Actor:** `executor`, `requestor`, `approver`, `external_operator`

## Execution Role Contract

Canonical functional roles during execution:

- `Coordinator`: program sequence authority and gate ownership.
- `Executor`: workbook execution inside active workbundles.
- `Builder`: tooling/config implementation lanes when present.
- `Validator`: verification/crosscheck verdict ownership.

Profile/subagent labels are presets; role semantics remain canonical.

## Sequence Naming Contract

Use numbered workbook names for fixed-order execution across workbundles in
this program:

- ordered books: `wb_NN_<name>.md` (for example `wb_01_preflight.md`)
- unordered books: `wb_<name>.md` (no sequence prefix)

Rule:

- If `execution_spine.md` or `workprogram_pipeline_<nn>.md` encodes strict
  order, apply `wb_NN_` naming for affected books.
- If order is informal or parallel-safe, numbering is optional.

Batch-sequenced parallel guidance:

- For staged execution with parallel batches, define explicit batch gates in
  `execution_spine.md` or `workprogram_pipeline_<nn>.md`.
- Books within a batch may run in parallel when `execution_mode` and
  `shared_files/lock_scope` permit it.
- Rule: batch `NN+1` starts only after all required books in batch `NN` pass
  their completion gates.

## Authority Source

- Sequence/gate authority: `execution_spine.md`
- Queue mirrors (optional): `workprogram_pipeline_<nn>.md`
- Conflict rule: spine wins; pipeline is synced after spine updates.

## CSCC Preflight

- [ ] Program planning-output source/spec/spine/registry paths are valid.
- [ ] Workbundle inventory reflects current reality.
- [ ] Compacted context source is known (program or bundle README).
- [ ] Gate owners/approval mode are explicit.
- [ ] Validation command paths are known.

## Status

- [ ] Workprogram created
- [ ] Active workbundles in progress
- [ ] All workbundles complete
- [ ] Closeout complete

## Maintenance

- Update this README when adding/removing workbundles.
- Update the `updated` date whenever contents change.

## Axis Mapping

- Primary axis: `commitment`
- Quality axes: `clarity`, `thrift`, `context`, `governance`

## References

- `<path/to/runbook_or_guide>`
- `execution_spine.md` (recommended)
- `workprogram_pipeline_<nn>.md` (optional)
