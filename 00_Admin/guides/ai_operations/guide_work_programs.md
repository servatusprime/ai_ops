---
title: Guide: Workprograms
version: 0.2.0
status: active
last_updated: 2026-03-04
owner: ai_ops
license: Apache-2.0
related:
- 00_Admin/guides/ai_operations/guide_workflows.md
- 00_Admin/guides/ai_operations/guide_ai_ops_vocabulary.md
- 00_Admin/guides/ai_operations/guide_execution_spines.md
- 00_Admin/guides/authoring/guide_workbooks.md
- 00_Admin/guides/authoring/guide_spec.md
---

# Guide: Workprograms

## Purpose and scope

A **Workprogram** is a commitment-level container that coordinates multiple workbooks/workbundles toward a single
objective. It is a program-level container with its own spec/spine and registries.

This guide defines how to structure a Workprogram folder, execution-role semantics,
and CSCC context requirements.

## Definition

Workprogram:

- Coordinates a sequence of workbooks/workbundles.
- Defines shared assumptions and dependencies.
- Includes an Execution Spine and a Program Spec to unify the program.

Workprograms are not Workbooks and are not executed directly.

## Execution roles (canonical)

Program execution uses canonical functional roles:

- `Coordinator`: owns program sequencing, gate decisions, and cross-bundle handoffs.
- `Executor`: runs workbook tasks inside bundled lanes.
- `Builder`: performs tooling/config implementation work when invoked by workbook scope.
- `Validator`: performs phase/program verification and crosschecks.

Profile/subagent labels are execution presets. Functional role meaning remains canonical.

## Required contents

Each Workprogram folder MUST include:

- **Execution Spine** (`execution_spine.md`)
- **Program Spec** (use spec template; filename `spec_<program_id>.md`)
- **Program index/README** (`README.md`) listing included workbooks/workbundles and status
- **Workbook registry** (list of workbooks/workbundles and their paths)
- **Work workbundles folder** (`work_packets/`) when the program includes workbooks
- **Execution Strategy** section in program `README.md` declaring mode, model tier, isolation, actor

Optional:

- Program-level notes (decisions, risks)
- Reference packs for handoff

## CSCC context contract (program lanes)

Before a CSCC agent executes any workbook under a workprogram, verify this minimum context set:

- workprogram `README.md` (execution strategy + current status),
- `execution_spine.md` (authoritative sequence and gates),
- `spec_<program_id>.md` (requirements/invariants),
- `workbooks_registry.md` (active packet inventory),
- target workbundle `README.md` and target workbook file,
- compacted context location (program/workbundle README unless standalone workbook lane).

If any context artifact is missing or stale, pause execution and repair context first.

## Location and naming

Workprograms live under `90_Sandbox/ai_workbooks/` using a program-specific folder:

`90_Sandbox/ai_workbooks/work_program_<program_id>/`

Naming rules:

- `program_id` is lower_snake_case.
- Keep all Workprogram artifacts inside the folder.
- Store workbundles under `work_program_<program_id>/work_packets/`.

## Structure (example)

```text
work_program_example_program/
  README.md
  execution_spine.md
  spec_example_program.md
  workbooks_registry.md
  work_packets/
    wb_example_step_01_2026-01-14/
      wb_example_step_01.md
```

## Workbook registry example

<!-- markdownlint-disable MD013 -->
```text
workbooks_registry.md
| Workbook ID | Path | Status | Dependencies |
| --- | --- | --- | --- |
| wb_example_step_01 | 90_Sandbox/ai_workbooks/work_program_example_program/work_packets/wb_example_step_01_2026-01-14/wb_example_step_01.md | active | none |
| wb_example_step_02 | 90_Sandbox/ai_workbooks/work_program_example_program/work_packets/wb_example_step_02_2026-01-14/wb_example_step_02.md | planned | wb_example_step_01 |
| wb_example_step_03 | 90_Sandbox/ai_workbooks/work_program_example_program/work_packets/wb_example_step_03_2026-01-14/wb_example_step_03.md | planned | wb_example_step_02 |
```
<!-- markdownlint-enable MD013 -->

## References

- `00_Admin/guides/authoring/guide_workbooks.md`
- `00_Admin/guides/authoring/guide_spec.md`
- `00_Admin/guides/ai_operations/guide_execution_spines.md`
- `00_Admin/guides/ai_operations/guide_ai_operations_stack.md`
