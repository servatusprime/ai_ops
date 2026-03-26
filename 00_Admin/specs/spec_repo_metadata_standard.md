---
title: Repo Metadata Standard
id: spec_repo_metadata_standard
module: admin
status: active
license: Apache-2.0
version: 0.1.4
created: 2025-12-02
updated: 2026-03-14
owner: ai_ops
ai_generated: true
---
<!-- markdownlint-disable-next-line MD025 MD041 -->
# Repo Metadata Standard

## Purpose

Defines required YAML front matter and key fields for guides, specs, workflows, AI workbooks, and catalog
entries to keep files AI-friendly, diff-friendly, and consistent across the repo.

## 1. Purpose

Defines required YAML front matter and key fields for guides, specs, workflows,
AI workbooks, and catalog entries to keep files AI-friendly, diff-friendly, and
consistent.

---

## 2. General YAML Rules

- Use YAML front matter delimited by `---` at the top of Markdown files.
- Use `kebab-case` for `id`, `snake_case` for filenames.
- Prefer ISO dates: `YYYY-MM-DD`.
- Avoid tabs; use spaces.

### 2.1 Owner Field Syntax

Use this canonical pattern:

- `owner: ai_ops` for owner fields.

Quoting and brackets are not required for simple scalar owner values.

---

## 3. Document Types and Required Fields

### 3.1 Guides (e.g., GIS discovery guide)

- Typical location: `02_Modules/<module>/guides/guide_*.md`
- Required fields: `title`, `version`, `status`, `last_updated`, `owner`
- Optional: `related`, `tags`, `module`, `ai_generated`, `promoted_from`

### 3.2 Specs (e.g., this file)

- Typical location: `00_Admin/specs/spec_*.md`
- Required fields: `title`, `id`, `module`, `status`, `version`, `created`, `owner`, `ai_generated`

### 3.3 AI Workbooks

- Location: `90_Sandbox/ai_workbooks/wb_*.md`
- Required fields: `title`, `id`, `status`, `version`, `created`, `ai_role`, `description`
- Optional: `replaces` (list of workbook IDs superseded), `role_assignments` (per-role
  model/tier overrides), `execution_mode` (e.g., `sequential`), `model_profile`
  (overall model tier or provider-specific name — see note below)

> **`model_profile` format:** Templates use generic tier descriptors only
> (e.g., `"high"`, `"reasoning:high | standard:medium"`). Active workbooks and
> runbooks may use provider-specific names (e.g., `"claude-sonnet-4.6:high"`).
> Validator rule VS029 warns when `model_profile` is absent from new
> `wb_*.md`/`rb_*.md` artifacts.

### 3.4 Runbooks

- Location: `00_Admin/runbooks/rb_*.md`
- Required fields: `title`, `id`, `status`, `version`, `created`, `owner`
- Optional: `model_profile` (reusable execution tier guidance), `execution_mode`,
  `role_assignments`

### 3.5 Workflow Contracts

- Location: `.ai_ops/workflows/*.md`
- Required fields: `name`, `description`, `kind`, `version`, `status`, `owner`,
  `license`, `claude`, `codex`, `exports`
- Validation lane:
  `00_Admin/scripts/validate_workflow_frontmatter.py`

---

## 4. Catalog YAML Entries

Example files: `../<work_repo>/01_Resources/data_sources/catalog/rest_sources.yaml`, `wms_sources.yaml`, `xyz_sources.yaml`

Each entry must have:

- `key` - lowercase snake_case, stable ID
- `name` - human-readable title
- `url` - full endpoint/template
- `category` - one of `local_gov`, `state`, `federal`, `imagery`, `environmental`, `utility`, `other`
- `notes` - 1-2 line description and caveats
- `source` - e.g., `gis_export_YYYY-MM-DD`, `user_added_YYYY-MM-DD`

Optional:

- `status` - `active` or `deprecated` (use `completed` for finished work; reserve `deprecated` for superseded)
- `tags` - list of keywords

---

## 5. Date and Time Rules

- `created`: date the file was first created (do not auto-update on edits).
- `last_updated`: date of the most recent edit (preferred key for guides).
- `source` (catalogs): date of the real-world artifact (e.g., GIS export).
- Track changes via `version`, changelogs, and Git history.

---

## 6. Status Values

Allowed statuses: `planned`, `stub`, `active`, `completed`, `deprecated`.

---

## 7. AI Attribution

`ai_generated: true` means the initial draft was AI-generated or heavily AI-assisted; requestor review remains expected.
Git history is the record of authorship.

---

## 8. License Field Policy

License field usage is scoped, not universal:

- **Required** for executable workflow contracts in `.ai_ops/workflows/*.md`
  (`license: Apache-2.0`).
- **Recommended** for new canonical runbooks/specs/templates that define reusable
  contracts.
- **Not required** for sandbox/history artifacts (for example
  `90_Sandbox/**`, review snapshots, transient notes).

Repository-wide legal licensing remains anchored by root `LICENSE`; frontmatter
license fields are contract metadata, not a substitute legal file.

---

## 9. Enforcement

`00_Admin/scripts/validate_repo_precommit.ps1` may warn or fail when required fields are missing on `wb_*.md`,
`guide_*.md`, or `spec_*.md`. This spec is the canonical reference for those checks.
