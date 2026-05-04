---
title: Guide: Runprograms
version: 0.1.0
status: stub
license: Apache-2.0
last_updated: 2026-01-24
owner: ai_ops
related:
- 00_Admin/guides/ai_operations/guide_workflows.md
- 00_Admin/guides/ai_operations/guide_ai_ops_vocabulary.md
- 00_Admin/guides/ai_operations/guide_execution_spines.md
- 00_Admin/guides/authoring/guide_spec.md
---

# Guide: Runprograms

## Purpose and scope

A **Runprogram** is an execution-level container that coordinates multiple runbooks in a required order. It is an
escalated Runbundle with added structure and a shared Execution Spine.

This guide defines how to structure a Runprogram folder and what it must contain.

## Definition

Runprogram:

- Coordinates a sequence of runbooks.
- Defines run-order dependencies and checkpoints.
- Includes an Execution Spine and a Program Spec to unify execution.

Runprograms are not runbooks and are not executed directly.

## Required contents

Each Runprogram folder MUST include:

- **Execution Spine** (`execution_spine.md`)
- **Program Spec** (use spec template; filename `spec_<program_id>.md`)
- **Program index/README** (`README.md`) listing included runbooks and status
- **Runbook registry** (list of runbooks and their paths)
- **Run bundles folder** (`run_bundles/`) when the program includes runbooks

Optional:

- Environment notes and validation gates
- Reference packs for handoff

## Location and naming

Runprograms live alongside the runbooks they coordinate:

- Cross-cutting: `00_Admin/runbooks/run_program_<program_id>/`
- Module-specific: `02_Modules/<module>/docs/runbooks/run_program_<program_id>/`

Naming rules:

- `program_id` is lower_snake_case.
- Keep Runprogram artifacts inside a single folder named `run_program_<program_id>/`.

Runbundle grouping (optional):

- Use a folder named by kind under the program folder, e.g.,
  `run_program_<program_id>/run_bundles/rnb_maintenance/`, to group related runbooks.
- Runbundles are informal groupings and do not require a Program Spec or Execution Spine.

## Structure (example)

```text
00_Admin/runbooks/run_program_repo_maintenance/
  README.md
  execution_spine.md
  spec_repo_maintenance_program.md
  runbooks_registry.md
  run_bundles/
    rnb_maintenance/
      rb_repo_health_review.md
```

## Runbundle vs Runprogram

| Aspect | Runbundle | Runprogram |
| --- | --- | --- |
| Definition | Informal grouping of related runbooks | Formal coordination with ordering |
| Structure | Optional README | Required: Execution Spine + Program Spec |
| Use when | 2-3 related runbooks, loose coupling | 3+ runbooks, dependencies, strict order |
| Location | `run_program_<id>/run_bundles/rnb_<bundle_name>/` | Dedicated program folder |
| Example | Maintenance runbooks grouped together | Full deployment sequence |

## Cost Governance

The `cost_governance:` field is optional frontmatter available in all execution artifact
types including runbundles and runprograms. Absence means thrift judgment applies without
a hard budget constraint. See `00_Admin/specs/spec_cost_governance.md` for the full schema.

## References

- `00_Admin/guides/authoring/guide_spec.md`
- `00_Admin/guides/ai_operations/guide_execution_spines.md`
- `00_Admin/specs/spec_cost_governance.md`
