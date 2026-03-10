---
title: Guide: Markdownlint Handling
version: 0.1.0
status: active
license: Apache-2.0
last_updated: 2026-02-03
owner: ai_ops
related:
  - ../authoring/guide_markdown_authoring.md
  - ../../runbooks/rb_repo_validator_01.md
---

# Guide: Markdownlint Handling

## Purpose

Define consistent markdownlint execution and exception handling.

## Standard Execution

- Use repo script when available (`run_markdownlint.ps1`).
- Lint changed paths first; run full pass when requested.

## Failure Handling

- Fix rule violations in scope.
- If tooling environment fails (for example pre-commit cache permission issue),
  use direct `markdownlint` CLI fallback.
- Record fallback usage in workbook evidence.

## Exception Policy

- Prefer content fixes over disables.
- Use narrow rule-disable blocks only when necessary and justified.
- Avoid file-wide disables for new artifacts.
