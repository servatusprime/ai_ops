---
title: Runbundle Pipeline Template
id: rnb_<bundle_name>_<nn>
version: 0.3.0
status: active
license: Apache-2.0
created: 2026-02-18
updated: 2026-07-16
owner: ai_ops
related:
  - 00_Admin/guides/ai_operations/guide_workflows.md
  - 00_Admin/guides/ai_operations/guide_parallel_execution.md
  - 00_Admin/specs/spec_run_family_composition.md
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
parallel_coordination_id: null  # Set when sibling bundles run concurrently
depends_on: []
shared_files: []
lock_scope: none
description: Template for explicit runbundle pipeline artifacts (`rnb_*.md`).
cost_governance:  # Work-family: MAY self-impose limits. Run-family: SHOULD populate. null = thrift judgment. See spec_cost_governance.md.
  session_token_budget: null
  workpacket_token_budget: null
  model_routing:
    planning: null
    execution: null
    review: null
  alert_threshold_pct: 80
  exceeded_action: PARK
---

# Runbundle Pipeline: <bundle_title>

## Purpose

Describe what this runbundle pipeline executes and why it exists.

## Authority Source

- Local execution queue authority: this pipeline file.
- Membership authority: `<path/to/runbundle_manifest.yaml>`.
- Optional consumer/gate authority: `<consumer_id>` / `<resolved_spine_path>`.
- Conflict rule: the explicitly referenced spine governs its gates; directory
  ancestry never grants authority.

## Inputs

- `<path/to/runbundle_manifest.yaml>`
- `00_Admin/runbooks/run_family_registry.yaml`
- `<input_1>`

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

1. `rb_<step_00>` -> `<resolved-canonical-home>`
1. `rb_<step_01>` -> `<resolved-canonical-home>`
1. `rb_<step_02>` -> `<resolved-canonical-home>`

## Batch Sequence Contract (Optional)

For staged execution with parallel batches:

- define `Batch 01`, `Batch 02`, etc. in this queue artifact
- run parallel-safe runbooks inside batch `NN`
- block batch `NN+1` until required runbooks in batch `NN` complete
- use `rb_NN_<name>.md` naming when strict ordered batches are used

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
- `<path/to/runbundle_manifest.yaml>`
- `00_Admin/runbooks/run_family_registry.yaml`
- `<resolved_spine_path>` (if an explicit consumer supplies gate authority)
