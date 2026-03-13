# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project adheres to
Semantic Versioning.

## [Unreleased]

## [0.2.0] - 2026-03-12

### Added

- `.github/dependabot.yml`: weekly Dependabot version updates for GitHub
  Actions, automating SHA pin refresh when action authors release new versions.
- `00_Admin/backlog/future_work_registry.yaml`: entry `fw_20260312_01` tracking
  recurring GitHub Actions SHA pin maintenance.
- Standalone private repository on GitHub (`servatusprime/ai_ops`), split
  from monorepo with fresh git history.
- Per-repo `.pre-commit-config.yaml` with repo-relative tool paths.
- Per-repo `repo_structure.txt` generation via pre-commit hook.
- Repo split preparation workbundle with three-workbook execution sequence
  (strategy, hygiene/staging, execution).
- `MD050` strong-style rule pinned to asterisk in `.markdownlint.json`.
- `.cache/`, `.ruff_cache/`, `.lint_repo_validator.log` added to `.gitignore`.

### Changed

- `lint.yml`: pinned all three actions (`actions/checkout`, `actions/setup-python`,
  `actions/setup-node`) to full commit SHAs for supply chain security; added
  top-level `permissions: contents: read` to scope workflow to minimum access.
- `README.md`: enriched with Agent Configuration, Supported Platforms, artifact
  model one-liner, quality axes, and design tests references; dangling sentence
  fixed; Quick References section removed; version aligned to release scheme.
- `HUMANS.md`: updated `last_updated` to 2026-03-12.
- `.gitignore` expanded: env/secrets exclusions, `.ai_ops/config.yaml`,
  `.aiops_session`, active crew profile.
- `plugin.json` homepage and repository URLs updated to `servatusprime/ai_ops`.
- `tools/` directory consolidated to `00_Admin/scripts/` (12+ reference
  sites updated).
- Cross-repo reference policy enforced: ai_ops must not reference external
  repos by name, path, or example (VS028).
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
