---
title: Runbook: Commit/Push Streamlining
version: 0.1.0
status: active
license: Apache-2.0
created: 2026-01-24
updated: 2026-01-26
owner: ai_ops
---

<!-- markdownlint-disable-next-line MD025 -->
# Runbook: Commit/Push Streamlining

## Purpose

Provide a repeatable, low-friction commit/push flow for approved work while preserving the requestor review gate.

## Preconditions

- Work scope is approved and in progress.
- Validation and lint steps are defined for the change set.
- Requestor review gate is required for Level 3+ work.

## External Repo Behavior

When running in an external repo (user mode):

- Use the target repo's own lint/validation steps if documented.
- If no repo-specific steps exist, run only safe defaults (markdownlint/yamllint when configs exist).
- Never assume ai_ops validator scripts are available in the external repo.
- Log the run in the target repo if it has a log location; otherwise report in chat only.

## Trigger / When to Use

- Use when the requestor wants to avoid repeated approval pauses for the same in-scope change set.
- Agent should suggest this runbook if approvals are already granted and the requestor prefers "approve once, run to
  completion" for commit/push.

## Authorization Marker (Turbo)

If the requestor provides this explicit marker, the agent may proceed through commit/push after validation without
pausing for further approval in the same scope:

`TURBO_AUTHORIZED: commit_push_after_validation`

The marker only applies to the current scope. Any scope expansion requires a new approval.

## Steps

1. Confirm scope and authority level.
2. Run the combined Self-Review Smoke Pass and fix issues found.
3. Run validation/lint commands.
4. Provide a change summary in the chat.
5. If the turbo marker is present, proceed to commit/push. Otherwise, pause for approval.
6. Log the run in `00_Admin/logs/log_workbook_run.md`.

## Postconditions

- Commit and push completed (or approval requested).
- Run log entry includes validation results and the approval marker used.

## Notes

- This runbook does not override policy; it defines an explicit marker to reduce repeated approvals.
- If validation fails, stop and fix before continuing.
