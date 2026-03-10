---
title: Module Metadata Standards Policy
version: 0.1.0
updated: 2025-12-02
status: stub
license: Apache-2.0
---
<!-- markdownlint-disable MD025 -->

# Module Metadata Standards Policy

## Purpose

Establish initial rules for `module.yaml` files.

## Minimum Fields

- `id` must match the module folder name (e.g., `gis_workflow`).
- Include: `id`, `name`, `description`.
- Include `spec` with path and `req_prefix`.
- Include `requirements_matrix` with path and status.
- Include `prompts` array; each prompt entry has `id`, `path`, `status` (role optional).
- All status fields must use: planned, stub, active, completed, deprecated.

## TODO

- _TODO (AI): Expand with full field definitions, validation rules, and examples._
