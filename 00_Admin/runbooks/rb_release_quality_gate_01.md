---
title: "Runbook: Release-Quality Gate"
id: rb_release_quality_gate_01
version: 0.1.1
status: active
license: Apache-2.0
created: 2026-02-22
updated: 2026-02-26
owner: ai_ops
---

# Runbook: Release-Quality Gate

## Purpose

Provide one canonical command path for pre-closeout quality validation of:

1. Repo validator rules.
2. Workflow frontmatter contract validation.
3. Workflow export drift.
4. Lint pipeline (no-fix mode).
5. Profile regeneration determinism check (dry-run).

## When to Run

Run this gate before closeout when any of the following are true:

1. Workflow/source-contract edits under `.ai_ops/workflows/`.
2. Setup/export script edits under `.ai_ops/setup/` or `00_Admin/scripts/`.
3. Wrapper/plugin generation changes under `plugins/ai-ops-governance/`.
4. Any workbook wave where crosscheck requires strict reconciliation evidence.

## Command

Run from repo root:

```powershell
python 00_Admin/scripts/run_release_quality_gate.py
```

## Dry-Run Preview

```powershell
python 00_Admin/scripts/run_release_quality_gate.py --dry-run
```

## Optional Flags

- `--skip-lint`: skip `00_Admin/scripts/lint.ps1` when PowerShell is unavailable
  (must be documented in workbook friction log).
- `--profile <path>`: pass explicit profile source path to the profiles check.
- `--model-family <name>`: pass explicit model family to the profiles check.

## Expected Result

- Exit code `0` and `[RESULT] release-quality gate: PASS`.
- Non-zero exit indicates the first failing lane and should block closeout.

## Notes

- This runbook does not commit or push.
- The profiles lane runs `regenerate_profiles.py --dry-run` and does not write files.
