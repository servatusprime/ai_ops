---
title: Execution Spine Template
id: execution_spine_<program_id>
version: 0.2.2
status: active
license: Apache-2.0
created: 2026-02-18
updated: 2026-03-21
owner: ai_ops
related:
  - 00_Admin/guides/ai_operations/guide_workflows.md
  - 00_Admin/guides/ai_operations/guide_execution_spines.md
lifecycle: commitment
primary_axis: commitment
execution_topology: single_agent  # single_agent | multi_agent | parallel_safe
activated_lanes:
  - Coordinator
  - Executor
  - Reviewer
delegation_policy: explicit_only  # explicit_only | lane_default
convergence_profile: iterative_convergence_standard
parallel_coordination_id: null  # Set when sibling spines run concurrently
description: Template for canonical program-level execution spine artifacts.
---

# Execution Spine: <program_title>

## Purpose and Scope

Define canonical sequencing, dependency gates, and validation checkpoints for
this program. This artifact is the authority for sequence/gate decisions.

## Authority Source and Boundaries

- Authority source:
  - workbook/runbook Planning Outputs (scope/rationale authority)
  - `spec_<program>.md` (requirements authority)
  - this execution spine (sequence/gate authority)
- Boundary rule:
  - do not duplicate scope rationale from Planning Outputs
  - do not duplicate requirements from Program Spec
  - pipelines may mirror queue order but must defer to spine for gate authority
- Conflict rule:
  - if pipeline and spine diverge, spine wins until synced

## Inputs and Assumptions

- Planning-output source: `<path/to/workbook_or_runbook_planning_outputs>`
- Program spec: `<path/to/spec>`
- Registry: `<path/to/registry>`
- Program README: `<path/to/README>`
- Runtime baseline assumptions: `<runtime/profile>`

## CSCC Preflight Gate

Before execution starts, confirm:

- [ ] Program planning-output source, spec, and registry paths are valid
- [ ] Active artifact set is known (`.ai_ops/local/work_state.yaml work_context.active_artifacts`)
- [ ] Operator environment/runtime assumptions are explicit
- [ ] Entry gate ownership and approval mode are explicit
- [ ] Required validators and lint command paths are known

## Sequence

| Phase | Milestone | Objective | Primary Outputs |
| --- | --- | --- | --- |
| M0 | `<milestone_0>` | `<objective>` | `<outputs>` |
| M1 | `<milestone_1>` | `<objective>` | `<outputs>` |
| M2 | `<milestone_2>` | `<objective>` | `<outputs>` |

## Batch Sequence Contract (Parallel + Ordered)

Use this when work can run in parallel batches but batch order is fixed:

- batch `NN`: parallel-safe items may execute concurrently
- batch `NN+1`: blocked until required gates for batch `NN` pass
- numbering guidance:
  - ordered workbooks: `wb_NN_<name>.md`
  - ordered runbooks: `rb_NN_<name>.md`

## Dependencies and Handoffs

- `<milestone_1>` depends on `<milestone_0>`
- `<milestone_2>` depends on `<milestone_1>`
- Cross-lane handoffs must cite source artifact paths

## Checkpoints and Validation Gates

| Milestone | Entry Criteria | Exit Criteria | Go/No-Go Gate |
| --- | --- | --- | --- |
| M0 | `<entry>` | `<exit>` | `<gate>` |
| M1 | `<entry>` | `<exit>` | `<gate>` |
| M2 | `<entry>` | `<exit>` | `<gate>` |

## Validation Commands

```powershell
python 00_Admin/scripts/validate_repo_rules.py --config 00_Admin/configs/validator/validator_config.yaml
markdownlint <changed_paths>
yamllint -c .yamllint <changed_yaml_paths>
```

## Outputs and Artifacts

- Program-level output artifacts and expected locations
- Gate evidence artifacts (reports/logs/checklists)
- Pipeline sync artifacts (if used)

## Spine/Pipeline Sync Stamp

- `spine_version`: `<semver>`
- `pipeline_sync_required`: `true` or `false`
- `last_pipeline_sync_at`: `<YYYY-MM-DD or timestamp>`

## Run Notes and Audit Trail

Record per-run updates without rewriting prior evidence.

| Date | Actor | Change | Evidence Path |
| --- | --- | --- | --- |
| `<YYYY-MM-DD>` | `<role>` | `<summary>` | `<path>` |

## Axis Mapping

| Artifact Section | Primary Axis | Notes |
| --- | --- | --- |
| Purpose and Scope | Commitment | Program-level locked outcome |
| Sequence and Dependencies | Commitment | Canonical ordering authority |
| Gates and Checkpoints | Commitment + Verification | Entry/exit/go-no-go criteria |
| Validation Commands | Verification | Machine-checkable confirmation |
| Run Notes and Audit Trail | Verification | Durable execution evidence |

## References

- `README.md`
- `<path/to/workbook_or_runbook_planning_outputs>`
- `<path/to/spec>`
- `<path/to/registry>`
