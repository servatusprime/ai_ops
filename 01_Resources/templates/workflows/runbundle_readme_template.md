---
title: Runbundle README Template
version: 0.2.2
status: active
license: Apache-2.0
created: 2026-02-01
updated: 2026-03-06
owner: ai_ops
related:
  - 00_Admin/guides/ai_operations/guide_workflows.md
  - 00_Admin/guides/ai_operations/guide_ai_ops_vocabulary.md
description: Template for runbundle README files.
---

# Runbundle: <runbundle_title>

## Purpose

Briefly describe why this runbundle exists and what it executes.

## Scope

- **Target**: <repo or module>
- **Focus areas**: <bullets>

## Contents

| File | Purpose |
| --- | --- |
| `runbooks/rb_<runbook_id>.md` | Primary runbook |
| `rnb_<bundle_name>_<nn>.md` | Local queue artifact (optional) |
| `_scratchpad_<agent>_<YYYY-MM-DD>.md` | Notes (optional) |

## Execution Strategy

| Artifact | Mode | Model Tier | Isolation | Actor | Notes |
| --- | --- | --- | --- | --- | --- |
| `rb_<runbook_id>` | subagent | low (haiku) | none | executor | bounded, repeatable |
| `Manual step` | operator | n/a | n/a | requestor | human-only gate |

**Modes:** `direct` (current session), `subagent` (spawned agent), `operator` (human action)

**Model tiers:** `low` (haiku-class), `medium` (sonnet-class), `high` (opus-class)

**Isolation:** `none`, `worktree` (isolated git worktree), `venv`, `container`

**Actor:** `executor`, `requestor`, `approver`, `external_operator`

## Execution Lane Contract

Canonical lanes during execution:

- `Coordinator`: sequence and gate ownership.
- `Executor`: runbook execution.
- `Builder`: tooling/config implementation when required by runbook scope.
- `Reviewer`: judgment-heavy review and crosscheck findings.
- `Linter`: mechanical validation findings and report-only checks.

## Sequence Naming Contract

Use numbered runbook names when execution order is fixed and coordinated
inside this runbundle:

- ordered books: `rb_NN_<name>.md` (for example `rb_01_preflight.md`)
- unordered books: `rb_<name>.md` (no sequence prefix)

Rule:

- If this README or `rnb_<bundle_name>_<nn>.md` defines strict order, apply
  `rb_NN_` naming.
- If order is informal, do not force numbering.

Batch-sequenced parallel guidance:

- If runbooks execute in parallel batches with strict stage ordering, keep
  `rb_NN_` numbering aligned to batch sequence.
- Use batch sections in local queue artifacts to show which runbooks can run
  concurrently in each stage.
- Rule: all required runbooks in batch `NN` must complete before starting
  batch `NN+1`.

## Authority Source

- Parent authority (if program-scoped): `../../execution_spine.md`
- Local queue artifact: `rnb_<bundle_name>_<nn>.md`
- Conflict rule: parent spine wins where applicable.

## CSCC Preflight

- [ ] Runbook path and companion artifacts are valid.
- [ ] Parent program references are valid (if present).
- [ ] Compacted context source is known (runbundle README or runbook body if standalone).
- [ ] Local gates/approvals are explicit before execution.
- [ ] Validation command paths are known.

## Status

- [ ] Runbundle created
- [ ] Execution in progress
- [ ] Execution complete
- [ ] Closeout complete

## Maintenance

- Update this README when new artifacts are added.
- Update the `updated` date whenever contents change.

## Axis Mapping

- Primary axis: `execution`
- Quality axes: `clarity`, `thrift`, `context`, `governance`

## References

- `<path/to/runbook_or_guide>`
- `rnb_<bundle_name>_<nn>.md` (optional pipeline artifact)
