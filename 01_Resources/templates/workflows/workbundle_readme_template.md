---
title: Workbundle README Template
version: 0.2.2
status: active
license: Apache-2.0
created: 2026-02-01
updated: 2026-03-06
owner: ai_ops
related:
  - 00_Admin/guides/ai_operations/guide_workflows.md
  - 00_Admin/guides/ai_operations/guide_ai_ops_vocabulary.md
description: Template for workbundle README files.
---

# Workbundle: <workbundle_title>

## Purpose

Briefly describe why this workbundle exists and what it will accomplish.

## Scope

- **Target**: <repo or module>
- **Focus areas**: <bullets>

## Contents

| File | Purpose |
| --- | --- |
| `wb_<workbook_id>.md` | Primary workbook |
| `_scratchpad_<agent>_<YYYY-MM-DD>.md` | Session notes |

## Execution Strategy

| Artifact | Mode | Model Tier | Isolation | Actor | Notes |
| --- | --- | --- | --- | --- | --- |
| `wb_<workbook_id>` | subagent | medium (sonnet) | none | executor | bounded, file writes |
| `Manual step` | operator | n/a | n/a | requestor | human-only gate |

**Modes:** `direct` (current session), `subagent` (spawned agent), `operator` (human action)

**Model tiers:** `low` (haiku-class), `medium` (sonnet-class), `high` (opus-class)

**Isolation:** `none`, `worktree` (isolated git worktree), `venv`, `container`

**Actor:** `executor`, `requestor`, `approver`, `external_operator`

## Execution Role Contract

Canonical functional roles during execution:

- `Coordinator`: sequencing and approval/gate ownership.
- `Executor`: workbook task execution and evidence capture.
- `Builder`: tooling/config implementation when invoked by workbook scope.
- `Validator`: pass/fail verification and crosscheck findings.

Profile/subagent labels are presets; role semantics remain canonical.

## Sequence Naming Contract

Use numbered workbook names when execution order is fixed and coordinated
inside this bundle:

- ordered books: `wb_NN_<name>.md` (for example `wb_01_audit.md`)
- unordered books: `wb_<name>.md` (no sequence prefix)

Rule:

- If this README or a local pipeline defines a strict order, apply `wb_NN_`
  naming.
- If order is informal, do not force numbering.

Batch-sequenced parallel guidance:

- If books run in parallel batches that must occur in strict stage order,
  keep `wb_NN_` numbering aligned to batch sequence.
- Use one queue section per batch (for example `Batch 01`, `Batch 02`) in the
  local pipeline/README and mark books within a batch as parallel-safe.
- Rule: all books in batch `NN` must complete before any book in batch `NN+1`
  starts.

## Authority Source

- Parent authority (if program-scoped): `../execution_spine.md`
- Local queue mirror (optional): `wb_pipeline_<bundle_name>_<nn>.md`
- Conflict rule: parent spine wins where applicable.

## CSCC Preflight

- [ ] Workbook path and companion artifacts are valid.
- [ ] Parent program references are valid (if present).
- [ ] Compacted context source is known (workbundle README or workbook body if standalone).
- [ ] Local gates/approvals are explicit before execution.
- [ ] Validation command paths are known.

## Status

- [ ] Workbundle created
- [ ] Primary workbook drafted
- [ ] Execution in progress
- [ ] Remediation complete
- [ ] Closeout complete

## Maintenance

- Update this README when new artifacts are added.
- Update the `updated` date whenever contents change.

## Axis Mapping

- Primary axis: `commitment`
- Quality axes: `clarity`, `thrift`, `context`, `governance`

## References

- `<path/to/runbook_or_guide>`
- `wb_pipeline_<bundle_name>_<nn>.md` (optional pipeline artifact)
