---
title: Runprogram README Template
version: 0.2.2
status: active
license: Apache-2.0
created: 2026-02-01
updated: 2026-03-06
owner: ai_ops
related:
  - 00_Admin/guides/ai_operations/guide_workflows.md
  - 00_Admin/guides/ai_operations/guide_ai_ops_vocabulary.md
description: Template for runprogram README files.
---

# Runprogram: <runprogram_title>

## Purpose

Briefly describe why this runprogram exists and what it coordinates.

## Scope

- **Target**: <repo or module>
- **Focus areas**: <bullets>

## Runbundles

| Runbundle | Purpose | Status |
| --- | --- | --- |
| `rnb_<bundle_name>/` | <short description> | <status> |

Runbundle layout expectation (recommended):

- `rnb_<bundle>/README.md`
- `rnb_<bundle>/rnb_<bundle>_<nn>.md` (optional local pipeline)
- `rnb_<bundle>/runbooks/rb_*.md`

## Execution Strategy

| Artifact | Mode | Model Tier | Isolation | Actor | Notes |
| --- | --- | --- | --- | --- | --- |
| `rnb_<bundle_01>` | subagent | low (haiku) | none | executor | bounded, repeatable |
| `rnb_<bundle_02>` | subagent | medium (sonnet) | worktree | executor | writes to shared surface |
| `Manual step` | operator | n/a | n/a | requestor | human-only gate |

**Modes:** `direct` (current session), `subagent` (spawned agent), `operator` (human action)

**Model tiers:** `low` (haiku-class), `medium` (sonnet-class), `high` (opus-class)

**Isolation:** `none`, `worktree` (isolated git worktree), `venv`, `container`

**Actor:** `executor`, `requestor`, `approver`, `external_operator`

## Execution Lane Contract

Canonical lanes during execution:

- `Coordinator`: runprogram sequencing and gate ownership.
- `Executor`: runbundle/runbook task execution.
- `Builder`: tooling/config implementation lanes when present.
- `Reviewer`: review and crosscheck verdict ownership.
- `Linter`: mechanical validation/report-only gate ownership.

## Sequence Naming Contract

Use numbered runbook names for fixed-order execution across runbundles in this
program:

- ordered books: `rb_NN_<name>.md` (for example `rb_01_preflight.md`)
- unordered books: `rb_<name>.md` (no sequence prefix)

Rule:

- If `execution_spine.md` or `runprogram_pipeline_<nn>.md` encodes strict
  order, apply `rb_NN_` naming for affected books.
- If order is informal or parallel-safe, numbering is optional.

Batch-sequenced parallel guidance:

- For staged execution with parallel batches, define explicit batch gates in
  `execution_spine.md` or `runprogram_pipeline_<nn>.md`.
- Runbooks may run in parallel within a batch only when `execution_mode` and
  lock declarations allow it.
- Rule: batch `NN+1` cannot start until all required runbooks in batch `NN`
  satisfy completion gates.

## Authority Source

- Sequence/gate authority (if present): `execution_spine.md`
- Queue mirror (optional): `runprogram_pipeline_<nn>.md`
- Conflict rule: spine wins; pipeline is synced after spine updates.

## CSCC Preflight

- [ ] Runprogram README/spine/pipeline references are valid.
- [ ] Runbundle inventory reflects current execution scope.
- [ ] Compacted context source is known (runprogram or runbundle README).
- [ ] Gate owners/approval mode are explicit.
- [ ] Validation command paths are known.

## Status

- [ ] Runprogram created
- [ ] Active runbundles in progress
- [ ] All runbundles complete
- [ ] Closeout complete

## Maintenance

- Update this README when adding/removing runbundles.
- Update the `updated` date whenever contents change.

## Axis Mapping

- Primary axis: `execution`
- Quality axes: `clarity`, `thrift`, `context`, `governance`

## References

- `<path/to/runbook_or_guide>`
- `execution_spine.md` (optional but recommended for governed runs)
- `runprogram_pipeline_<nn>.md` (optional)
