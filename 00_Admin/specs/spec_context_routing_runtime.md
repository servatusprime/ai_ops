---
title: Spec - Context Routing Runtime Design
id: spec_context_routing_runtime
module: ai_ops
status: active
version: 0.1.0
created: 2026-03-14
owner: ai_ops
ai_generated: true
description: >
  Target-state runtime design for context_routing.yaml. Captures session-state-dependent
  onboarding tiers, hook points, fast-path conditions, and trigger detection contracts
  that current stateless LLM agents cannot evaluate. Apply fallback policy until a
  stateful runtime context manager is available.
related:
  - 00_Admin/configs/context_routing.yaml
  - AGENTS.md
  - .ai_ops/workflows/work.md
  - 00_Admin/runbooks/rb_bootstrap.md
---

<!-- markdownlint-disable MD013 -->
<!-- markdownlint-disable-next-line MD025 -->
# Spec - Context Routing Runtime Design

## Purpose

This spec holds the target-state runtime design for the ai_ops context routing system.
These specifications require session-state tracking that current stateless LLM chat
agents cannot evaluate.

**Current fallback policy (apply now):**

> Unknown state policy: apply `fresh_bootstrap` tier (read `AGENTS.md`) and proceed.
> Do not block on unverifiable session state.

The active routing contract lives in `00_Admin/configs/context_routing.yaml`.
This spec describes what that contract WILL become when a stateful runtime is available.

---

## Onboarding Tiers (Session-State Design)

These tiers extend the three bootstrap paths defined in `context_routing.yaml`.
`fresh_bootstrap` and `recenter` are currently active. The `resume_same_scope`
fast-path requires session-state evaluation that stateless agents cannot perform.

```yaml
onboarding_tiers:
  resolution_order:
  - fresh_bootstrap
  - resume_same_scope
  - recenter
  fresh_bootstrap:
    description: Unknown state or missing bootstrap requirements.
    bootstrap_path: fresh_bootstrap
    required_reads:
    - ai_ops/AGENTS.md
  resume_same_scope:
    description: Same target repo and stable state; reuse prior reads.
    bootstrap_path: resume_same_scope
    required_reads:
    - ai_ops/AGENTS.md
    required_session_contract:
    - same_target_repo
    - no_recenter_trigger
    - bootstrap_reads_still_valid
    fast_path_allows:
    - skip_heavy_role_profile_topology_gate
  recenter:
    description: Explicit recenter trigger requires bootstrap refresh.
    bootstrap_path: recenter
    required_reads:
    - ai_ops/AGENTS.md
```

---

## Bootstrap Fast-Path Conditions

The `resume_same_scope` fast path requires evaluating these conditions. Stateless
agents MUST apply `fallback_on_unknown_state: fresh_bootstrap` when session state
is unavailable.

```yaml
resume_same_scope_fast_path:
  enabled: true
  conditions:
  - same_target_repo
  - mode_unchanged
  - no_reread_trigger_fired
  fallback_on_unknown_state: fresh_bootstrap
```

---

## Trigger Detection Contract

These expressions define how runtime agents SHOULD detect reread triggers when
session-state tracking is available. Stateless agents: apply fallback.

```yaml
trigger_detection_contract:
  explicit_rebootstrap: session_flags.explicit_rebootstrap == true
  mode_or_target_repo_change: session_state.mode_or_target_repo_changed == true
  agents_md_updated: file_state_hash_changed(ai_ops/AGENTS.md) == true
```

---

## Bootstrap Missing Condition (Formal Definition)

When session-state tracking is available, evaluate these conditions to determine
whether a fresh bootstrap is required. Until then, apply `unknown_state_policy`.

```yaml
bootstrap_missing_condition:
  definition:
  - required_bootstrap_read_not_in_session_state
  - session_state_unavailable_or_unverifiable
  - reread_trigger_fired
  required_session_state_fields:
  - loaded_reads
  - active_target_repo
  - mode
  evaluation_order:
  - check_reread_triggers
  - check_required_reads_presence
  - if_state_unknown_treat_as_missing
  unknown_state_policy: treat_as_missing
```

---

## Hook Points

Named hook points for future integration with external tooling. No current ai_ops
tool or workflow fires these hooks; they are preserved for runtime design continuity.

```yaml
hook_points:
  work:
  - intake_after_bootstrap
  - mode_selected
  - governed_first_entry
  - recenter_on_drift
  bootstrap:
  - post_manifest_read
  health:
  - scope_confirmed
  crosscheck:
  - targets_confirmed
  lint:
  - scope_confirmed
  profiles:
  - profile_source_resolved
  ai_ops_setup:
  - modality_confirmed
```

---

## Implementation Roadmap

When a stateful runtime context manager is available:

1. Implement `session_flags` / `session_state` evaluation for `trigger_detection_contract`.
2. Implement `required_session_state_fields` tracking for `bootstrap_missing_condition`.
3. Activate `resume_same_scope_fast_path.conditions` evaluation.
4. Wire `hook_points` to an event bus or tool integration layer.
5. Migrate activated specs back into `context_routing.yaml` as enforced active config.
