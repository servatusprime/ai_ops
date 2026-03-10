---
title: Guide: Changelog Conventions
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

# Guide: Changelog Conventions

## Purpose

Define consistent changelog expectations for workbook-driven updates.

## Location Rules

- Module-level changelogs live with their module docs.
- Workbundle-level change summaries live in `work_summary.md`.
- Do not duplicate the same change log entry across multiple files.

## Entry Format

Use concise entries:

```text
YYYY-MM-DD | scope | change summary | evidence path
```

## Minimum Content

- date
- impacted scope/path
- what changed
- verification/evidence pointer

## Promotion Rule

If a change affects canonical governance docs, mirror the result in the
appropriate guide/spec/policy and reference it from workbook selfcheck.
