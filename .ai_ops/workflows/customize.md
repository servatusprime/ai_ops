---
description: Configure agent preferences and customization options.
name: customize
kind: workflow
version: 0.1.1
status: active
owner: ai_ops
license: Apache-2.0
claude:
  argument-hint: null
  disable-model-invocation: false
  user-invocable: true
  allowed-tools: null
  model: null
  context: null
  agent: null
codex:
  metadata:
    short-description: Configure agent preferences and customization options.
  interface:
    display_name: customize
    short_description: Configure agent preferences and customization options.
  policy:
    allow_implicit_invocation: true
exports:
  claude_plugin:
    enabled: true
    skill_name: customize
  codex:
    enabled: true
    skill_name: customize
  claude_project:
    enabled: true
    skill_name: customize
---

# /customize

## Purpose

Configure agent preferences and customization options.

## Inputs and Preconditions

- Confirm target repo and desired scope before writing.
- If inputs are insufficient or the request is illogical, pause and ask for clarification.

## Setup-State Guard (Mandatory)

Before writing customization overrides:

1. Read `required_version` from `00_Admin/configs/setup_contract.yaml`.
2. Read setup receipt from receipt path in `00_Admin/configs/setup_contract.yaml`
   (default: `.ai_ops/local/setup/state.yaml`) when present.
3. If required setup is missing and defaults are insufficient, stop and route
   to `/ai_ops_setup` with path-specific remediation.
4. If defaults are sufficient, proceed and note optional setup hardening.
5. If model capabilities are undeclared, recommend declaration in this lane
   before profile tuning.

## Context Routing Hook

Use `00_Admin/configs/context_routing.yaml` as the canonical onboarding
contract.

1. Apply `commands._defaults.guard_profile` and
   `commands.customize.guard_profile`.
2. Resolve onboarding tier in order: `fresh_bootstrap`,
   `resume_same_scope`, `recenter` (fallback `fresh_bootstrap` when state is
   unknown).
3. Load `always_read`; expand `read_on_demand` only when needed.
4. Emit route metadata: `bootstrap_path`, `resume_basis`, and `reads_applied`.
5. If requested action requires canonical remediation edits, transition to
   `/work`.

## Decision Matrix (Cold-Start)

### Decision Matrix - Inside (Maintainer)

- Config target clear: proceed with customization.
- Config target unclear: ask for target path and desired settings.
  - **Default**: If unclear, default to `.ai_ops/local/config.yaml`.

### Decision Matrix - External (User)

- Target repo and config path clear: proceed.
- Target unclear or multiple repos: ask which repo and config path to use.

## Steps

### Inside Repo (Maintainer)

1. Apply bootstrap guard BRG-01: if bootstrap requirements are missing or
   unverifiable, apply `fresh_bootstrap` tier (read `AGENTS.md`) before lane
   steps.
2. Run Setup-State Guard before customization writes.
3. Run the customization interview and load defaults from
   `02_Modules/00_operator_config/templates/aiops_config.template.yaml`.
4. Focus areas: bootstrap preferences, profile layering, external resources, session limits.
   - model capabilities (user-declared available models, default model/reasoning level,
     and operator model-to-level binding via `model_level_map`)
   - validation policy for governed external repos (ai_ops vs repo-native)
5. Preview changes and confirm before writing overrides to `.ai_ops/local/config.yaml`.
6. If user adds free-form notes, record them in `customizations.notes.free_form` only.
7. Offer dry-run and rollback guidance.

### External Repo (User)

1. Apply bootstrap guard BRG-01 before lane steps.
2. Same settings available as inside mode (bootstrap, profile layering, external resources, session limits).
3. Store settings in user's repo config file (`.ai_ops/local/config.yaml` or user-specified location).
4. Adapt to user's repo structure (no ai_ops paths).
5. Preview changes and confirm before writing.
6. If user adds free-form notes, record them in `customizations.notes.free_form` only.

## Outputs

- Updated `.ai_ops/local/config.yaml` (or user-specified path).
- Summary of applied preferences.
- Model capability declaration summary when provided.

## Resources

- `02_Modules/00_operator_config/templates/aiops_config.template.yaml`
- `02_Modules/00_operator_config/docs/spec_customization_interview.md`
- `02_Modules/00_operator_config/docs/spec_customization_schemas.md`
- `02_Modules/00_operator_config/docs/spec_customization_ux.md`

## Lane

Default lane: Coordinator → Executor.

## Risks and Limits

- Customizations are per-repo; confirm the target before writing.
- Do not write to committed config files; all machine settings go to `.ai_ops/local/config.yaml`.
- Do not change settings outside the override path.
- Do not skip confirmation for destructive changes.
- Do not assume command folders exist; if missing, read `.ai_ops/workflows/customize.md` manually.
