---
title: "Runbook: Codex Compatibility Mirror"
id: rb_codex_compat_mirror_01
version: 0.1.0
status: active
license: Apache-2.0
created: 2026-02-22
updated: 2026-02-23
owner: ai_ops
---

# Runbook: Codex Compatibility Mirror

## Purpose

Generate Codex compatibility mirror wrappers in `.codex/skills` only when
explicitly needed.

Default Codex policy in ai_ops is:

- primary: `.agents/skills`
- compatibility mirror: on-demand via `--compat`

## Preconditions

- Run from repo root.
- `.ai_ops/workflows/*.md` exists.
- Python is available.

## Repo-Scoped Compatibility Install

```powershell
.ai_ops\setup\setup_codex_skills.bat --repo --compat
```

```bash
./.ai_ops/setup/setup_codex_skills.sh --repo --compat
```

## User-Scoped Compatibility Install

```powershell
.ai_ops\setup\setup_codex_skills.bat --user --compat
```

```bash
./.ai_ops/setup/setup_codex_skills.sh --user --compat
```

## Force Regeneration

Use `--force` when wrappers must be overwritten:

```powershell
.ai_ops\setup\setup_codex_skills.bat --repo --compat --force
```

```bash
./.ai_ops/setup/setup_codex_skills.sh --repo --compat --force
```

## Verification

Confirm expected folders exist:

- repo scope: `.codex/skills/<workflow>/SKILL.md`
- user scope: `$HOME/.codex/skills/<workflow>/SKILL.md`

Run drift check after generation:

```powershell
python 00_Admin/scripts/check_workflow_exports_drift.py
```

## Notes

- Do not use compatibility mirror as default install target.
- Keep `.agents/skills` as canonical Codex path in this repo.
