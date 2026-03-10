---
title: Spec - Workbundle Dependency Tracking
id: spec_workbundle_dependency_tracking
module: admin
version: 0.2.0
status: active
license: Apache-2.0
created: 2026-02-24
updated: 2026-03-04
owner: ai_ops
owners: ["ai_ops"]
ai_generated: true
description: Canonical dependency declaration contract for workbook and infrastructure impact tracking.
---

# Spec - Workbundle Dependency Tracking

## Purpose

Define a low-friction dependency tracking contract so agents can answer:

- what a workbook depends on
- what a workbook affects
- what other workbooks are impacted by infrastructure edits

## Scope

In scope:

- workbook-level dependency declarations
- infrastructure impact declarations
- minimal query contract for crosscheck and closeout

Out of scope:

- full graph database or external service
- automatic dependency inference from commit history

## Contract

Workbook frontmatter extension:

```yaml
depends_on:
  - wb_repo_process_hardening_01_2026-02-24
affects:
  artifacts:
    - ai_ops/00_Admin/scripts/lint.ps1
    - ai_ops/.ai_ops/workflows/closeout.md
  workbooks:
    - wp_multi_agent_plugin_architecture_01_2026-02-19
```

## Query Patterns

1. `what does this workbook depend on?` -> `depends_on`
2. `what does this workbook affect?` -> `affects`
3. `what workbooks depend on <artifact>?` -> search `affects.artifacts` across workbooks

## Validation Rules

- `depends_on` entries must resolve to existing workbook IDs in current repo scope.
- `affects.artifacts` paths must be repo-relative and exist at authoring time or include defer note.

## Adoption Guidance

- Workbook templates SHOULD include `affects` by default.
- `/closeout` SHOULD use `depends_on` + `affects` metadata during boundary checks.
- Schema enforcement MAY be staged; contract publication does not require immediate validator hard-fail.
