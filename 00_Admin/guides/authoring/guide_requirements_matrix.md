---
title: Guide: Requirements Matrix
version: 0.1.0
status: active
license: Apache-2.0
last_updated: 2026-02-03
owner: ai_ops
related:
  - ./guide_workbooks.md
  - ../ai_operations/guide_workflows.md
  - 00_Admin/specs/spec_repo_metadata_standard.md
---

# Guide: Requirements Matrix

## Purpose

Standardize requirements matrix usage for traceable execution and validation.

## When to Use

- Multi-step efforts with explicit acceptance requirements.
- Workprogram milestones needing requirement-to-output traceability.

## Recommended Columns

- requirement_id
- source (spec/plan/workbook)
- owner
- status
- evidence_path
- last_updated

## Update Cadence

- Update matrix when requirement status changes.
- Refresh evidence paths before closeout.

## Placement

- Module-specific matrices live in module docs.
- Program-level matrices live in the program root.
