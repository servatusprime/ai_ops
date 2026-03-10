---
title: Guide: aiops agent endpoint
version: 0.3.0
status: active
license: Apache-2.0
last_updated: 2026-02-28
owner: ai_ops
related:
  - ./guide_bootstrap_algorithm.md
  - ../ai_operations/guide_workflows.md
  - ../../runbooks/rb_bootstrap.md
---

# Guide: aiops agent endpoint

## Purpose

Define the runtime endpoint contract agents use to bootstrap and execute work in ai_ops-governed sessions.

This guide is endpoint-focused. It does not redefine manifest schema, command semantics, or workspace policy.

## Canonical Sources (No Duplication)

- Bootstrap entry point and workspace topology: `AGENTS.md`
- Bootstrap algorithm and fallbacks: `00_Admin/guides/architecture/guide_bootstrap_algorithm.md`
- Command semantics (`/work`, `/work_status`, `/work_savepoint`, etc.):
  `00_Admin/guides/ai_operations/guide_workflows.md` and `.ai_ops/workflows/*.md`

If guidance conflicts, treat those sources as canonical and update this guide by reference.

## Agent Endpoint Contract

Agents MUST consume structured runtime input (JSON/YAML) and produce structured results.

Wrappers (CLI or other UX layers) are optional and MUST map to the same endpoint contract.

### Minimal runtime payload

```json
{
  "action": "bootstrap | run_workbook | query",
  "target": "path/to/workbook-or-query",
  "agents_md_path": "path/to/AGENTS.md"
}
```

## Onboarding Paths

Supported current path:

1. Clone + `/work` (default)

Optional future wrappers:

- CLI wrappers
- Other UI wrappers

All wrappers, if used, MUST read/write the same governed config paths and invoke the same endpoint contract.

## Workspace Behavior (Endpoint-Level)

- Detect context using `AGENTS.md` and the workspace topology block it contains.
- Respect user overrides in `.ai_ops/local/config.yaml`.
- Do not write user-specific values into committed config files; use `.ai_ops/local/config.yaml`.
- Do not restructure workspaces without explicit approval.

## Output Expectations

- Structured output (JSON/YAML) is primary.
- Human-readable summaries are derived views of structured output.

## Audit Logging

Onboarding and endpoint-affecting setup actions SHOULD be logged in:

- `00_Admin/logs/log_setup_audit.md`

Record: date, agent, path used, workspace scope, files touched, and rollback notes if any.

## Change Control

When endpoint behavior changes:

1. Update this guide.
2. Confirm bootstrap alignment in `guide_bootstrap_algorithm.md`.
3. Confirm workflow alignment in `.ai_ops/workflows/*.md`.
4. Log schema/interface impact in `00_Admin/logs/log_schema_changes.md` if applicable.
