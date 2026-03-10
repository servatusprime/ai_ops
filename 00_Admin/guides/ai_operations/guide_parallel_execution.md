---
title: Guide: Parallel Execution
version: 0.1.0
status: active
license: Apache-2.0
last_updated: 2026-02-03
owner: ai_ops
related:
  - ./guide_workflows.md
  - ../authoring/guide_workbooks.md
---

# Guide: Parallel Execution

## Purpose

Define safe parallel execution guardrails for multi-artifact work.

## Preconditions

- Parallel work must be explicitly requested or approved.
- Shared-file contention must be identified first.

## Required Metadata

Use workbook/runbook frontmatter:

- `execution_mode`
- `depends_on`
- `shared_files`
- `lock_scope`

## Safety Rules

1. Do not run parallel edits on the same file unless `lock_scope` is managed.
2. Keep one source of truth for status (active workbook or spine).
3. Re-sync compacted context at each merge checkpoint.
4. Run validation after each parallel branch merges.

## Stop Conditions

- conflicting edits on shared files
- unresolved blocker in any branch
- scope expansion beyond approved boundaries
