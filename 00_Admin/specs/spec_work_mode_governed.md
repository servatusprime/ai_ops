---
title: Work Governed Mode Spec
id: spec_work_mode_governed
module: admin
status: active
license: Apache-2.0
version: 0.3.0
created: 2026-02-13
updated: 2026-03-09
owner: ai_ops
ai_generated: true
---

<!-- markdownlint-disable-next-line MD025 -->
# Work Governed Mode Spec

## 1. Purpose

Define normative `/work` behavior when ai_ops governs an external target repo.

## 2. Scope

Applies to `ai_ops/.ai_ops/workflows/work.md` command execution path for
Governed mode only.

## 3. Required Behavior

When `target_repo != ai_ops` and governed mode is active, `/work` MUST:

1. Resolve target repo from `AGENTS.md` workspace topology `work_repos`
   (or `.ai_ops/local/config.yaml` if present; or explicit user confirmation).
2. Resolve active artifacts scoped to that target repo before proposing new
   artifact creation.
3. Apply ai_ops governance by reference without duplicating governance prose
   into downstream repos unless explicitly warranted.
4. Enforce Level 4 stop-gate behavior for governed-path writes requiring
   approval.
5. Record governed target selection evidence and handoff state.
6. Apply command routing hook from `context_routing.yaml` when present.
7. Enforce cross-repo reference policy:
   - canonical `ai_ops` artifacts must use generic governed-repo placeholders
     instead of concrete external repo names/paths;
   - governed repos should reference ai_ops governance via repo-root-relative
     paths (for example `../ai_ops/...`).

## 4. Safety Constraints

- Governed mode MUST NOT mutate ai_ops governance files as part of downstream
  repo execution unless explicitly approved.
- Governed mode MUST NOT create new command-surface workflow files in lieu of
  updating canonical `/work`.
- Governed mode MUST NOT introduce machine-local absolute governance paths
  (for example `C:\...` or `/Users/...`) in committed artifacts.

## 5. Verification Evidence

Governed-mode execution evidence SHOULD include:

- target repo confirmation,
- active-artifact resolution result,
- authority-gate disposition for governed paths,
- cross-repo reference contract disposition.

## 6. Related References

- `ai_ops/.ai_ops/workflows/work.md`
- `ai_ops/AGENTS.md`
- `ai_ops/00_Admin/guides/ai_operations/guide_command_workflows.md`
