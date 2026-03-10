---
title: tooling_extensions
version: 0.1.0
status: active
author: chatgpt
owner: ai_ops
created: 2026-02-25
updated: 2026-02-25
ai_generated: true
core_doc_exempt: false
---

# IDE Extensions — Repo Baseline

> This document explains _why_ each extension is recommended and how we audit them.

## Tiers

### Required (baseline)

- Note: "Required" means baseline tooling for ai_ops authoring/validation.
  It does not imply a specific model provider is required.
- Ruff (`charliermarsh.ruff`) — fast Python linting
- Prettier (`esbenp.prettier-vscode`) — consistent formatting
- markdownlint (`davidanson.vscode-markdownlint`) — Markdown standards
- EditorConfig (`editorconfig.editorconfig`) — cross-editor consistency
- Markdown All in One (`yzhang.markdown-all-in-one`) — authoring QoL
- YAML (`redhat.vscode-yaml`) — schema-aware YAML editing
- YAML Path (`smoore.yaml-path`) — YAML navigation/copy paths
- GitLens (`eamodio.gitlens`) & GitHub PRs (`github.vscode-pull-request-github`)
- Python (`ms-python.python`) & Pylance (`ms-python.vscode-pylance`)
- Jupyter (`ms-toolsai.jupyter`) — notebooks for data/GIS helpers
- SQLTools (`mtxr.sqltools`) + Postgres driver (`mtxr.sqltools-driver-pg`)
- pgFormatter (`bradymholt.pgformatter`) — readable Postgres SQL
- PowerShell (`ms-vscode.powershell`) — scripts/automation

### Recommended (GIS / <repo_name>)

- Map Preview (`jumpinjackie.vscode-map-preview`) — quick GeoJSON/KML preview
- Geo Data Viewer (`randomfractalsinc.geo-data-viewer`) — alt/companion spatial viewer
- Markdown Mermaid (`bierner.markdown-mermaid`) — sequence/flow diagrams
- Regex Previewer (`chrmarti.regex`) — faster text wrangling
- Spell Checker (`streetsidesoftware.code-spell-checker`) — prose quality
- XML Tools (`dotjoshjohnson.xml`) — QGIS templates
- TODO Tree (`gruntfuggly.todo-tree`) — index TODO/FIXME markers

### Optional (situational)

- Model-specific AI assistants (choose one or none):
  - `openai.codex`
  - `anthropic.claude-code`
  - `google.geminicodeassist`
  - `openai.chatgpt`
- GitHub Copilot (`github.copilot`), Copilot Chat (`github.copilot-chat`) — licensed AI assist
- Remote SSH (`ms-vscode-remote.remote-ssh`) — remote PostGIS/QGIS hosts
- Dev Containers (`ms-vscode-remote.remote-containers`) — containerized stacks

## How we audit & install

- IDE auto-prompts using `.vscode/extensions.json`.
- Script audit:

  ```powershell
  pwsh ./00_Admin/scripts/validate_ide_extensions.ps1
  pwsh ./00_Admin/scripts/validate_ide_extensions.ps1 -InstallMissing
  ```

## Update policy

- Adjust only via PRs with rationale.
- Keep **Required** lean (onboarding speed), move extras to **Recommended/Optional**.
- Extra/untracked installed extensions are allowed; treat them as informational
  unless they cause conflicts.
