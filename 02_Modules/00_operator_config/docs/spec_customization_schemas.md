---
spec_id: customization_schemas
title: Spec: Customization Schemas
status: stub
license: Apache-2.0
version: 0.1.0
owner: ai_ops
related: []
last_updated: 2026-01-24
---

# Spec: Customization Schemas

## Purpose

Define the schema artifacts used to model rider settings, crews, and presets for ai_ops customization.

## Files

- `02_Modules/01_agent_profiles/schemas/schema_rider_settings.yaml` — rider archetype field definitions
- `02_Modules/01_agent_profiles/schemas/profile_source_schema.yaml` — active_crew.yaml structure
- `02_Modules/01_agent_profiles/schemas/model_tuning_manifest_schema.yaml` — model-family calibration manifest
- `02_Modules/00_operator_config/templates/aiops_config.template.yaml` — machine-local config template

Note: `rider_archetypes.yaml`, `crews.yaml`, and `preset_vibe_coder.yaml` were deprecated and moved to
`99_Trash/profiles_deprecated_2026-03-22/` (EA-11, 2026-03-22). The active profile source format is
`active_crew.yaml` managed by `/profiles`.

## Schema Rules

- Schemas are versioned (`version` uses semver).
- Status values follow repo policy: `stub`, `active`, `deprecated`.
- No machine-local paths in schema artifacts.

## Validation Expectations

- Rider settings must include `id`, `name`, `version`, `status`, and `safety`.
- Profile source (`active_crew.yaml`) maps subagent slots to rider IDs + overrides.
- Operator config (`aiops_config.template.yaml`) must not include machine-local paths.

## Overrides

Workspace-specific values belong in `.ai_ops/local/config.yaml` and are not committed.
