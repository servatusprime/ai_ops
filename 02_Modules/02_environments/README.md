---
title: Module: 02_environments
version: 0.1.0
status: active
last_updated: 2026-02-28
owner: ai_ops
---

# Module: 02_environments

Environment setup contracts used by `/bootstrap` and `/ai_ops_setup`.

## Purpose

- Define setup readiness expectations and install surfaces.
- Keep setup contract evidence and install matrix references centralized.
- Separate environment/setup concerns from operator preferences and profiles.

## Key Surfaces

- `setup/install_matrix.yaml`
- setup-state contract references in `00_Admin/configs/setup_contract.yaml`
- local setup receipt: `.ai_ops/local/setup/state.yaml` (machine-local)
