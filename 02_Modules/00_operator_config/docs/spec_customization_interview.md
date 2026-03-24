---
spec_id: customization_interview
title: Spec: Customization Interview
status: active
license: Apache-2.0
version: 0.2.0
owner: ai_ops
related: []
last_updated: 2026-03-23
---

# Spec: Customization Interview

## Purpose

Define the agent-led interview flow for generating or updating customization overrides.

## Minimal Question Set

### First-Time Bootstrap Verification (Required for new users)

Before customization questions, verify bootstrap understanding:

1. Have you reviewed the authority model (Levels 0-4)?
2. Do you understand the canonical vocabulary (workbook, workbundle, policy, spec, guide)?
3. Can you identify where to find policies, specs, and guides in the repository?

If any answer is "no" or uncertain, guide user to:

- `AGENTS.md` for bootstrap sequence
- `00_Admin/guides/ai_operations/guide_bootstrap_verification_checklist.md` for detailed verification
- `00_Admin/guides/ai_operations/guide_authority_decision_tree.md` for decision guidance

### Customization Questions

1. Which repo(s) should be writable for work?
2. Which repo(s) are read-only resources?
3. Do you want defaults or a custom preset?
4. Do you want advanced options (directory overrides, profile layering)?
5. Do you want a thrift-pass before validation? If yes, which mode (`local` or `meta`)?
6. Do you want /work to offer status, anchor, and pause options by default?
7. For governed external repos, should ai_ops validators/linters be used or should we use the target repo's tooling?
8. Are you trying to change session output style only (for example concise or verbose)? If yes, use the native style
   command for your surface (for example Claude `/output-style`) instead of persistent profile changes.
9. Would you like to declare a model-to-level binding? This maps concrete model IDs (e.g., `claude-opus-4-6`)
   to ai_ops reasoning levels (1–4) so workbook `model_profile` tier references resolve at runtime. Skip if using
   a single model or if the defaults are sufficient.

## Flow

1. **Bootstrap verification** (first-time users only):
   - Check if `.ai_ops/local/config.yaml` exists (if yes, skip bootstrap verification)
   - If new user, ask bootstrap verification questions
   - If gaps identified, provide guidance and pause interview
   - Record bootstrap verification completion in interview state
2. Load defaults from `aiops_config.template.yaml`.
3. Ask minimal questions and apply overrides.
4. Show a preview diff of `.ai_ops/local/config.yaml` changes.
5. Confirm before writing.
6. Offer dry-run and rollback guidance.

## Interview State (Structured)

Represent the interview state as a single object so the flow can resume or be audited.

```yaml
interview_state:
  version: 0.1.0
  status: in_progress
  step: 3
  bootstrap_verified: true # Set to true after bootstrap verification (first-time only)
  answers:
    work_repos: []
    resource_repos: []
    preset_id: null
    advanced_mode: false
    thrift_pass: false
    thrift_pass_mode: local
    validation_policy:
      governed_mode: ai_ops
    model_capabilities:
      model_level_map: {}   # populated if operator answers yes to Q9
    work_command_preferences:
      offer_status: true
      offer_anchor: true
      offer_pause: true
  overrides_path: .ai_ops/local/config.yaml
  pending_changeset_id: null
  last_updated: 2026-01-24T00:00:00Z
```

## Structured Diff Format

Changes are expressed as a simple patch list keyed by path and operation.

```yaml
changeset:
  id: cs_20260124_01
  target: .ai_ops/local/config.yaml
  operations:
    - op: set
      path: workspace.work_repos
      value:
        - id: <work_repo>
          path: ./<work_repo>
    - op: set
      path: workspace.directory_overrides.sandbox_dir_name
      value: null
```

## Output Format

- `overrides_path`: `.ai_ops/local/config.yaml`
- `changeset`: structured YAML diff
- `confirmation`: true/false

## Safeguards

- Never write to versioned committed config files (`AGENTS.md`, `00_Admin/configs/setup_contract.yaml`).
- Require confirmation for destructive changes.
- Log changes in the execution log when a workbook is active.
