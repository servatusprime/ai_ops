---
spec_id: customization_ux
title: Spec: Customization UX
status: stub
license: Apache-2.0
version: 0.1.0
owner: ai_ops
related: []
last_updated: 2026-01-24
---

# Spec: Customization UX

## Purpose

Define how customization is presented to users through `/customize` and related onboarding flows.

## Modes

- **Basic**: minimal prompts with safe defaults.
- **Advanced**: expanded options for experienced users.

## Advanced Options

- `directory_overrides` (sandbox/trash naming)
- Repo bindings for `work_repos` and `resource_repos`
- Profile layering overrides (`global_profile_path`, `repo_overrides_path`)
- Review preferences (`review_preferences.thrift_pass`, `review_preferences.thrift_pass_mode`)
- Work command preferences (`work_command_preferences.offer_status`, `offer_anchor`, `offer_pause`)

## UX Principles

- Preset-first; ask only high-signal questions.
- Preview + confirm before writing overrides.
- Dry-run option for showing changes without writing.
- Defaults are loaded from `aiops_config.template.yaml`.

## Native Style Command Complement

When users ask for session-level response formatting (for example concise vs verbose output), prefer the platform-native
style command where available (for example Claude `/output-style`).

ai_ops profile controls (`/profiles`) govern persistent behavioral contracts across roles. Native style commands govern
session surface formatting. If both are set, native style commands take precedence for presentation style.

## Outputs

- Overrides written to `.ai_ops/local/config.yaml`.
- Active preset recorded with `preset_id` and `crew_id`.
- Interview state tracked using the `InterviewState` structure defined in
  `02_Modules/00_operator_config/docs/spec_customization_interview.md`.
