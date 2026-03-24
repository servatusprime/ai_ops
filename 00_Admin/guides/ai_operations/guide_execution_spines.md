---
title: Guide: Execution Spines
version: 0.2.0
status: active
license: Apache-2.0
last_updated: 2026-03-04
owner: ai_ops
related:
- 00_Admin/guides/ai_operations/guide_ai_ops_vocabulary.md
- 00_Admin/guides/ai_operations/guide_workflows.md
- 00_Admin/guides/ai_operations/guide_ai_operations_stack.md
- 00_Admin/specs/spec_execution_orchestration.md
- 00_Admin/guides/authoring/guide_spec.md
---

# Guide: Execution Spines

## Purpose and scope

An **Execution Spine** is the canonical sequencing and checkpoint artifact for a Workprogram or Runprogram. It unifies
the order of operations, dependencies, and validation gates.

## Where it lives

Execution Spines live inside the program folder and are named:

`execution_spine.md`

## Required sections

Each Execution Spine MUST include:

1. Purpose and scope
2. Inputs and assumptions
3. Sequence (ordered steps)
4. Dependencies and handoffs
5. Checkpoints and validation gates (include per-milestone entry/exit criteria and go/no-go gates)
6. Outputs and artifacts
7. Status and last run notes (if applicable)

Execution Spines SHOULD reference their related planning-output source, spec, and registry paths to keep linkage
explicit.

## Lane semantics during spine execution

Execution Spines orchestrate lane handoffs across program milestones:

- `Coordinator` owns sequence ordering, dependency gates, and go/no-go decisions.
- `Executor` owns milestone task execution and output publication.
- `Builder` owns tool/config implementation milestones when present.
- `Reviewer` owns judgment-heavy milestone review and close-gate checks.
- `Linter` owns mechanical validation passes when a milestone requires them.

Lane labels are canonical execution semantics; profile/subagent labels are
implementation presets.

Per-milestone gate format (example):

```yaml
milestone_gate:
  name: "M1_extent_engine"
  entry_criteria:
    - condition: "Test-Path ../<work_repo>/02_Modules/gis_workflow/src/extent_engine.py"
      required: true
  exit_criteria:
    - condition: "pytest tests/test_extent_engine.py::test_basic_flow"
      required: true
  go_no_go_gate:
    type: "automated"
    command: "<validator_command>"
```

Execution Spines MUST NOT duplicate planning-output or spec content. Keep scope/rationale in workbook/runbook
Planning Outputs and requirements in the Program Spec; the spine is sequencing and gates only.

## CSCC context contract for spine-driven lanes

Before executing a milestone from an execution spine, a CSCC agent MUST verify:

- `execution_spine.md` is loaded and reflects current milestone status;
- linked program spec path is valid;
- linked registry path is valid and includes target packet/book;
- compacted context source is known (`README.md` at program or bundle level);
- current workbook/runbook path for the active milestone is valid.

If any context input is missing, stop execution and restore context artifacts before proceeding.

## Relationship to Program Spec

Execution Spines are paired with a Program Spec:

- Spec captures requirements and invariants.
- Spine captures the ordered execution path.

Use `00_Admin/guides/authoring/guide_spec.md` for spec authoring guidance.

## Minimal scaffold

```markdown
---
title: Execution Spine: <Program>
version: 0.1.0
status: active
last_updated: 2026-01-15
owner: ai_ops
---

## Execution Spine: <Program>

## Purpose and scope

## Inputs and assumptions

## Sequence

## Dependencies and handoffs

## Checkpoints and validation gates

## Outputs and artifacts

## Status and last run notes
```

## References

- `00_Admin/guides/authoring/guide_spec.md`
- `00_Admin/specs/spec_execution_orchestration.md`
