---
title: Runbook: Workbundle Relocation
version: 0.1.0
status: active
license: Apache-2.0
created: 2026-02-03
updated: 2026-02-03
owner: ai_ops
ai_role: executor
description: Safe relocation procedure for workbundles/runbundles with verification and fallback.
---

# Runbook: Workbundle Relocation

## Purpose

Relocate a workbundle safely when it is created in the wrong location.

## Preconditions

- Source workbundle exists and target folder is known.
- No active destructive command is in progress.
- Requestor approved relocation scope.

## Inputs

- Source workbundle path
- Target workbundle path
- Whether pointer stub is required (default: yes)

## Steps

1. Copy source workbundle to target location.
1. Verify copied file count and key artifact presence (`README`, workbook/runbook).
1. Update internal references if required.
1. Create pointer note in source workbundle location.
1. Remove source workbundle only after verification passes.

## Windows Fallbacks (Access Denied)

- If remove fails with access denied:
  1. Close file handles (editor/processes).
  1. Retry deletion once.
  1. If still blocked, keep source workbundle and mark as pending cleanup.

## Outputs

- Workbundle at target path with validated structure.
- Pointer note at original path (or explicit no-pointer decision).
- Verification evidence in workbook/scratchpad.

## Validation Commands

```powershell
markdownlint <changed_paths>
python 00_Admin/scripts/validate_repo_rules.py --config 00_Admin/configs/validator/validator_config.yaml
```
