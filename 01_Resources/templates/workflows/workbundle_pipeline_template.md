---
title: Workbundle Pipeline Template
id: wb_pipeline_<bundle_name>_<nn>
version: 0.2.1
status: active
license: Apache-2.0
created: 2026-02-18
updated: 2026-03-06
owner: ai_ops
related:
  - 00_Admin/guides/ai_operations/guide_workflows.md
  - 00_Admin/guides/ai_operations/guide_parallel_execution.md
lifecycle: transient
primary_axis: execution
execution_mode: sequential
depends_on: []
shared_files: []
lock_scope: none
description: Template for explicit workbundle pipeline artifacts (`wb_pipeline_*.md`).
---

# Workbundle Pipeline: <bundle_title>

## Purpose

Describe what this workbundle pipeline executes and why it exists.

## Authority Source

- Local execution queue authority: this pipeline file.
- Parent gate authority (if program-scoped): `../execution_spine.md`.
- Conflict rule: parent spine wins where applicable.

## Inputs

- `<input_1>`
- `<input_2>`

## Preconditions

- Required environment(s) are available.
- Required source files are present.
- Required approvals/manual gate owners are identified.

## CSCC Preflight

- [ ] Queue entries exist and are reachable.
- [ ] Any parent spine reference is valid (if present).
- [ ] Local manual gate owners are identified.
- [ ] Validation command paths are known.

## Ordered Execution Queue

1. `./wb_<step_00>.md`
1. `./wb_<step_01>.md`
1. `./wb_<step_02>.md`

## Batch Sequence Contract (Optional)

For staged execution with parallel batches:

- define `Batch 01`, `Batch 02`, etc. in this queue artifact
- run all parallel-safe books inside batch `NN`
- block batch `NN+1` until required books in batch `NN` complete
- use `wb_NN_<name>.md` naming when strict ordered batches are used

## Manual Gates (If Any)

| Gate ID | Before Step | Gate Type | Approver | Description |
| --- | --- | --- | --- | --- |
| `G-01` | `<step>` | `handoff` / `checkpoint` | `<role>` | `<what must be confirmed before proceeding>` |

**Gate types:** `handoff` -- step passed to gated role; executor stops until confirmation.
`checkpoint` -- executor produces output but another role must confirm before downstream continues.

## Validation Commands

```powershell
python 00_Admin/scripts/validate_repo_rules.py --config 00_Admin/configs/validator/validator_config.yaml
markdownlint <changed_paths>
```

## Outputs

- `<output_1>`
- `<output_2>`

## Postconditions

- `<postcondition_1>`
- `<postcondition_2>`

## Axis Mapping

- Primary axis: `execution`
- Quality axes: `clarity`, `thrift`, `context`, `governance`

## References

- `README.md`
- `./work_summary.md`
- `../execution_spine.md` (if program-scoped)
