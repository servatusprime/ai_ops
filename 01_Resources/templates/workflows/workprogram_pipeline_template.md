---
title: Workprogram Pipeline Template
id: workprogram_pipeline_<nn>
version: 0.2.2
status: active
license: Apache-2.0
created: 2026-02-18
updated: 2026-03-21
owner: ai_ops
related:
  - 00_Admin/guides/ai_operations/guide_workflows.md
  - 00_Admin/guides/ai_operations/guide_parallel_execution.md
lifecycle: transient
primary_axis: execution
execution_mode: sequential
execution_topology: single_agent  # single_agent | multi_agent | parallel_safe
activated_lanes:
  - Coordinator
  - Executor
  - Reviewer
delegation_policy: explicit_only
convergence_profile: iterative_convergence_minimal
parallel_coordination_id: null  # Set when sibling programs run concurrently
depends_on: []
shared_files: []
lock_scope: none
description: Template for explicit workprogram pipeline artifacts.
---

# Workprogram Pipeline: <program_title>

## Purpose

Describe what this workprogram pipeline orchestrates and why it exists.

## Authority Source

- Governance/gate authority: `execution_spine.md`
- Queue mirror authority: this pipeline file (operational order view)
- Conflict rule: spine wins; pipeline must be synced after spine updates.

## Inputs

- `README.md`
- `work_packets/` inventory
- Optional: `execution_spine.md` and registry artifacts

## Preconditions

- Workprogram README exists and is current.
- Workbundle inventory is current.
- Required approvals/manual gate owners are identified.

## CSCC Preflight

- [ ] `execution_spine.md` exists and is current.
- [ ] Workbundle queue entries exist and are reachable.
- [ ] Manual gate owners and approval mode are explicit.
- [ ] Validation command paths are known.

## Spine/Pipeline Sync Stamp

- `spine_version`: `<semver>`
- `last_spine_sync_at`: `<YYYY-MM-DD or timestamp>`
- `sync_status`: `in_sync` or `needs_sync`

## Ordered Execution Queue

1. `work_packets/wb_<bundle_01>_<YYYY-MM-DD>/README.md`
1. `work_packets/wb_<bundle_02>_<YYYY-MM-DD>/README.md`
1. `work_packets/wb_<bundle_03>_<YYYY-MM-DD>/README.md`

## Batch Sequence Contract (Optional)

For staged execution with parallel batches:

- encode batch gates here and in `execution_spine.md`
- run eligible bundles/books in parallel within batch `NN`
- start batch `NN+1` only after batch `NN` gate conditions pass
- when strict ordered batches are used, prefer `wb_NN_<name>.md` for books

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
- `workbooks_registry.md` (if present)
