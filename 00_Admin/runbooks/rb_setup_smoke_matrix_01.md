---
title: "Runbook: Setup Smoke Matrix"
id: rb_setup_smoke_matrix_01
version: 0.1.0
status: active
license: Apache-2.0
created: 2026-02-23
updated: 2026-02-23
owner: ai_ops
---

# Runbook: Setup Smoke Matrix

## Purpose

Provide a minimal, explicit setup verification matrix when setup scripts or
workflow export plumbing changes.

## Scope

- Claude skills setup scripts
- Codex skills setup scripts
- Help and dry-run lanes only (no write-mode execution)

## Preconditions

- Run from `ai_ops/` repo root.
- Python is available if export generation checks are included in the same wave.

## Matrix

| Check | Command | Expected |
| --- | --- | --- |
| Claude setup help (Windows) | `.ai_ops\\setup\\setup_claude_skills.bat --help` | usage output |
| Claude setup dry-run (Windows) | `.ai_ops\\setup\\setup_claude_skills.bat --dry-run` | no writes |
| Codex setup help (Windows) | `.ai_ops\\setup\\setup_codex_skills.bat --help` | usage output |
| Codex setup dry-run (Windows) | `.ai_ops\\setup\\setup_codex_skills.bat --dry-run` | no writes |
| Claude setup help (bash) | `./.ai_ops/setup/setup_claude_skills.sh --help` | usage output |
| Claude setup dry-run (bash) | `./.ai_ops/setup/setup_claude_skills.sh --dry-run` | no writes |
| Codex setup help (bash) | `./.ai_ops/setup/setup_codex_skills.sh --help` | usage output |
| Codex setup dry-run (bash) | `./.ai_ops/setup/setup_codex_skills.sh --dry-run` | no writes |

## Blocked Lane Handling

If one shell lane is unavailable on the current host, record:

1. blocked lane (`bash` or `powershell/cmd`)
2. reason (tool/shell missing)
3. successful equivalent lane checks on available shell

Do not mark setup verification complete without this record.
