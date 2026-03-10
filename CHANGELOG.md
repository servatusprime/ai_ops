# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project adheres to
Semantic Versioning.

## [Unreleased]

### Added

- Repo split preparation workbundle with three-workbook execution sequence
  (strategy, hygiene/staging, execution).
- `MD050` strong-style rule pinned to asterisk in `.markdownlint.json`.
- `.cache/`, `.ruff_cache/`, `.lint_repo_validator.log` added to `.gitignore`.

### Changed

- Sandbox `ai_workbooks/README.md` updated: stale entries removed, template
  path corrected.
- `work_state.yaml` reconciled: stale entries for retired workbundles removed.

## [0.1.0] - 2026-02-27

### Summary

- Directory structure simplified to three tracked directories: `00_Admin`,
  `01_Resources`, `02_Modules`.
- Root documents: LICENSE (Apache 2.0), CHANGELOG.md, CONTRIBUTING.md,
  SECURITY.md, CODE_OF_CONDUCT.md, CODEOWNERS.
- GitHub Actions CI: `lint.yml` with canonical release-quality gate.
- GitHub issue templates (bug report, feature request) and PR template with
  authority-level classification.
- HUMANS.md with Core Concepts, Quick Start, Mermaid diagrams, and
  deployment-model framing.
- Plugin surface: 13 commands with skill wrappers, 6 agent definitions,
  export-drift checking, marketplace manifest, and `plugin.json`.
- State architecture: tracked config (`setup_contract.yaml`,
  `context_routing.yaml`) split from machine-local state
  (`work_state.yaml`).
- `work_savepoint` command (renamed from `work_pause`) with commit+push
  default and `--no-commit` flag.

### Removed

- `aiops.yaml` manifest retired; replaced by split config/state
  architecture.
- Legacy directories: `01_Agents/`, `04_Projects/`, `05_Backups/`.
- `backup_re_gis.ps1` and other non-governance scripts.
