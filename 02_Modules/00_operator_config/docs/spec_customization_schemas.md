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

- `02_Modules/01_agent_profiles/schemas/schema_rider_settings.yaml`
- `02_Modules/01_agent_profiles/config/rider_archetypes.yaml`
- `02_Modules/01_agent_profiles/config/crews.yaml`
- `02_Modules/01_agent_profiles/profiles/preset_vibe_coder.yaml`

## Schema Rules

- Schemas are versioned (`version` uses semver).
- Status values follow repo policy: `stub`, `active`, `deprecated`.
- No machine-local paths in schema artifacts.

## Validation Expectations

- Rider settings must include `id`, `name`, `version`, `status`, and `safety`.
- Crews map roles to rider IDs defined in `rider_archetypes.yaml`.
- Presets point to a crew and may override rider settings.

## Overrides

Workspace-specific values belong in `.ai_ops/local/config.yaml` and are not committed.
