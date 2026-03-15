---
title: Guide: Workflows
version: 1.1.0
status: active
license: Apache-2.0
last_updated: 2026-03-14
owner: ai_ops
related:
- ./guide_ai_operations_stack.md
- ./guide_ai_ops_vocabulary.md
- ../authoring/guide_runbooks.md
- ../authoring/guide_workbooks.md
---

# Guide: Workflows

This guide defines **Workflows** and how they relate to Runbooks and Workbooks. It is normative.

Enforceable requirements live in `00_Admin/specs/spec_workflow_structure.md`. This guide provides advisory context;
if there is a conflict, the spec wins.

## Core definition

A **Workflow** describes how an outcome can be achieved at the intent level.

Characteristics:

- Reusable
- Describes patterns, not commitments
- References pipelines and contracts by ID or path

A Workflow MUST NOT:

- Lock assumptions
- Specify tools or code

## Relationship to runbooks and workbooks

Runbooks and Workbooks are workflow specializations defined by their primary axis:

- **Runbooks** are execution workflows (reusable, parameterized).
- **Workbooks** are commitment workflows (single-use, frozen after approval).

For authoring details, use the dedicated guides:

- `00_Admin/guides/authoring/guide_runbooks.md`
- `00_Admin/guides/authoring/guide_workbooks.md`

## Repository context

- Workbook index: `../<work_repo>/01_Resources/<domain_core>/ai_workbook_index.yaml`.
- Workbooks live in `90_Sandbox/ai_workbooks/`.
- Runbooks live in `00_Admin/runbooks/` (or module runbook folders).
  Key operational runbooks for workflow governance:
  - `rb_release_quality_gate_01.md` -- Pre-closeout release-quality checks
  - `rb_setup_smoke_matrix_01.md` -- Setup script help/dry-run verification
  - `rb_workflow_frontmatter_validation_01.md` -- Workflow frontmatter contract validation
  - `rb_codex_compat_mirror_01.md` -- Codex compatibility mirror maintenance
- Module metadata lives in `02_Modules/<module>/metadata/module.yaml`.

## Relationship to Specifications

- Workflows/Runbooks/Workbooks SHOULD reference Specs and Contracts by ID or path.
- Engine/phase specs (e.g., `spec_zoning_logic_engine_zle.md`) supply intent; Workbooks commit to runs against them.
- Contracts (e.g., `spec_contract_zle_to_fle_v0_1_0.md`) govern Verification and SHOULD be referenced where applicable.

Execution mechanics and index hierarchy are defined in:

- `00_Admin/specs/spec_execution_orchestration.md`
- `00_Admin/specs/spec_repository_indices.md`
- `00_Admin/specs/spec_workflow_structure.md`
- `00_Admin/specs/spec_runbook_structure.md`
- `00_Admin/specs/spec_workbook_structure.md`
- `00_Admin/specs/spec_workbundle_dependency_tracking.md`
- `00_Admin/specs/spec_workbundle_placement_suggestion.md`
- `00_Admin/specs/spec_infrastructure_change_validation_gate.md`

For CSCC-first workflow lanes:

- `/work` relevance-gate behavior should follow placement decision echo fields
  defined by `spec_workbundle_placement_suggestion.md`.
- workbook templates should include dependency declarations (`depends_on`,
  `affects`) aligned to `spec_workbundle_dependency_tracking.md`.
- closeout lanes should apply the infrastructure validation checklist when
  triggered by `spec_infrastructure_change_validation_gate.md`.

## Relationship summary

Terminology note: use single-token forms (`workbundle`, `workprogram`, `runbundle`, `runprogram`) in prose. Filenames
and prefixes remain unchanged unless explicitly revised by a separate refactor workbook. Folder paths remain
`work_program_*` / `run_program_*` for filesystem compatibility.

Workflow -> Runbook (reusable, execution) -> Runbundle -> Runprogram

Workflow -> Workbook (single-use, committed) -> Workbundle -> Workprogram

Runbundles provide the same grouping function for runbooks that Workbundles provide for workbooks, but they are not
interchangeable (different artifact types and locations).

## Pipeline Artifacts (Execution Queue)

Pipeline artifacts are optional execution-queue files used to sequence books and bundles without changing governance
authority.

Boundary rule:

- **Execution spine** remains the governance/commitment authority for sequencing gates.
- **Pipeline artifacts** are operational queue views for run execution.
- If both exist, update spine first, then align pipeline artifacts.

Creation rules:

- Create pipeline artifacts when one of these is true:
  - 3+ ordered steps must be run repeatedly.
  - A bundle/program has manual gates that benefit from explicit queue visibility.
  - Handoffs require a single "entrypoint" artifact for execution order.
- Skip pipeline artifacts for simple one- or two-step flows where README + runbook/workbook order is already obvious.

Placement and naming:

- Workbundle pipeline:
  - location: workbundle root
  - pattern: `wb_pipeline_<bundle_name>_<nn>.md`
  - template: `01_Resources/templates/workflows/workbundle_pipeline_template.md`
- Execution spine (workprogram authority source):
  - location: workprogram root
  - pattern: `execution_spine.md`
  - template: `01_Resources/templates/workflows/execution_spine_template.md`
- Workprogram pipeline:
  - location: workprogram root
  - pattern: `workprogram_pipeline_<nn>.md`
  - template: `01_Resources/templates/workflows/workprogram_pipeline_template.md`
- Runbundle pipeline:
  - location: runbundle root
  - pattern: `rnb_<bundle_name>_<nn>.md`
  - template: `01_Resources/templates/workflows/runbundle_pipeline_template.md`
- Runprogram pipeline:
  - location: runprogram root
  - pattern: `runprogram_pipeline_<nn>.md`
  - template: `01_Resources/templates/workflows/runprogram_pipeline_template.md`

Minimum section contract for pipeline artifacts:

1. Purpose
1. Inputs
1. Preconditions
1. Ordered Execution Queue
1. Manual Gates (if any)
1. Validation Commands
1. Outputs
1. Postconditions
1. References

Execution-oriented templates should include coordination metadata:

- `execution_mode`
- `depends_on`
- `shared_files`
- `lock_scope`

## Front Matter Profiles

Use these profiles to keep metadata aligned and avoid overloading every
artifact with execution-only fields.

<!-- markdownlint-disable MD013 -->
| Artifact Family | Always Include | Conditional Include | Avoid by Default |
| --- | --- | --- | --- |
| README templates (`workbundle`, `workprogram`, `runbundle`, `runprogram`) | `title`, `version`, `status`, `created`, `updated`, `owner`, `description`, `related` | `primary_axis`, `lifecycle` | `execution_mode`, `depends_on`, `shared_files`, `lock_scope` |
| Spine templates (`execution_spine`) | README profile + `id`, `primary_axis` | `lifecycle` | `execution_mode`, `depends_on`, `shared_files`, `lock_scope` |
| Pipeline templates (`workbundle/workprogram/runbundle/runprogram pipeline`) | spine profile + `execution_mode`, `depends_on`, `shared_files`, `lock_scope` | `primary_axis`, `lifecycle` | none |
| Workbook/runbook templates (`wb_*`, `rb_*`) | follow `guide_workbooks.md` / `guide_runbooks.md` front matter requirements + `model_profile` (`model:reasoning`) | coordination keys when parallel/ordering matters | n/a |
<!-- markdownlint-enable MD013 -->

Reference key normalization:

- Use `related` as the canonical cross-reference list key for new templates.
- `related_refs` remains validator-compatible for existing workbook surfaces
  during transition.

## Planning Outputs vs Program Spec vs Execution Spine

Keep these boundaries tight to avoid overlap:

<!-- markdownlint-disable MD013 -->
| Artifact | Primary Purpose | Contains | Must Not Contain |
| --- | --- | --- | --- |
| Planning Outputs (in workbook/runbook) | Scope + rationale for active lane | Assumptions, risks, success criteria, planning checklist | Ordered execution steps |
| Program Spec | Requirements | Invariants, requirements, acceptance criteria | Execution sequencing |
| Execution Spine | Sequencing + gates | Ordered steps, dependencies, validation gates, handoffs | Scope justification or requirements |
<!-- markdownlint-enable MD013 -->

If you need to pick one place for content, use this table. Recommended read order: Planning Outputs -> Program Spec ->
Execution Spine.

## Governance Boundary Reinforcement

This section reinforces placement without replacing canonical workflow content.

- Workflow governance is upstream.
- Downstream guides/templates consume upstream governance by reference.
- Downstream artifacts should capture local execution interpretation, not copy
  global governance prose.

Rule-location matrix:

- Cross-artifact governance rule -> `guide_workflows.md` and/or policy/spec.
- Workbook authoring interpretation -> `guide_workbooks.md`.
- Profile-specific execution checks -> workbook templates.
- Machine-checkable requirements -> spec + validator path.

Cycle-burden control:

- Keep one authoritative upstream governance location for each rule family.
- Keep local execution checks near execution surfaces (templates/workbooks).
- Reduce backtracking loops between upstream governance and downstream context.

Related specs for extended enforcement patterns:

- `00_Admin/specs/spec_governance_enforcement.md`
- `00_Admin/specs/spec_execution_orchestration.md`

## Placement Rules

- Runbundles live inside a Runprogram when one exists, under
  `run_program_<program_id>/run_bundles/rnb_<bundle_name>/` (with the bundle README plus its runbooks).
  If no Runprogram exists, runbundles MAY live alongside runbooks in
  `00_Admin/runbooks/` or `02_Modules/<module>/docs/runbooks/`.
- For scalable runbundles, keep runbooks inside the bundle at
  `runbooks/rb_*.md` and keep queue entries local to the bundle.

- Workbundles live inside a Workprogram when one exists, under
  `work_program_<program_id>/work_packets/wb_<id>_<YYYY-MM-DD>/`.
  If no Workprogram exists, workbundles MAY live under
  `90_Sandbox/ai_workbooks/wb_<id>_<YYYY-MM-DD>/`.
- Workprograms live under `90_Sandbox/ai_workbooks/work_program_<program_id>/`.
- Runprograms live under `00_Admin/runbooks/run_program_<program_id>/` or
  `02_Modules/<module>/docs/runbooks/run_program_<program_id>/`.
- Workprograms and Runprograms keep only program-level artifacts at the program root
  (spec/spine/registry/README).

Legacy note: older workprograms may use `wp_<program_id>_<YYYY-MM-DD>/`.
New workprograms SHOULD use `work_program_<program_id>/`. Workbundles SHOULD
use the canonical `wb_` prefix. If migrating legacy paths, use a dedicated
refactor workbook.

Naming decision rule:

| If the folder name is... | Artifact |
| --- | --- |
| `wb_<id>_<YYYY-MM-DD>/` | Workbundle (single-run container; may be nested) |
| `work_program_<program_id>/` | Workprogram (multi-workbook coordination) |

## Operational Workbundle Boundaries

Some workbundles operate adjacent to a workprogram without being part of its sequencing. These are
**operational workbundles** - endpoint-specific execution that may consume program outputs but maintains
independent status and scope.

### Boundary rules

| Aspect | Workprogram Workbundles | Operational Workbundles |
| --- | --- | --- |
| Location | Inside `work_program_*/work_packets/` | Standalone in `90_Sandbox/ai_workbooks/` |
| Sequencing | Governed by program spine | Independent |
| Dependencies | May depend on prior milestones | May consume program outputs but not block program |
| Status tracking | Program registry | Own task.md or README |
| Closeout | With program | Independent (may outlive program) |

### When to use operational workbundles

- Endpoint-specific work (e.g., stakeout, export, deployment) that uses program outputs
- Work that iterates faster than the parent program's milestone cadence
- Cross-cutting operational tasks that span multiple programs

### Deterministic placement rule

Use this decision order:

1. If work affects milestone sequencing or milestone deliverables -> keep inside
   workprogram workbundle.
2. If work is endpoint-specific and can evolve independently -> use adjacent
   operational workbundle.
3. If work crosses multiple programs but is operationally bounded -> use
   adjacent operational workbundle with explicit backlinks.

### Labeling requirement

Operational workbundles MUST be labeled in:

1. Their own README (state: "Adjacent operational workbundle, not part of [program] sequencing")
2. The program's workbooks_registry.md or README (reference with "Adjacent" label)
3. The program spec (if R11/R14 style rules apply)

### Artifact consumption

Operational workbundles MAY:

- Reference program runbooks/scripts as dependencies
- Copy program outputs as inputs
- Extend program patterns with endpoint-specific logic

Operational workbundles MUST NOT:

- Modify program artifacts without proposal
- Block program milestone progression
- Claim program-level status (e.g., "M3 complete")

### Relocation Example

When a workbundle was created in the wrong location:

1. Copy workbundle to correct target folder.
2. Verify copied files and references.
3. Leave pointer note in original location.
4. Remove original only after verification and pointer creation.

Use runbook:

- `00_Admin/runbooks/rb_packet_relocation_01.md`

Use base work-family templates:

- `01_Resources/templates/workflows/workbundle_readme_template.md`
- `01_Resources/templates/workflows/wb_template_generic.md`
- `01_Resources/templates/workflows/work_proposal_template.md` (Level 4 governance proposals)

Use pipeline templates when queue artifacts are warranted:

- `01_Resources/templates/workflows/workbundle_pipeline_template.md`
- `01_Resources/templates/workflows/workprogram_pipeline_template.md`
- `01_Resources/templates/workflows/runbundle_pipeline_template.md`
- `01_Resources/templates/workflows/runprogram_pipeline_template.md`

## Request Clarification Gate

If a request is vague or underspecified, stop and clarify before selecting artifacts or starting execution. Use this
minimum set:

- Desired outcome and deliverable
- Scope boundaries (in/out)
- Target artifact type (runbook/workbook/spec/pipeline/spine)
- Constraints (time, tools, data sources)
- Success criteria or acceptance checks

If scope expands during work, pause and reclassify authority. If it crosses into Level 3+, create a workbook/workbundle
and wait for approval.

Clarification decision rule:

- If any minimum clarification is missing, pause and ask.
- If the request could map to multiple artifact types, pause and ask.
- If the request hints at multi-step work or 3+ files, pause and ask.

### Candidate-Idea Maturation

When requestor input is an early-stage idea:

1. Capture candidate intent in one sentence.
2. Propose 1-3 concrete execution options with tradeoffs.
3. Confirm selected option and scope boundaries.
4. Convert selected option into workbook/runbook tasks before editing.

## Governance Rules

> **Warning — Strict Frontmatter Schema:** Workflow files in `.ai_ops/workflows/` use
> `additionalProperties: false` in `schema_workflow_frontmatter.yaml`. Only the declared
> fields (`name`, `description`, `kind`, `version`, `status`, `owner`, `license`, `claude`,
> `codex`, `exports`) are allowed. Adding any other field (including `last_updated`, `updated`,
> `tags`, etc.) will fail `validate_workflow_frontmatter.py`. Use `version` to signal changes;
> do not add date fields.

- Execution MUST follow current ai_ops authority and command contracts.
- Every Workbook SHOULD originate from a runbook/workflow lane.
- Level 4 changes MUST begin from an approved Work Proposal.
- Workbundle compacted context MUST stay synchronized at handoff checkpoints.
- Command wrappers MUST defer to `.ai_ops/workflows/*.md` as single source.
- After editing any `.ai_ops/workflows/*.md` file, run
  `python 00_Admin/scripts/generate_workflow_exports.py` before committing.
  The pre-commit export-drift check will block the commit if exports are stale.
- Verification failures keep artifact `status: active` until corrected.

Downstream enforcement surfaces (do not duplicate full procedural detail here):

- `/work`, `/crosscheck`, `/closeout`, `/health` workflows for execution order
  and task-local gates.
- workbook templates for pre-execution checks, verification, and selfcheck.
- specs/policies for authoritative machine-checkable contract definitions.

These distinctions separate **intent**, **commitment**, and **execution** while
reducing internal cycle burden.

## Emergency Autonomy Protocol

Use only when progress is blocked and delay would materially harm the work. Required phrase:

`EMERGENCY_AUTONOMY_APPROVED`

Trigger guidance: if conditions are met, the agent SHOULD propose invoking this protocol and request confirmation
before proceeding, unless immediate stabilization is required.

Trigger conditions (one or more):

- A blocking failure threatens data integrity or critical deadlines.
- A safety fix is needed to prevent cascading errors.
- The requestor is unavailable and delay would materially harm the work.

If time allows, the requestor SHOULD explicitly approve invocation. If immediate stabilization is required, invoke,
log, and notify as soon as possible.

When invoked:

1. Record the event in `00_Admin/logs/log_emergency_autonomy.md`.
2. Limit scope to the smallest safe fix.
3. Define a rollback trigger and mark its status.
4. Run validation and record outcomes.

If validation fails or the requestor flags scope drift, rollback is mandatory.

## Decision Tiers and Promotion

Decisions fall into two tiers:

- **Workbook-level**: run-specific decisions that do not affect repo-wide rules.
- **Repo-level**: cross-cutting governance, templates, or validation changes.

Promotion criteria (repo-level):

- Affects 2+ domains (guides/specs/policies/templates).
- Introduces or changes machine-checkable requirements.
- Alters canonical workflows or naming.

Repo-level decisions MUST be promoted to `00_Admin/decisions/` or `00_Admin/reports/`.

## Mid-Stream Agent Integration Protocol

When a new agent joins mid-run, it MUST:

1. Read the active workbook and workbundle README.
2. Confirm authority level and approval scope.
3. Revalidate scope boundaries and target files.
4. Review compacted context and last checkpoint.
5. Log a handoff note (what changed, what remains, what is blocked).

Do not continue execution until this checklist is complete.

## Agent Task Management Conventions

- **Internal notes** live in session artifacts or scratchpads inside the workbundle.
- Scratchpads may be used for ai_ops development and active `/work` sessions; they are temporary and must be
  distilled into canonical artifacts or future work entries.
- **Repo artifacts** (guides/specs/templates/logs) are the only long-lived records.

## Reference Thrift Rule

Keep references agent-friendly without creating long, noisy blobs:

- Prefer one parent directory pointer plus the 2-6 critical files for execution.
- Add per-file references only for files that are gate-authoritative,
  machine-validated, or frequent handoff entrypoints.
- Avoid listing every sibling file when a directory pointer already scopes
  discovery.
- Sync points: after scope changes, after validation, and before commit/push.

## Multi-Tier Agent Support

When mixing chat-only reasoning with repo artifacts:

- Conversation artifacts MUST be summarized into repo artifacts if they affect scope or decisions.
- Repo artifacts are canonical; conversations are ephemeral.

## Feedback Intake and Batch Triage

To avoid suggestion spam, use a single intake queue:

- `00_Admin/backlog/feedback_intake.md`
- `00_Admin/guides/ai_operations/guide_feedback_intake.md` (process guidance)

Batch triage weekly:

1. Accept: move to a workbook or future work entry.
2. Defer: keep in intake with a next-review date.
3. Reject: record rationale and close.

For cross-artifact policy/guide overlap notes, use:

- `00_Admin/guides/ai_operations/guide_alignment_notes.md`

## Artifact Escalation Triggers

- Scratchpad -> Workbook: 6+ edits or 3+ directories.
- Workbook -> Workbundle: supporting artifacts are required.
- Workbundle -> Workprogram: 3+ workbooks with shared objectives.

For explicit parallel-safety guardrails, see:

- `00_Admin/guides/ai_operations/guide_parallel_execution.md`

## Alignment Note Pattern

When guidance overlaps policy, add a short alignment note:

```markdown
> Alignment Note: This guide defers to `00_Admin/policies/<policy_name>.md` for enforcement.
```

## Execution Gate Order

Run these steps in order before commit/push:

1. Deliverables completed (files/artifacts created).
2. Verification checklist completed (intent and scope).
3. Automated validation (lint/validators/tests).
4. Requestor review gate closed (approval confirmed).
5. Commit/push.

## Handoff Payload

At each handoff (Coordinator -> Executor -> Validator), include a compacted context block per
`guide_ai_operations_stack.md`. When Level 4 applies, the handoff MUST include:

- `proposal_id`
- `target_files`
- `status_checksum`
- `validation_commands`

## Registry Guidance

Registry rules, promotion workflow, and maintenance guidance live in `00_Admin/guides/ai_operations/guide_workflow_registries.md`.
Use that guide as the single source of truth and keep registries lean (paths + metadata, not full inventories).

## AI Agent Quick Decision Matrix

<!-- markdownlint-disable MD013 -->
| Scenario | Primary Artifact | Required Companions | Placement |
| --- | --- | --- | --- |
| Single execution run | Workbook | Inline Planning Outputs if no plan | `90_Sandbox/ai_workbooks/wb_<id>.md` or workbundle |
| Workbook needs companions | Workbundle | README + workbook + required companions | `work_program_<id>/work_packets/wb_<id>_<YYYY-MM-DD>/` (or top-level if no program) |
| Reusable procedure | Runbook | Preconditions + postconditions + checklist | `00_Admin/runbooks/rb_<id>.md` |
| Informal runbook grouping | Runbundle | README + runbooks | `run_program_<id>/run_bundles/rnb_<bundle_name>/` (or top-level if no program) |
| Coordinated multi-workbook | Workprogram | Workbook Planning Outputs + Spec + Spine + Registry + README | `90_Sandbox/ai_workbooks/work_program_<program_id>/` |
| Coordinated multi-runbook | Runprogram | Spec + Spine + Registry + README | `00_Admin/runbooks/run_program_<program_id>/` |
<!-- markdownlint-enable MD013 -->

## Validator Alignment

When a Workflow, Runbook, or Workbook introduces or changes machine-checkable requirements, the same execution must
update the validator configuration that enforces those checks.

Requirements:

- Do not rely on inference; update the validator config explicitly in the same workbook/runbook.
- Only include requirements that are canonical and machine-checkable.
- Document the canonical source that each validator rule mirrors.

This keeps automated enforcement aligned with canonical requirements and prevents drift.
