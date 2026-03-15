---
title: Workbook Structure Spec
id: spec_workbook_structure
module: admin
status: active
license: Apache-2.0
version: 0.2.3
created: 2026-01-31
updated: 2026-03-14
owner: ai_ops
ai_generated: true
---

<!-- markdownlint-disable-next-line MD025 MD041 -->
# Workbook Structure Spec

## 1. Purpose

Define enforceable structure, naming, and metadata rules for workbooks.

## 2. Scope

Applies to any file under `90_Sandbox/ai_workbooks/` or other locations explicitly documented as AI workbooks.

## 3. Naming and Locations

### 3.1 File Naming

- Prefix: `wb_`
- Snake_case topic: `gis_data_source_discovery`, `styles_library`, etc.
- Optional suffix: `_phase_1`, `_combined`, `_final`, etc.
- Extension: `.md`

### 3.2 Directory

- Active workbooks live in `90_Sandbox/ai_workbooks/`.
- Reusable templates live in `01_Resources/templates/workflows/`.

### 3.3 Workprogram Governance Artifacts

If a workprogram exists, it MUST include:

- Execution spine: `execution_spine.md`
- Program spec: `spec_<program_id>.md`
- Registry: `workbooks_registry.md`
- README: `README.md`

## 4. Required Workbook Structure

Each workbook MUST include:

1. YAML front matter (see `spec_repo_metadata_standard.md`).
2. A visible top-level heading (`# ...`).
3. Sections covering the following content (headings may be renamed but content is required):

- Scope and Authority
- Inputs and Preconditions
- Outputs and Targets
- Rules and Workflow
- Execution Steps
- Cold-Start execution contract
- Pre-Execution readiness gate
- Ordered execution queue
- Verification checklist
- Selfcheck results

Required gate behavior:

- Ordered execution queue MUST include a Phase 0 (cold-start + ambiguity stop gate).
- Workbook MUST include an explicit crosscheck stop marker before closeout.
- If no workbundle/workprogram README exists, workbook MUST include compacted context
  for handoff continuity.

Execution Steps content MUST include:

- At least one explicit decision gate (proceed/revise/pause/abort), and
- Evidence expectation for verification (file path + section or command output).

## 5. Deprecation and Replacement

- New workbook must list superseded workbook IDs near the top.
- Superseded workbooks should be deleted or replaced with a stub marked `status: deprecated` pointing to the new
  workbook.

## 6. Workbundle Closeout Summary

When a workbundle is closed, a `work_summary.md` MUST be added to the workbundle root summarizing scope, files
 touched, validation results, and follow-ups.

## 7. Versioning and Metadata

- Use semantic-ish versions (0.1.0, 0.1.1, ...). Increment when rules or targets change.
- Required front matter fields follow `spec_repo_metadata_standard.md`.
- Status values follow `policy_status_values.md` (use `completed` for finished work; reserve `deprecated` for
  superseded).
- `model_profile`: declares the AI model tier for workbook execution.
  - In **templates**: use tier-only descriptors (e.g., `"high"`,
    `"reasoning:high | standard:medium"`). Templates are provider-agnostic.
  - In **active workbooks and runbooks**: provider-specific names are allowed
    (e.g., `"claude-sonnet-4.6:high"`).
  - In **specs and guides**: document both levels; abstract tiers for templates,
    concrete names allowed in artifact examples.

## 8. Related References

- Authoring guide: `00_Admin/guides/authoring/guide_workbooks.md`
- Workbook template: `01_Resources/templates/workflows/wb_template_generic.md`
- Policies: `00_Admin/policies/`
- Specs: `00_Admin/specs/`
