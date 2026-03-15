---
title: Runbook Structure Spec
id: spec_runbook_structure
module: admin
status: active
license: Apache-2.0
version: 0.1.1
created: 2026-01-31
last_updated: 2026-03-14
owner: ai_ops
ai_generated: true
---

<!-- markdownlint-disable-next-line MD025 MD041 -->
# Runbook Structure Spec

## 1. Purpose

Define enforceable structure, naming, and metadata rules for runbooks.

## 2. Scope

Applies to any file under `00_Admin/runbooks/` or module-specific runbook locations
(`02_Modules/<module>/runbooks/`).

## 3. Naming and Locations

### 3.1 File Naming

- Prefix: `rb_`
- Snake_case topic: `repo_maintenance_program`, `commit_push_streamlining`, etc.
- Optional suffix: `_01`, `_v2`, etc.
- Extension: `.md`

### 3.2 Directory

- Repo-level runbooks: `00_Admin/runbooks/`
- Module-specific runbooks: `02_Modules/<module>/runbooks/`
- Runbundles: `rnb_<bundle_name>/` folder containing grouped runbooks

### 3.3 Index

All repo-level runbooks MUST be listed in `00_Admin/runbooks/README.md` with applicability labels.

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

When runbooks are frequently executed together, group them in a runbundle:

- Folder: `rnb_<bundle_name>/`
- Required: `README.md` with purpose, inventory, and parallel work guidance

## 7. Versioning and Metadata

- Use semantic versions (0.1.0, 0.1.1, ...).
- Required front matter fields follow `spec_repo_metadata_standard.md`.
- Status values: `planned`, `stub`, `active`, `completed`, `deprecated` (no `draft`).
- `model_profile`: declares the AI model tier for runbook execution.
  - In **templates**: use tier-only descriptors (e.g., `"high"`,
    `"reasoning:high | standard:medium"`). Templates are provider-agnostic.
  - In **active runbooks**: provider-specific names are allowed
    (e.g., `"claude-sonnet-4.6:high"`).
  - See `00_Admin/guides/authoring/guide_runbooks.md` for authoring guidance.

## 8. Related References

- Authoring guide: `00_Admin/guides/authoring/guide_runbooks.md`
- Runbooks index: `00_Admin/runbooks/README.md`
- Workflow guide: `00_Admin/guides/ai_operations/guide_workflows.md`
- Vocabulary: `00_Admin/guides/ai_operations/guide_ai_ops_vocabulary.md`
