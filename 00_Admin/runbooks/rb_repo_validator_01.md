---
title: Runbook: Repo Validator
version: 1.2.0
status: active
license: Apache-2.0
created: 2026-01-13
updated: 2026-03-09
owner: ai_ops
related:
  - 00_Admin/configs/validator/validator_config.yaml
  - 00_Admin/scripts/validate_repo_rules.py
  - 00_Admin/specs/spec_repo_metadata_standard.md
---
<!-- markdownlint-disable MD013 -->
<!-- markdownlint-disable-next-line MD025 -->
# Runbook: Repo Validator

## Purpose

Run the repo validator after drafting new documents or completing heavy edits to catch structural issues early.

## When to Run

- After drafting a new document.
- After a heavy edit batch (6+ files or 3+ directories).
- Before requesting review.

Optional:

- Run via pre-commit on-demand hook (`--hook-stage manual`).

Fast path:

- If only Markdown changed, run markdownlint only.
- If only YAML changed, run yamllint only.

## External Repo Fallback

If the target repo does not include ai_ops validator scripts:

- Run the repo's documented lint/validation steps (if any).
- If no lint rules exist, run a minimal check:
  - `markdownlint` (if config exists)
  - `yamllint` (if config exists)
  - Repo-specific tests (if documented)
- Report what ran and what was skipped.

## How to Run

From repo root:

```powershell
python 00_Admin/scripts/validate_repo_rules.py --config 00_Admin/configs/validator/validator_config.yaml
```

Markdown lint (run on changed paths):

```powershell
markdownlint <changed_paths>
```

If canonical files or directories were added or removed, refresh structure maps:

```powershell
00_Admin/scripts/generate_repo_structure.ps1
```

Manual pre-commit hook:

```powershell
pre-commit run re-projects-validator --hook-stage manual
```

## Interpreting Results

- Errors: must fix before commit.
- Warnings: investigate and fix when feasible, or document in commit/push summary.

## Validator Rule Pointers

Use this runbook as the operational entry point for rule-related questions.

- Canonical rule source:
  `00_Admin/configs/validator/validator_config.yaml`
- Rule engine:
  `00_Admin/scripts/validate_repo_rules.py`
- Metadata field contract:
  `00_Admin/specs/spec_repo_metadata_standard.md`

Quick rule discovery (read-only):

```powershell
Select-String -Path 00_Admin/configs/validator/validator_config.yaml -Pattern "code:|description:"
```

## Monorepo Baseline (Current Canonical Path)

Cross-repo flag mode is not implemented. Canonical execution is per-repo:

1. Run validator in `ai_ops` from the `ai_ops` root.
2. Run validator in the governed repo from that repo root.
3. Capture any command divergences explicitly in workbook evidence.

Example baseline:

```powershell
Write-Host "ai_ops"
powershell -NoProfile -ExecutionPolicy Bypass -File 00_Admin/scripts/run_markdownlint.ps1 <changed_paths>
python 00_Admin/scripts/validate_repo_rules.py --config 00_Admin/configs/validator/validator_config.yaml

Write-Host "governed_repo"
powershell -NoProfile -ExecutionPolicy Bypass -File 00_Admin/scripts/run_markdownlint.ps1 <changed_paths>
python 00_Admin/scripts/validate_repo_rules.py --config 00_Admin/configs/validator/validator_config.yaml
```

See `00_Admin/configs/validator/validator_config.yaml` for planned XR* roadmap
rules.

## Baseline Sync Helper (ai_ops -> governed repos)

Use the helper when validator baseline files in a governed repo drift from
`ai_ops` canonical versions:

```powershell
python 00_Admin/scripts/sync_validator_baseline.py --targets ../<governed_repo>
```

Dry-run preview:

```powershell
python 00_Admin/scripts/sync_validator_baseline.py --targets ../<governed_repo> --dry-run
```

The helper syncs:

- `00_Admin/scripts/validate_repo_rules.py`
- `00_Admin/scripts/run_markdownlint.ps1`
- `00_Admin/configs/validator/validator_config.yaml`
- `00_Admin/runbooks/rb_repo_validator_01.md`

## Outputs

The validator prints a list of errors and warnings to stdout. No files are modified.
