---
name: profiles
description: Manage rider/crew profile source data and regenerate deterministic derivative behavior files.
kind: workflow
version: 0.1.1
status: active
owner: ai_ops
license: Apache-2.0
claude:
  argument-hint: '[mode]'
  disable-model-invocation: true
  user-invocable: true
  allowed-tools: Read Grep Glob LS Write Edit Bash
  model: null
  context: null
  agent: null
codex:
  metadata:
    short-description: Manage crew profiles and regenerate behavior artifacts.
  interface:
    display_name: profiles
    short_description: Edit rider/crew profile source and regenerate outputs.
  policy:
    allow_implicit_invocation: false
exports:
  claude_plugin:
    enabled: true
    skill_name: profiles
  codex:
    enabled: true
    skill_name: profiles
  claude_project:
    enabled: true
    skill_name: profiles
---

<!-- markdownlint-disable MD013 -->

# /profiles

## Purpose

Manage profile source data for rider/crew behavior and regenerate deterministic derivative files used by governed
agents, including adapter-managed primary-agent context artifacts.

## Inputs and Preconditions

- Optional mode: `view`, `preset`, `slot`, `slider`, `reset`, `regenerate`.
- Optional model-family target for calibration context: `neutral`, `claude`, `gpt5`, `gemini` (from model tuning
  manifest).
- Profile source path defaults:
  - per-repo: `.ai_ops/local/profiles/active_crew.yaml`
  - factory default: `02_Modules/01_agent_profiles/base/default_crew.yaml`
- Model tuning manifest default:
  - `02_Modules/01_agent_profiles/base/model_tuning_manifest.yaml`
- If inputs are insufficient or the request is illogical, pause and ask for clarification.
- If model capabilities are not declared in `.ai_ops/local/config.yaml`, recommend running `/customize` before
  model-family calibration actions.

## Setup-State Guard (Mandatory)

Before profile writes/regeneration:

1. Read `required_version` from `00_Admin/configs/setup_contract.yaml`.
2. Read setup receipt from receipt path in `00_Admin/configs/setup_contract.yaml`
   (default: `.ai_ops/local/setup/state.yaml`) when present.
3. If required setup is missing and defaults are insufficient, stop and route
   to `/ai_ops_setup` with path-specific remediation.
4. If defaults are sufficient, proceed and note optional setup hardening.

## Profile Storage Contract

- `/profiles` uses YAML as the canonical editable source (`active_crew.yaml`) for Claude, Codex, and Gemini profile
  behavior contracts.
- Gemini `.toml` files are command-wrapper adapters under `.gemini/commands/` and are not a `/profiles` value-edit
  backend.
- No TOML value mutation path exists in `/profiles` for Claude or Codex by design.

## Context Routing Hook

Use `00_Admin/configs/context_routing.yaml` as the canonical onboarding
contract.

1. Apply `commands._defaults.guard_profile` and `commands.profiles.guard_profile`.
2. Resolve onboarding tier in order: `fresh_bootstrap`,
   `resume_same_scope`, `recenter` (fallback `fresh_bootstrap` when state is
   unknown).
3. Load `always_read`; expand `read_on_demand` only when needed.
4. Emit route metadata: `bootstrap_path`, `resume_basis`, and `reads_applied`.
5. If requested action requires non-profile canonical remediation edits,
   transition to `/work`.

## Decision Matrix (Cold-Start)

### Decision Matrix - Inside (Maintainer)

- No per-repo profile exists: load factory default, show crew state, offer customization.
- Per-repo profile exists: load and show crew state.
- User requests change: enter profile edit flow (preset/slot/slider/reset).
- User confirms change: write profile source YAML, run regeneration script, report results.

### Decision Matrix - Governed (External Repo with ai_ops)

- Store profile source in target repo `.ai_ops/local/profiles/active_crew.yaml`.
- If target repo plugin directory exists, regenerate derivative agent files there.
- If plugin directory is missing, report preview-only and do not fabricate plugin structure silently.

### Decision Matrix - External (User)

- Confirm profile source file and desired edit mode.
- Apply deterministic changes only (no freeform profile prose edits).
- Report resulting diffs and regeneration outcome.

## Steps

### Inside Repo (Maintainer)

1. Apply bootstrap guard BRG-01: if bootstrap requirements are missing or
   unverifiable, apply `fresh_bootstrap` tier (read `AGENTS.md`) before lane
   steps.
2. Run Setup-State Guard before profile writes/regeneration.
3. Load active profile source YAML:
   - prefer `.ai_ops/local/profiles/active_crew.yaml` when present
   - compatibility read: `.ai_ops/profiles/active_crew.yaml`
   - otherwise use `02_Modules/01_agent_profiles/base/default_crew.yaml` (fallback compatibility:
     `02_Modules/00_customize/base/default_crew.yaml`)
4. Display current state:
   - crew preset
   - lead rider
   - subagent slot-to-rider mapping
   - active overrides
5. If user requests change, offer modes:
   - switch crew preset
   - change rider for a slot
   - adjust slider overrides for a slot
   - reset to factory default
6. For slider adjustments:
   - show current value and proposed value
   - validate safety floors (`conservatism` floor for write roles, `deference` floor global)
   - show preview diff before write
7. Confirm write intent before updating profile source YAML.
8. Write `.ai_ops/local/profiles/active_crew.yaml`.
9. Invoke regeneration script:
   - `python 00_Admin/scripts/regenerate_profiles.py`
   - optional model family: `python 00_Admin/scripts/regenerate_profiles.py --model-family <family>`
10. Report:

- files regenerated
- safety-floor clamps or warnings
- selected model-family calibration status
- any validation failures

1. If generated files fail lint, report findings and offer remediation via `/work`.

### External Repo (User)

1. Resolve profile source in target repo.
2. Apply requested profile edits with validation.
3. Run regeneration for target repo outputs when plugin paths exist.
4. Report results and diffs.

## Relationship to /customize

| Concern              | /customize                                         | /profiles                                                                |
| -------------------- | -------------------------------------------------- | ------------------------------------------------------------------------ |
| What it configures   | Session/bootstrap preferences and external context | Rider archetypes, slider overrides, crew behavior contracts              |
| Primary write target | `.ai_ops/local/config.yaml`                        | `.ai_ops/local/profiles/active_crew.yaml` and generated derivative files |
| Typical trigger      | Setup and preference tuning                        | Behavior contract changes                                                |

## Outputs

- Updated profile source YAML (when confirmed).
- Regenerated derivative files:
  - functional subagent files
  - single-agent profile map
  - primary-agent adapter context (`lead_agent_profile_context.md`)
  - model tuning summary (`model_tuning_summary.md`)
- Structured regeneration summary and warnings.

## Surface Adapter Notes

When `lead_agent_profile_context.md` is regenerated, load it as secondary
behavior context on supported surfaces:

- Codex: load as secondary context artifact (do not modify root `AGENTS.md`).
- Claude: load as secondary context artifact (do not modify root `CLAUDE.md`).
- Gemini: load as secondary context artifact (do not modify root `GEMINI.md`).

## Roles

Default role: Coordinator -> Executor (profile edits and script invocation).

## Risks and Limits

- `/profiles` manages profile source and deterministic derivatives only.
- Do not use this lane for unrelated governance edits.
- Rider sliders affect prose and `maxTurns`; they do not mutate structural role permissions.
- Primary-agent profile behavior is delivered through adapter-managed context
  files, not by modifying root `AGENTS.md`/`GEMINI.md`.
- Do not assume command folders exist; if missing, read `.ai_ops/workflows/profiles.md` manually.

## Working with Native Commands

Use native assistant commands for session-scoped mechanics (model selection, output formatting, local IDE helpers) when
available.

Use ai_ops workflow commands for governed execution contracts, authority gates, artifact handling, and
validation/reporting behavior.

If overlap exists, native commands handle session mechanics while this workflow remains the source of truth for governed
process behavior.

## Resources

- `02_Modules/01_agent_profiles/base/default_crew.yaml`
- `02_Modules/01_agent_profiles/base/model_tuning_manifest.yaml`
- `02_Modules/01_agent_profiles/schemas/profile_source_schema.yaml`
- `02_Modules/01_agent_profiles/schemas/model_tuning_manifest_schema.yaml`
- compatibility fallback: `02_Modules/00_customize/base/default_crew.yaml`
- `00_Admin/scripts/regenerate_profiles.py`
- `00_Admin/specs/spec_slider_manifest.md`
- `00_Admin/specs/spec_subagent_file.md`
