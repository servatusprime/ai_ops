---
title: Module: 01_agent_profiles
version: 0.1.1
status: active
last_updated: 2026-03-04
owner: ai_ops
---

# Module: 01_agent_profiles

Canonical rider/crew profile contracts and generated profile artifacts.

## Purpose

This module is the implementation layer of the ai_ops Crew Model — see
`00_Admin/guides/architecture/guide_design_and_philosophy.md` §The Crew Model.

- Provide deterministic profile source contracts for `/profiles`.
- Store baseline rider/crew defaults and schemas.
- Store generated adapter context artifacts for deterministic behavior lanes.

## Key Surfaces

- `base/default_crew.yaml`
- `base/model_tuning_manifest.yaml`
- `config/crews.yaml`
- `config/rider_archetypes.yaml`
- `schemas/*.yaml`
- `generated/*.md`

## Canonical Lane Mapping

Subagent profile slots map to canonical ai_ops execution lanes as follows:

| Profile Slot | Canonical Lane |
| --- | --- |
| `ai-ops-planner` | `Planner` |
| `ai-ops-executor` | `Executor` |
| `ai-ops-builder` | `Builder` |
| `ai-ops-reviewer` | `Reviewer` |
| `ai-ops-researcher` | `Researcher` |
| `ai-ops-closer` | `Closer` |
| `ai-ops-linter` | `Linter` |

`ai-ops-closer` and `ai-ops-linter` are specialized presets bound to
`Closer` and `Linter` respectively.

## Local Runtime Boundary

Active user profile state is local and non-committed:
`.ai_ops/local/profiles/active_crew.yaml`.

Compatibility reads may still check legacy
`.ai_ops/profiles/active_crew.yaml`.
