---
title: Workflow Structure Spec
id: spec_workflow_structure
module: admin
status: active
license: Apache-2.0
version: 0.2.2
created: 2026-01-31
updated: 2026-02-17
owner: ai_ops
ai_generated: true
---

<!-- markdownlint-disable-next-line MD025 MD041 -->
# Workflow Structure Spec

## 1. Purpose

Define enforceable structure and naming rules for workflow definitions.

## 2. Scope

Applies to workflow definitions referenced in `00_Admin/guides/ai_operations/guide_workflows.md` and any workflow
templates in `01_Resources/templates/`.

## 3. Required Structure

Each workflow definition MUST include:

1. Intent (outcome, no commitments).
2. Pattern (ordered intent-level steps).
3. Generates (runbooks or workbook patterns produced).
4. References (specs, contracts, or modules referenced).
5. Notes (constraints on usage).

Workflows SHOULD also name at least two decision gates (intent-level only):

- Gate 1: inputs/assumptions confirmed.
- Gate 2: outputs verified against acceptance criteria.

These gates remain tool-agnostic; execution evidence belongs in runbooks/workbooks.

## 4. Naming and Locations

### 4.1 Workflow Templates

- Location: `01_Resources/templates/workflows/`
- Naming: descriptive (e.g., `<workflow_name>_template.md`)

### 4.2 Workflow Definitions

- Canonical workflow patterns are documented in `00_Admin/guides/ai_operations/guide_workflows.md`.
- Module-specific workflows live in module docs.

## 5. Versioning and Status

- Workflow templates use semantic versions in front matter.
- Status values: `planned`, `stub`, `active`, `completed`, `deprecated` (no `draft`).

## 6. Related References

- Workflow guide: `00_Admin/guides/ai_operations/guide_workflows.md`
- Runbook spec: `00_Admin/specs/spec_runbook_structure.md`
- Workbook spec: `00_Admin/specs/spec_workbook_structure.md`
- Vocabulary: `00_Admin/guides/ai_operations/guide_ai_ops_vocabulary.md`
