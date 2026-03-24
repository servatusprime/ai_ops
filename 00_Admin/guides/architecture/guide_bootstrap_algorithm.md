---
title: Guide: Bootstrap Algorithm
version: 0.2.1
status: active
license: Apache-2.0
last_updated: 2026-03-24
owner: ai_ops
related:
  - ../ai_operations/guide_workflows.md
  - ../ai_operations/guide_ai_ops_vocabulary.md
  - ../ai_operations/guide_bootstrap_self_repair.md
  - ../../runbooks/rb_bootstrap.md
---

# Guide: Bootstrap Algorithm

## Purpose

Define a consistent, agent-first bootstrap flow for reading `AGENTS.md`, resolving context, and handling fallbacks.
This guide is normative for agent bootstrapping. `AGENTS.md` is the sole bootstrap entry point; no additional
manifest file is required.

## Decision Tree (Canonical)

```text
START
  |
  |-- Read AGENTS.md
      |-- Present -> Parse workspace topology block -> Read CONTRIBUTING.md -> END
      |
      |-- Missing -> Halt with error: "AGENTS.md not found; cannot bootstrap"
```

## Required Information Checklist

Agents MUST obtain:

- Repo structure and placement rules
- Active work context (from `.ai_ops/local/work_state.yaml`; absence = no active work)
- Customization overrides (if any; from `.ai_ops/local/config.yaml`)
- External resource locations (if any)
- Session state (if resuming)

## Staged Bootstrap (Recommended)

To minimize initial context load, agents SHOULD bootstrap in stages:

1. Authority and rules (`AGENTS.md`, `CONTRIBUTING.md`)
2. Structure map (read `<git_root>/repo_structure.txt` only if the task needs full navigation)
3. Task context (program/workbundle docs and module guides as needed)

## Context Pairing Rule

`work_context` lives in `.ai_ops/local/work_state.yaml` (machine-local, gitignored).
When `work_context` contains multiple artifacts, each checkpoint MUST declare
its `artifact_path` (and optional `artifact_type` and `repo`) to bind it to
the correct work item.

- `checkpoints[].artifact_path` binds the checkpoint to the tracked artifact.
- `checkpoints[].artifact_type` SHOULD match
  `work_context.active_artifacts[].type` when present.
- `checkpoints[].repo` is optional and useful for governed external repo runs.
- Timestamps in checkpoints MUST use ISO 8601 `date-time` format.

## Fallback Protocol

1. Primary: `AGENTS.md` (required; halt if missing)
2. If `AGENTS.md` present but workspace topology block absent: apply defaults from `AGENTS.md` workspace topology section
3. Local config (`.ai_ops/local/config.yaml`): optional; absence is not an error

## Conflict Resolution Rules

- `AGENTS.md` vs local config: local config wins for machine-specific fields (surface, work_repos);
  `AGENTS.md` wins for structural/governance fields
- Session vs local config: session wins (current over default)
- Multiple sessions: newest timestamp wins (recency over history)

## External Resource Resolution

Resolution order:

1. `local_path` exists -> use local
2. `required: true` and `clone_if_missing: true` -> clone from `fallback_url` (only with explicit requestor approval)
3. `required: true` and `clone_if_missing: false` -> halt with error
4. `required: false` -> warn and continue

All resolved paths MUST be repo-relative or absolute and MUST NOT escape repo boundaries. Cache resolution results in
`.aiops_session` for the session duration.

**Clone Approval Protocol (Explicit):**

- Prompt: "Clone external repo `<name>` from `<fallback_url>`? [Y/n]"
- Proceed only on explicit confirmation.

## Version Compatibility Check

Agents MUST verify compatibility before proceeding:

1. Compare this guide's current version (`0.2.0`) against the version recorded in `AGENTS.md` front matter.
2. If this guide is outdated relative to AGENTS.md expectations, the agent MUST warn the user that its internal
   bootstrap logic may be outdated, but SHOULD attempt to proceed.

## Session Recovery Protocol

If `.aiops_session` exists but is unparseable or corrupted:

1. Archive the corrupted file as `.aiops_session.corrupted.{timestamp}`.
2. Create a fresh session with a new `session_id`.
3. Log a blocker in the new session: "Previous session corrupted and archived."
4. Continue bootstrap from `AGENTS.md`.

## Session Coordination (Baseline)

- Last-write-wins with timestamp comparison
- Lock TTL: 30 minutes of inactivity
- Roles:
  - Reader: read-only
  - Writer: read/write
  - Coordinator: can invalidate sessions and resolve conflicts
- If timestamps differ by <5 minutes: warn and request merge
- If timestamps differ by >5 minutes: newer session wins, archive older

## Context Compression

When `.aiops_session` exceeds 7KB:

1. Remove oldest checkpoints (keep last 3)
2. Summarize completed workbundles (preserve outcome only)
3. Compress blockers list (keep unresolved only)

If still >10KB, archive as `.aiops_session.001` and start fresh.

**Compacted Context Structure:** While `compacted_context` allows flexible structure, agents SHOULD prefer a key-value
summary of:

- `strategic_goal`: One sentence goal.
- `current_focus`: What is being worked on now.
- `key_decisions`: List of architectural decisions that constrain future work.

## Schema Evolution

- `manifest_version`: schema structure (breaking changes increment major)
- `data_version`: content changes (non-breaking increment minor)
- Agents should warn on unsupported versions and ignore unknown fields.
