---
title: Naming Conventions Policy
version: 0.1.1
updated: 2026-03-24
status: active
license: Apache-2.0
related:
- ../guides/architecture/guide_naming_conventions.md
- ../guides/architecture/guide_naming_architecture.md
---
<!-- markdownlint-disable MD025 -->

# Naming Conventions Policy

## Purpose

Establish the canonical naming rules for files, folders, identifiers, and requirement IDs used across the repo.

## Rules

- Folder and file names: lower_snake_case.
- Module IDs: lower_snake_case and must match the module folder name.
- YAML keys: lower_snake_case.
- Prompt IDs: lower_snake_case.
- Python identifiers: lower_snake_case (PEP 8).
- Requirement IDs (only allowed exception): `REQ_<module_code>_<numeric_id>` (e.g., `REQ_gis_workflow_0001`).
- Prohibited naming styles: camelCase, PascalCase, kebab-case, StudlyCase, or other mixed-case schemes.
- The REQ ID format above is the only approved deviation from lower_snake_case.
