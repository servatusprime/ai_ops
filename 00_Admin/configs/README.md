---
title: configs_readme
version: 0.3.0
status: active
license: Apache-2.0
owner: ai_ops
created: 2026-02-25
updated: 2026-02-28
---

# Configs

Settings and configuration files for repo tooling and validation.

## Purpose

Provide canonical config templates and policy docs that are safe to keep in repo.

## Subfolders

- `env/`: environment variable docs and example env files.
- `secrets/`: placeholder location for local secret material that must not be committed.

## Triggers

- `env/`: use during machine bootstrap, onboarding, or when repo-level variables
  are added/changed.
- `secrets/`: use only when a workflow explicitly needs file-based local secrets
  and an OS secret store is not viable.

In open-source mode, keep only placeholders/docs in `secrets/` (`README.md`,
`.gitkeep`) and never real secret values.

## Rules

- Keep machine-specific values out of version control.
- Track examples and docs only (for example `*.example.env`).
- Local runtime values should be created per user machine and ignored by git.

## Setup Contract Linkage

- Baseline setup contract version is defined in `00_Admin/configs/setup_contract.yaml`.
- Local setup receipt is machine-local:
  `.ai_ops/local/setup/state.yaml`.
- Repo-local operator overrides are machine-local:
  `.ai_ops/local/config.yaml`.
- Compatibility reads may still check legacy paths during migration:
  `.ai_ops/config.yaml` and `.ai_ops/profiles/active_crew.yaml`.
