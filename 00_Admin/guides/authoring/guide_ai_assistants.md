---
title: AI Assistant Authoring Guide (External)
version: 0.1.0
status: active
license: Apache-2.0
last_updated: 2026-01-24
owner: ai_ops
related:
- ./guide_markdown_authoring.md
- ./guide_workbooks.md
- 00_Admin/specs/spec_workbook_structure.md
- 00_Admin/specs/spec_repo_metadata_standard.md
- ./guide_yaml_authoring.md
- ./guide_json_authoring.md
- ./guide_python_authoring.md
- ../<work_repo>/02_Modules/gis_workflow/docs/guides/guide_pyqgis_authoring.md
- ./guide_sql_authoring.md
---

# AI Assistant Authoring Guide (External)

## Purpose

How to generate workbooks, docs, and code for this repo when you cannot read the repo directly. Outputs must be
lint-safe, path-accurate, and ready to commit.

## MVP First Alignment

- Scan 2-3 similar artifacts before drafting to match expected depth and length.
- Default to the smallest useful version; expand only when a gap is proven.
- If a draft exceeds target length (guide > 250 lines, template > 120 lines), pause and trim.
- If unsure about target depth, use a short inline question comment:
  `<!-- @Question[Author][open]: Is this depth acceptable? -->` (remove before linting).

## Output format (for chat delivery)

- One fenced block per file with a language hint (e.g., ```markdown```, ```yaml```, ```python```).
- First line inside each fence: HTML comment with intended repo path (e.g., `<!-- File:
  90_Sandbox/ai_workbooks/wb_example.md -->`).
- Keep commentary outside fences; fences contain only file content.

## Workflow Pattern: Sandbox Workbooks

Use a sandbox workbook to package instructions and draft artifacts before applying changes to canonical paths.

**Roles:**

- **Authoring agent**: drafts plans, specs, and file contents.
- **Executor agent**: applies changes in the local repo.

**Pattern:**

1. Create a workbundle folder under `90_Sandbox/ai_workbooks/`.
2. Add an instruction file that maps each draft file to its target path and apply mode.
3. Apply changes from the sandbox workbundle into final repo paths.
4. Validate touched files before commit/push.

**Instruction file checklist:**

- Source file name
- Target repo path
- Apply mode (`create_new`, `replace_entire_file`, `merge_section`)
- Notes or anchors for merges

## File-type quick rules

- Markdown (see `guide_markdown_authoring.md`)
- Front matter first, then a single visible H1. Blank lines around headings, lists, and blockquotes.
- Use ASCII dashes; avoid control characters and non-ASCII separators.
- Add a language to fenced code blocks.
- Workbooks (see `guide_workbooks.md`)
- Structure: Overview/Scope, Inputs, Tasks/Steps, Outputs, Do-not-execute/Future.
- Name as `wb_<topic>_<phase>.md` under `90_Sandbox/ai_workbooks/`.
- Keep workbooks lint-safe; no file-wide markdownlint disables for new content.
- YAML/JSON (see `guide_yaml_authoring.md`, `guide_json_authoring.md`)
- 2-space indents, no tabs; keep keys ordered logically; avoid trailing spaces.
- JSON: double quotes, no trailing commas.
- YAML: avoid tabs and anchors unless necessary; prefer plain scalars where possible.
- Python (see `guide_python_authoring.md`)
- Follow repo Python conventions; keep imports sorted/grouped; add docstrings where needed.
- Use type hints when practical; prefer readable, small functions.
- PyQGIS (see `../<work_repo>/02_Modules/gis_workflow/docs/guides/guide_pyqgis_authoring.md`)
- Align with QGIS scripting patterns and the project's version expectations.
- SQL (see `guide_sql_authoring.md`)
- Use uppercase for keywords; format for readability; avoid vendor-specific syntax unless required.

## Lint and safety expectations

- Markdown: conforms to `.markdownlint.json` (single H1, blank lines, language on fences). Avoid file-wide disables for
  new files.
- YAML/JSON: must parse; avoid trailing spaces; keep indentation consistent.
- ASCII preferred unless the file already uses other characters.
- If `customizations.review_preferences.thrift_pass` is enabled, trim redundancy and move misplaced content before
  linting.
- Commit/push steps and lint execution are defined in `00_Admin/policies/policy_git_workflow_conventions.md`.
- Provide exact repo paths and filenames for deliverables.

## Self-resolve first (pause only when necessary)

- Fix missing/broken references by live-searching the repo and updating paths.
- Fix YAML/front matter and markdownlint issues rather than disabling rules.
- Align terminology to `guide_ai_ops_vocabulary.md` (Workbook, Runbook, Contract, Module).
- Pause only if no valid target exists or a write is required outside authorized scope.

## Naming and paths

- Use `lower_snake_case` for files/folders unless a template dictates otherwise.
- Reference paths relative to repo root (e.g., `../<work_repo>/01_Resources/data_sources/catalog/rest_sources.yaml`).

## Writing Rules

- Prefer concrete nouns over metaphors.
- Avoid anthropomorphic phrasing for agents.
- Use "NOT this" entries to prevent synonym drift.
- Avoid ambiguous terms that imply human-only actions unless a human is explicitly required. See VS017 in
  `00_Admin/configs/validator/validator_config.yaml`.

## Changelog/cross-links (when applicable)

- If you change catalogs (e.g., GIS YAMLs), update
  `../<work_repo>/01_Resources/data_sources/catalog/CHANGELOG.md` with a dated entry (newest first).
- Cross-link related workbooks/guides when adding new workbooks.
