---
title: Workbook Structure Spec
id: spec_workbook_structure
module: admin
status: active
license: Apache-2.0
version: 0.3.1
created: 2026-01-31
updated: 2026-11-04
owner: ai_ops
ai_generated: true
spec_archetype: governance_spec
related:
  - ../guides/authoring/guide_workbooks.md
  - ../../01_Resources/templates/workflows/wb_template_generic.md
---

<!-- markdownlint-disable-next-line MD025 MD041 -->
# Workbook Structure Spec

## Purpose

Defines enforceable structure, naming, and metadata rules for workbooks in ai_ops and governed repos.
Used by the validator and as the authoritative authoring contract alongside `guide_workbooks.md`.

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

### 3.4 Dogfood Execution Authority

When a workbook edits governance files that will be consumed during the same
execution session (dogfood pattern), the executing agent MUST record in Phase 0
which file version is authoritative - working-tree or last committed.

- **Working-tree files are authoritative** for agents running in the same session
  where those files were written. The committed state is stale for that session.
- **Committed state is authoritative** for agents bootstrapping fresh in a new
  session where no in-session writes have occurred.
- Record the authority boundary explicitly in Phase 0 when dogfood execution is
  expected. Example: "WB03 changes are in working tree (uncommitted); this run
  executes against working-tree state as authoritative."

## 4. Required Workbook Structure

This section is the one normative home for required workbook sections; `work.md`,
`guide_workbooks.md` and the workbook template point here.

Each workbook MUST include:

1. YAML front matter (see `spec_repo_metadata_standard.md`), including `ai_role`.
2. A visible top-level heading (`# ...`).
3. These five headings, exactly as written. VS024 in `validator_config.yaml` pins them,
   and governed repos pin the same headings in their own validators, so a change here
   changes those pins together:
   - `## Cold-Start Execution Contract`
   - `## Pre-Execution Readiness Gate`
   - `## Ordered Execution Queue`
   - `## Verification Checklist`
   - `## Selfcheck Results`

Reviewer-checked content (headings may be renamed or merged): scope and authority,
inputs and preconditions, outputs and targets, rules and workflow, execution steps.

Required gate behavior:

- The Ordered Execution Queue MUST include a Phase 0 (cold start and ambiguity stop gate).
- The workbook MUST include an explicit crosscheck stop marker before closeout.
- If no workbundle or workprogram README exists, the workbook MUST include compacted
  context for handoff continuity.
- The expanded `## Execution Topology Contract` block is required only for material
  delegation as `AGENTS.md` defines it; otherwise it is omitted and the frontmatter lane
  fields stay as they are.
- The section check run by `/work` reports a malformed or unknown topology, lane or
  delegation value and stops the workbook. VS024 also validates the frontmatter
  vocabulary and required routing fields; the expanded material-delegation body
  block remains reviewer-checked.

Execution Steps content MUST include:

- At least one explicit decision gate (proceed, revise, pause or abort), and
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
- `cost_governance:` (optional): quantitative cost governance levers for token budgets,
  model routing preferences, and alert thresholds. Applies to workbooks, workbundles,
  and workprograms. Absence means all values are `null` - agents apply thrift judgment
  without a hard budget constraint.
  See `00_Admin/specs/spec_cost_governance.md` for the full schema.

## 8. Related References

- Authoring guide: `00_Admin/guides/authoring/guide_workbooks.md`
- Workbook template: `01_Resources/templates/workflows/wb_template_generic.md`
- Policies: `00_Admin/policies/`
- Specs: `00_Admin/specs/`

### 8.1 Cross-Repo Path Rules

The following rules apply to all `related_refs` entries in ai_ops workbooks:

(a) Entries must be repo-relative (e.g., `00_Admin/guides/...`) or use a `../` prefix for
cross-repo references. The patterns `../ai_ops/...` and `../<work_repo>/...` are accepted.

(b) Absolute paths are forbidden. Entries starting with `/`, a drive letter (e.g., `C:\`,
`D:\`), or any machine-specific root must not appear in `related_refs`.

(c) Mixing repo-relative and workspace-absolute paths in the same `related_refs` block is
forbidden. All entries in a block must use the same path anchor convention.

(d) An entry may carry one of two labels: `must_read` (needed to execute) or `may_consult`
(background). This rule moved here from `context_routing.yaml`
`policy.related_refs_classification` (2026-11-04).

## Change Log

- 0.3.1 (2026-11-06): VS024 validates workbook frontmatter routing vocabulary;
  the material-delegation body contract remains reviewer-checked.
- 0.3.0 (2026-11-04): Section 4 is the one home for required workbook sections and pins
  exactly the five VS024 headings; the other content areas are reviewer-checked; the
  topology block is required only for material delegation.
- 0.2.5 (2026-05-05): Metadata normalized to declare spec_archetype.
  Existing version history remains in Git history and prior frontmatter dates.
