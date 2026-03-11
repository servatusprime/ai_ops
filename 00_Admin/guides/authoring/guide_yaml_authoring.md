---
title: Guide: YAML Authoring
version: 1.0.1
status: active
license: Apache-2.0
last_updated: 2026-02-02
owner: ai_ops
related:
  - 00_Admin/guides/authoring/guide_json_authoring.md
  - 00_Admin/guides/authoring/guide_markdown_authoring.md
  - 00_Admin/guides/architecture/guide_repository_structure.md
  - 00_Admin/specs/spec_repo_metadata_standard.md
---

# Guide: YAML Authoring

YAML is the authoritative human-authored format for metadata in `<repo_name>`.

## Baseline Rules

- 2 spaces only; no tabs.
- UTF-8 with LF.
- Final newline required.
- No trailing spaces.
- No anchors unless required.

## Allowed Constructs

- Prefer block mappings.
- Avoid inline objects.
- Quote dates to avoid implicit typing.

## Module Metadata Pattern

```yaml
id: <module_code>
name: <module_name>
version: 0.1.0
owner: ai_ops
description: >
  Short module description.
depends_on: []
provides: []
tags: []
```

## Tooling

- Use yamllint.
- Use IDE YAML extension.
- Commit/push steps and lint execution are defined in
  `00_Admin/policies/policy_git_workflow_conventions.md`.
