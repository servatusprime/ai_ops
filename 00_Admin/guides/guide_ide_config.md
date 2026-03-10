---
title: IDE Configuration Standards
version: 0.1.0
status: stub
license: Apache-2.0
last_updated: 2026-01-12
owner: ai_ops
---

# IDE Configuration Standards

This guide explains the IDE configuration for <repo_name> and what to expect when editing files.

## 1. Line Length Standard

- Repo-wide maximum line length is **120 characters**.
- Enforced by authoring guides, editor rulers, Prettier (`printWidth`), and Ruff (`line-length`).

## 2. Python Format & Lint Policy (Hybrid Model)

### 2.1 Ruff

- Runs automatically for `.py` files per Ruff IDE defaults.
- Provides formatting, linting, import ordering, and bug detection (flake8-bugbear).
- Do not use deprecated Ruff settings (for example `ruff.lint.run`) in workspace config.

### 2.2 Mypy

- Remains the **only** type checker.
- Reports type issues separately from Ruff.

### 2.3 Formatter Choice

- Black is retired for day-to-day editing: `python.formatting.provider` is set to `none`.
- Ruff is the default Python formatter in IDE.

## 3. Markdown & YAML Formatting

- Formatted exclusively by Prettier.
- Scoped to `.md`, `.yml`, `.yaml` via language-specific settings.

## 4. Extension Interaction Levels

### 4.1 Runs Automatically (Background)

- EditorConfig
- Ruff
- Pylance
- YAML (Red Hat)
- markdownlint
- Code Spell Checker

### 4.2 Used Only for Certain File Types

- Prettier - formatting Markdown and YAML
- Markdown All in One - workbooks and guides
- YAML Path - navigating large manifests
- XML Tools - editing `.qml`, `.qpt`, and other XML styles
- SQLTools - interacting with Postgres from IDE
- Jupyter - when working with notebooks

### 4.3 Used Intentionally

- Codex - executing AI Workbooks and large refactors
- GitLens - exploring history and blame
- Todo Tree - scanning TODO/FIXME notes

## 5. Troubleshooting Formatting

If formatting looks wrong:

1. Check the file type and expected formatter (Ruff for Python; Prettier for MD/YAML).
2. Run `Format Document` or `Format Document With...` to confirm the active formatter.
3. Verify settings in `.vscode/settings.json` match this guide before changing global IDE prefs.
