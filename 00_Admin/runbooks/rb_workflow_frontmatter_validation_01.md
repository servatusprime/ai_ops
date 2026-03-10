---
title: "Runbook: Workflow Frontmatter Validation"
id: rb_workflow_frontmatter_validation_01
version: 0.1.0
status: active
license: Apache-2.0
created: 2026-02-23
updated: 2026-02-23
owner: ai_ops
---

# Runbook: Workflow Frontmatter Validation

## Purpose

Validate `.ai_ops/workflows/*.md` frontmatter against the canonical workflow
contract (required keys, types, and export mappings).

## Command

Run from repo root:

```powershell
python 00_Admin/scripts/validate_workflow_frontmatter.py
```

## Validation Scope

- required top-level workflow keys
- key type checks for `claude`, `codex`, and `exports`
- file-stem/name alignment
- expected constants (`kind`, `owner`, `license`)
- export skill-name alignment

## Expected Result

- Exit code `0` with `[OK] workflow frontmatter validation passed`.
- Non-zero exit blocks closeout until the frontmatter contract is corrected.

## Canonical References

- `00_Admin/configs/validator/schema_workflow_frontmatter.yaml`
- `00_Admin/scripts/validate_workflow_frontmatter.py`
