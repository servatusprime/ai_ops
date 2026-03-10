---
title: Project Directory Template
version: 1.0.0
status: active
license: Apache-2.0
owner: ai_ops
created: 2026-02-27
updated: 2026-02-27
---

# Project Directory Template

## Purpose

Define a canonical project "suitcase" layout for bounded deliverables in governed repos.
This pattern is optional in ai_ops core but recommended when external repos need
project-scoped work with inputs, outputs, and run provenance.

## Canonical Folder Name

Use `Projects/` (no numeric prefix) as the default container in governed repos.
If a repo prefers numbered top-level directories, `04_Projects/` is an optional
convention, not a requirement.

## Suitcase Structure

```text
Projects/
  <project_name>/
    00_Admin/
      run_logs/
        README.md
    docs/
    inputs/
    outputs/
    README.md
```

## README.md Template

Include these sections in each project README:

- **Scope**: one-paragraph statement of what the project delivers.
- **Inputs**: data sources or required artifacts.
- **Outputs**: expected deliverables (paths and formats).
- **Run Logs**: pointer to `00_Admin/run_logs/` for execution evidence.
- **Owners**: primary contact or team.
- **Status**: active, paused, completed.

## Run Logs

Store execution evidence in `00_Admin/run_logs/`:

- daily execution notes
- validation outputs
- provenance snapshots

## Trigger

Use this template when:

- a governed repo needs scoped deliverables over time
- multiple workstreams must remain isolated
- execution evidence needs a per-project log trail

## Repo Rule

- Keep project inputs/outputs under the project folder.
- Do not store secrets in project directories.
- Reference `00_Admin/guides/architecture/guide_repository_structure.md` for
  global layout rules and exceptions.
