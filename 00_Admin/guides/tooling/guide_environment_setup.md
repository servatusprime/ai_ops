---
title: guide_environment_setup
version: 2.0.3
status: active
license: Apache-2.0
last_updated: 2026-02-28
owner: ai_ops
related:
  - 00_Admin/guides/architecture/guide_repository_structure.md
note: >
  Domain-specific tooling (GIS, databases, platform stacks) belongs in the
  target work repo's own `00_Admin/guides/tooling/` folder.
---

<!-- markdownlint-disable MD025 -->

# Guide: Environment Setup & Integration Phases

For requestor and agent collaboration. This guide outlines practical phases to get your local
environment, version control, and tools configured in a clean, reproducible way.

---

## Phase 0 -- Planning & Alignment

Objective: Confirm scope, tools, and integration order.

- Identify all components: IDE, GitHub, `<workspace_root>`, PowerShell, Python.
- Decide: Local-first workflow (not Codespaces).
- Verify repo layout per `guide_repository_structure.md`.
- Define naming conventions and prefix rules (guide, spec, prompt, etc.).
- Prepare `<workspace_root>` folder structure:
  `<workspace_root>/<repo_name>/` (OS-specific path syntax as needed).

Deliverables: Project folder skeleton exists; GitHub repo private; `<workspace_root>` confirmed.

---

## Phase 1 -- Local System Preparation

Objective: Configure workstation foundation.

### Windows Developer Environment

- Enable Developer Mode.
- Install Windows Terminal and PowerShell 7.
- Enable long path support.

### Git & Authentication

- Install Git for Windows.
- Configure global name/email, `autocrlf = true`, default branch = `main`.
- Generate SSH key (ed25519) and register with GitHub.

### Folder Scaffolding

- Create repo root folders (`00_Admin` ... `99_Trash`).
- Confirm `.gitignore` and `.gitattributes` templates applied.

Deliverables: Verified Git connection (push/pull works), clean PowerShell environment.

---

## Phase 2 -- IDE Configuration

Objective: Establish the main work interface.

- Install IDE (VS Code recommended).
- Read `00_Admin/guides/guide_ide_extensions.md` before extension install/update.
- Use troubleshooting/formatting standards in `guide_ide_extensions.md` when
  editor behavior drifts from repo standards.
- Add essential extensions per `00_Admin/tooling/extensions.md`.
- Apply workspace settings (`.vscode/settings.json`).
- Test Markdown rendering and auto-format on save.
- Optional: create a `.code-workspace` for multi-folder repo view.

Deliverables: IDE connected to repo, formatting rules enforced, GitLens visible.

---

## Phase 3 -- Repo Sync & Version Control

Objective: Finalize private GitHub integration and sync model.

- Clone `<org>/<repo_name>` into `<workspace_root>` folder.
- Test branch creation, commit, and push to `main`.
- Implement Conventional Commit messages (`feat:`, `fix:`, etc.).
- Validate `.github/CODEOWNERS` and branch protection (main locked).
- Document run logs in `00_Admin/logs/`.

Deliverables: Git baseline verified, push/pull latency minimal, conflict-free sync.

---

## Setup State and Local Contract

Use a two-layer setup contract to avoid repeated setup runs:

- baseline contract version in `00_Admin/configs/setup_contract.yaml` (committed default contract),
- local setup receipt in `.ai_ops/local/setup/state.yaml` (machine-local).

Local user values stay outside committed defaults:

- `.ai_ops/local/config.yaml`
- `.ai_ops/local/profiles/active_crew.yaml`
- `.ai_ops/local/setup/state.yaml`
- `*.local.env` files (gitignored; use `01_Resources/templates/documents/env_vars_template.md`
  as the pattern for adding env var documentation to any repo)

Command guard behavior:

- `/work`, `/customize`, and `/profiles` check setup state before execution.
- if required setup is missing and defaults are insufficient, route to
  `/ai_ops_setup`.
- if defaults are sufficient, proceed and offer optional customization.

### First-Clone Deterministic Flow

For first-time users, follow this sequence exactly:

1. clone repo,
2. run `/bootstrap`,
3. run `/ai_ops_setup`,
4. create/confirm local state under `.ai_ops/local/**`,
5. run `/work` after readiness passes.

If any prerequisite is missing, commands should return path-specific
remediation rather than implicit defaults.

---

## Phase 4 -- Domain-Specific Tools

Objective: Deploy supporting software for your work repo.

This phase is domain-specific. See your work repo's environment setup guide:

- **GIS/geospatial work**: `<work_repo>/00_Admin/guides/tooling/guide_environment_setup_gis.md`
- **Other domains**: Check `<work_repo>/00_Admin/guides/tooling/` for applicable guides

Common patterns for domain tools:

- Keep external infrastructure (databases, services) outside the repo
- Store migrations, configs, and backups in repo; not live data
- Export environment definitions (`environment.yml`, `requirements.txt`) for reproducibility
- Use environment variables or `.env` files for local connection settings

---

## Next Steps

After completing these phases:

1. Run ai_ops setup for your AI tool (see `.ai_ops/setup/README.md`)
2. Say `/work` to initialize a work session
3. Follow domain-specific setup in your work repo if applicable
