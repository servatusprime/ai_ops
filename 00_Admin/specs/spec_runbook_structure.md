---
title: Runbook Structure Spec
id: spec_runbook_structure
module: admin
status: active
license: Apache-2.0
version: 0.2.1
created: 2026-01-31
last_updated: 2026-07-16
owner: ai_ops
ai_generated: true
spec_archetype: governance_spec
---

<!-- markdownlint-disable-next-line MD025 MD041 -->
# Runbook Structure Spec

## Purpose

Defines enforceable structure, naming, and metadata rules for runbooks in ai_ops and governed repos.

## 1. Purpose

Define enforceable structure, naming, and metadata rules for runbooks.

## 2. Scope

Applies to runbooks and their run-family composition metadata under
`00_Admin/runbooks/` or module-specific canonical homes. The module canonical
home is `02_Modules/<module>/docs/runbooks/`. A repository MUST NOT maintain a
second "legacy" runbook location as another valid discovery or authority path.

## 3. Naming and Locations

### 3.1 File Naming

- Prefix: `rb_`
- Snake_case topic: `repo_maintenance_program`, `commit_push_streamlining`, etc.
- Optional suffix: `_01`, `_v2`, etc.
- Extension: `.md`

### 3.2 Directory

- Repo-level runbooks: `00_Admin/runbooks/`
- Module runbooks: `02_Modules/<module>/docs/runbooks/`
- Runbundles: neutral `rnb_<bundle_name>/` homes; physical containment is optional

### 3.3 Index

All repo-level runbooks MUST appear in the mechanically checked human index at
`00_Admin/runbooks/README.md`. Graph-addressable run-family artifacts MUST also
resolve through the derived `00_Admin/runbooks/run_family_registry.yaml`.

## 4. Required Runbook Structure

Each runbook MUST include:

1. YAML front matter (see `spec_repo_metadata_standard.md`).
2. A visible top-level heading (`# Runbook: <name>`).
3. Sections covering:

- Purpose
- Preconditions
- Inputs
- Steps (ordered execution steps)
- Outputs
- Postconditions
- Validation

## 5. Execution Rules

- Runbooks are reusable and parameterized; they MUST NOT freeze one-off assumptions.
- One-off decisions belong in workbooks, not runbooks.

## 6. Runbundle Grouping

When runbooks are frequently executed together, compose them in a runbundle:

- Canonical home: one repo- or module-owned `rnb_<bundle_name>/` location
- Required: `README.md` and a colocated authoritative `manifest.yaml`
- Membership: outgoing `consumes` references owned by the runbundle
- Reuse: one runbook MAY be consumed by multiple runbundles without copying it
- Derived views: `consumed_by` and impact closure MUST NOT be hand-maintained authority

## 7. Run-Family Identity and Composition

Runbooks, runbundles, and runprograms that participate in the run-family graph
MUST follow `spec_artifact_graph_identity.md` and
`spec_run_family_composition.md`. Directory ancestry MUST NOT imply exclusive
ownership, membership, or gate authority. Colocated `manifest.yaml` files are
the only run-family machine authority and own outgoing edges; exact
run-instance locks and receipts remain separate from definitions.

## 8. Versioning and Metadata

- Use semantic versions (0.1.0, 0.1.1, ...).
- Required front matter fields follow `spec_repo_metadata_standard.md`.
- Status values: `planned`, `stub`, `active`, `completed`, `deprecated` (no `draft`).
- `model_profile`: declares the AI model tier for runbook execution.
  - In **templates**: use tier-only descriptors (e.g., `"high"`,
    `"reasoning:high | standard:medium"`). Templates are provider-agnostic.
  - In **active runbooks**: provider-specific names are allowed
    (e.g., `"claude-sonnet-4.6:high"`).
  - See `00_Admin/guides/authoring/guide_runbooks.md` for authoring guidance.
- `cost_governance:` (optional): quantitative cost governance levers for token budgets,
  model routing preferences, and alert thresholds. Applies to runbooks and runbundles.
  Absence means all values are `null` - agents apply thrift judgment without a hard
  budget constraint. See `00_Admin/specs/spec_cost_governance.md` for the full schema.

## 9. Related References

- Authoring guide: `00_Admin/guides/authoring/guide_runbooks.md`
- Runbooks index: `00_Admin/runbooks/README.md`
- Workflow guide: `00_Admin/guides/ai_operations/guide_workflows.md`
- Vocabulary: `00_Admin/guides/ai_operations/guide_ai_ops_vocabulary.md`
- Shared identity: `00_Admin/specs/spec_artifact_graph_identity.md`
- Run-family composition: `00_Admin/specs/spec_run_family_composition.md`

## Change Log

- 0.2.1 (2026-07-16): Removed indefinite legacy-location retention; one
  canonical home and one discovery route are required after migration.
- 0.2.0 (2026-07-16): Replaced containment authority with neutral canonical
  homes and consumer-owned many-to-many run-family composition.
- 0.1.2 (2026-05-05): Metadata normalized to declare spec_archetype.
  Existing version history remains in Git history and prior frontmatter dates.
