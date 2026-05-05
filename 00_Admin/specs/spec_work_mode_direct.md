---
title: Work Direct Mode Spec
id: spec_work_mode_direct
module: admin
status: active
license: Apache-2.0
version: 0.2.0
created: 2026-02-13
updated: 2026-05-05
owner: ai_ops
ai_generated: true
spec_archetype: governance_spec
---

<!-- markdownlint-disable-next-line MD025 -->
# Work Direct Mode Spec

## Purpose

Defines normative `/work` behavior when the target repo is `ai_ops` (Direct mode). Covers activation
conditions, pre-flight checks, and authority boundaries for direct-mode sessions.

## 1. Purpose

Define normative `/work` behavior when the target repo is `ai_ops` (Direct
mode).

## 2. Scope

Applies to `ai_ops/.ai_ops/workflows/work.md` command execution path for Direct
mode only.

## 3. Required Behavior

When `target_repo == ai_ops`, `/work` MUST:

1. Confirm Direct mode selection and state that target is `ai_ops`.
2. Resolve active artifacts from `.ai_ops/local/work_state.yaml` `work_context.active_artifacts`
   before asking to create new work artifacts.
3. If no active artifact exists, ask for explicit scope (existing artifact or
   new workbook/workbundle).
4. Enforce pre-write authority guard before any write.
5. Keep reads scoped to required references and applicable routing rules.
6. Record mode confirmation in execution notes or session output.
7. Apply command routing hook from `context_routing.yaml` when present.

## 4. Safety Constraints

- Direct mode MUST NOT bypass Level 4 stop-gates for governance files.
- Direct mode MUST NOT create new command-surface workflow files.

## 5. Verification Evidence

Direct-mode execution evidence SHOULD include:

- target confirmation line,
- active-artifact resolution result,
- authority gate disposition for touched files.

## 6. Related References

- `ai_ops/.ai_ops/workflows/work.md`
- `ai_ops/AGENTS.md`
- `ai_ops/00_Admin/guides/ai_operations/guide_command_workflows.md`

## Change Log

- 0.2.0 (2026-05-05): Metadata normalized to declare spec_archetype.
  Existing version history remains in Git history and prior frontmatter dates.
