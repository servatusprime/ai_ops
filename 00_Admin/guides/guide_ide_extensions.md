---
title: Guide: IDE Extensions (ai_ops)
version: 0.4.0
status: active
license: Apache-2.0
last_updated: 2026-02-25
owner: ai_ops
---

# Guide: IDE Extensions

## Purpose

Define the baseline IDE tooling add-ons for ai_ops and how to validate drift.

## Canonical Sources

- Workspace recommendations: `<workspace_root>/.vscode/extensions.json`
- Baseline rationale: `00_Admin/tooling/extensions.md`
- Validation script: `00_Admin/scripts/validate_ide_extensions.ps1`
- IDE behavior standards: this guide (supersedes `guide_ide_config.md`)

If there is any mismatch, treat workspace `.vscode/extensions.json` as the source
of truth and update this guide/tooling notes.

## Required (Baseline)

- Note: "Required" here means required for baseline ai_ops authoring/validation
  ergonomics, not required to run a specific AI model provider.
- Ruff: `charliermarsh.ruff`
- Prettier: `esbenp.prettier-vscode`
- markdownlint: `davidanson.vscode-markdownlint`
- EditorConfig: `editorconfig.editorconfig`
- Markdown All in One: `yzhang.markdown-all-in-one`
- YAML: `redhat.vscode-yaml`
- YAML Path: `smoore.yaml-path`
- GitLens: `eamodio.gitlens`
- GitHub PRs: `github.vscode-pull-request-github`
- Python: `ms-python.python`
- Pylance: `ms-python.vscode-pylance`
- Jupyter: `ms-toolsai.jupyter`
- SQLTools + PG Driver: `mtxr.sqltools`, `mtxr.sqltools-driver-pg`
- pgFormatter: `bradymholt.pgformatter`
- PowerShell: `ms-vscode.powershell`

## Recommended (Common Utility)

- Mermaid preview: `bierner.markdown-mermaid`
- Spell check: `streetsidesoftware.code-spell-checker`
- GIS quick viewers: `jumpinjackie.vscode-map-preview`, `randomfractalsinc.geo-data-viewer`
- XML tools (GIS templates): `dotjoshjohnson.xml`
- Regex helper: `chrmarti.regex`
- TODO index: `gruntfuggly.todo-tree`

## Optional (Situational)

- Model-specific AI assistants (choose what you use):
  - `openai.codex`
  - `anthropic.claude-code`
  - `google.geminicodeassist`
  - `openai.chatgpt`
- Copilot: `github.copilot`, `github.copilot-chat`
- Remote workflows: `ms-vscode-remote.remote-ssh`, `ms-vscode-remote.remote-containers`

## Audit Interpretation

- `Missing` means missing from the workspace recommendation baseline.
- `Extra/Untracked` is informational and allowed; these do not block ai_ops use.

## Validation and Install

From `ai_ops/` repo root:

```powershell
pwsh ./00_Admin/scripts/validate_ide_extensions.ps1
pwsh ./00_Admin/scripts/validate_ide_extensions.ps1 -InstallMissing
```

From workspace root:

```powershell
pwsh ./ai_ops/00_Admin/scripts/validate_ide_extensions.ps1
pwsh ./ai_ops/00_Admin/scripts/validate_ide_extensions.ps1 -InstallMissing
```

## IDE Behavior Standards

### Formatting and Lint Baseline

- Repo line length baseline is **120** (`ruff.toml`).
- Python formatting/linting baseline is Ruff + Pylance.
- Markdown and YAML formatting baseline is Prettier.
- Avoid deprecated/legacy IDE settings in workspace config.

### Troubleshooting

If formatting/lint behavior drifts:

1. Confirm file type and expected formatter.
2. Run `Format Document`/`Format Document With...` to verify active formatter.
3. Re-check workspace extensions with `00_Admin/scripts/validate_ide_extensions.ps1`.
4. Confirm repo lint config files are present and unchanged.

## Change Rule

- Update `.vscode/extensions.json` first.
- Then update `00_Admin/tooling/extensions.md` and this guide.
- Keep Required minimal to reduce onboarding friction.
