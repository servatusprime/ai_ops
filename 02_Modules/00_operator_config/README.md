---
title: Module: 00_operator_config
version: 0.1.1
status: active
last_updated: 2026-02-26
owner: ai_ops
---

# Module: 00_operator_config

Operator-level customization contracts for ai_ops.

## Purpose

- Provide baseline templates for repo-local override behavior.
- Support `/customize` interview and config-generation lanes.
- Keep committed defaults separate from machine-local runtime state.

## Key Surfaces

- `templates/aiops_config.template.yaml`
- `templates/aiops_config.user.yaml`
- `docs/spec_customization_*.md`
- `operations/op_sync_external_context.py`

## Decommission Note

The legacy customization module has been retired. Use:

- `02_Modules/00_operator_config/` for operator config templates/specs.
- `02_Modules/01_agent_profiles/` for profile/base/schema/generated assets.
