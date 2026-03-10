---
title: Environment and Mode Selection Guide
version: 0.2.0
status: active
license: Apache-2.0
last_updated: 2026-02-28
owner: ai_ops
applies_to:
  - ai_ops
  - Governed target repositories
tags:
  - environment-selection
  - mode-selection
  - direct-mode
  - governed-mode
  - standalone-mode
---

# Environment and Mode Selection Guide

## Purpose

Define how agents and operators choose the correct execution environment and operating mode for ai_ops-governed work.

This guide is environment-selection only. Setup mechanics belong to:

- `00_Admin/guides/tooling/guide_environment_setup.md`

## Core Distinctions

Use these distinctions before choosing any lane:

- `analysis`: read and reason; no writes.
- `editing`: file changes in repo scope.
- `execution`: run commands/scripts/tests.
- `governance`: authority gates, workflow lanes, validation, closeout.

## Mode Selection (Normative)

Mode is determined by target repo relationship to `AGENTS.md`:

1. `Direct` mode: target repo is ai_ops itself.
2. `Governed` mode: target repo is external and governed by an ai_ops stack.
3. `Standalone` mode: no ai_ops stack is reachable.

Canonical behavior contract:

- `AGENTS.md` (workspace topology and bootstrap sequence)
- `00_Admin/guides/ai_operations/guide_workflows.md`
- `.ai_ops/workflows/work.md`

## Environment Selection Matrix

| Work Type | Preferred Environment | Why |
| --- | --- | --- |
| Governance and workflow execution | Agent lane (`/work`, `/crosscheck`, `/closeout`) | Applies authority, tracking, and QA gates consistently |
| Repo edits and artifact generation | IDE/CLI agent runtime (Codex or Claude) | Full repo context and deterministic file operations |
| Validation and linting | Local shell from agent runtime | Reproducible command evidence |
| Heavy data processing or domain runtimes | External runtime (for example Conda/QGIS/toolchain-specific env) | Correct dependencies and scale outside chat sandbox |
| Read-only audits | `/crosscheck` or `/health` | Structured evidence and verdict output |

## Tool Surface Selection

Use the simplest surface that can complete the task with evidence:

1. Prefer primary workflow lane (`/work`) for governed edits.
2. Use `/crosscheck` for independent QA/QC pass before closeout.
3. Use `/customize` for user-declared model capabilities and preferences.
4. Use `/profiles` for rider/crew behavior and subagent mapping regeneration.
5. Use `/ai_ops_setup` for wrapper/adapter installation and setup receipt updates.

## Model and Reasoning Selection

Model availability is not reliably auto-detectable across providers/plans.
Treat model capability as user-declared configuration.

- Declare available/default models in `.ai_ops/local/config.yaml` via `/customize`.
- Use `model_profile` in workbook/runbook front matter to communicate preferred model:reasoning options.
- Apply "simplest sufficient model" as guidance, then verify outcomes with selfcheck + `/crosscheck`.

## Quick Decision Flow

1. Identify target repo.
2. Determine mode (`Direct`, `Governed`, `Standalone`).
3. Classify task (`analysis`, `editing`, `execution`, `governance`).
4. Pick lane (`/work`, `/crosscheck`, `/customize`, `/profiles`, `/ai_ops_setup`).
5. Confirm authority level before writes.
6. Execute and record evidence.
7. Require non-blocking `/crosscheck` before `/closeout` for governed workbook work.

## Anti-Patterns

Do not:

- choose tools by preference before selecting mode and authority;
- treat chat-only context as execution state;
- skip `/crosscheck` for governed workbook closeout;
- assume model availability without user declaration;
- apply setup/install actions without `/ai_ops_setup` modality confirmation.

## References

- `AGENTS.md`
- `.ai_ops/workflows/work.md`
- `.ai_ops/workflows/crosscheck.md`
- `.ai_ops/workflows/ai_ops_setup.md`
- `.ai_ops/workflows/customize.md`
- `.ai_ops/workflows/profiles.md`
- `00_Admin/guides/ai_operations/guide_workflows.md`
