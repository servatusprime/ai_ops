---
title: Runprogram Pipeline Template
id: runprogram_pipeline_<nn>
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
description: Template for explicit runprogram pipeline artifacts.
---

# Runprogram Pipeline: <program_title>

## Purpose

Describe what this runprogram pipeline orchestrates and why it exists.

## Authority Source

- Governance/gate authority (if present): `execution_spine.md`
- Queue mirror authority: this pipeline file (operational order view)
- Conflict rule: spine wins; pipeline must be synced after spine updates.

## Inputs

- `README.md`
- `run_bundles/` inventory
- Optional: `execution_spine.md` and registry artifacts

## Preconditions

- Runprogram README exists and is current.
- Runbundle inventory is current.
- Required approvals/manual gate owners are identified.

## CSCC Preflight

- [ ] `execution_spine.md` reference is valid (if present).
- [ ] Runbundle queue entries exist and are reachable.
- [ ] Manual gate owners and approval mode are explicit.
- [ ] Validation command paths are known.

## Spine/Pipeline Sync Stamp

- `spine_version`: `<semver>`
- `last_spine_sync_at`: `<YYYY-MM-DD or timestamp>`
- `sync_status`: `in_sync` or `needs_sync`

## Ordered Execution Queue

1. `run_bundles/rnb_<bundle_01>/README.md`
1. `run_bundles/rnb_<bundle_02>/README.md`
1. `run_bundles/rnb_<bundle_03>/README.md`

Note:

- Keep runprogram queue entries at bundle README level.
- Bundle-internal runbook ordering belongs in each bundle's local
  `rnb_<bundle_name>_<nn>.md` queue artifact.

## Batch Sequence Contract (Optional)

For staged execution with parallel batches:

- encode batch gates here and in `execution_spine.md` when present
- run eligible runbundles/runbooks in parallel within batch `NN`
- start batch `NN+1` only after batch `NN` gate conditions pass
- when strict ordered batches are used, prefer `rb_NN_<name>.md` for runbooks

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
- `execution_spine.md` (if present)
- `runbooks_registry.md` (if present)
