---
title: Work Focus Recenter Spec
id: spec_work_focus_recenter
module: admin
status: active
license: Apache-2.0
version: 0.2.0
created: 2026-02-13
updated: 2026-02-28
owner: ai_ops
ai_generated: true
---

<!-- markdownlint-disable-next-line MD025 -->
# Work Focus Recenter Spec

## 1. Purpose

Define normative focus-tracking and recenter behavior for `/work` sessions.

## 2. Scope

Applies to `ai_ops/.ai_ops/workflows/work.md` focus-check and recenter behavior
across Direct and Governed modes.

## 3. Trigger Model

Recenter is not a session-start action. Session start establishes initial
focus; recenter applies only after drift signals.

### 3.1 Initial Focus (Not Recenter)

At session start/resume, `/work` MUST establish initial focus by confirming:

- active artifact,
- current phase/task,
- immediate next gate.

### 3.2 Recenter Triggers (Required)

During active execution, recenter MUST run only when one or more triggers fire:

1. Scope drift signal (new request would change scope).
2. Blocker/gate signal (task blocked or required gate unresolved).
3. Side-quest return signal (agent returns from explicitly logged tangent).
4. Completion-integrity signal (task/checklist mismatch before completion).

### 3.3 Conditional Pre-Action Hook

Pre-action recenter SHOULD run only for high-impact actions when drift risk is
non-trivial (for example multi-file edits, broad scans, or mode switch).
It MUST NOT run as blanket overhead before every action or at cold session
start.

### 3.4 Non-Triggers (Do Not Recenter)

Recenter MUST NOT trigger for:

1. Session start/resume while initial focus is being established.
2. Atomic low-risk actions with no scope-shift signal.
3. Pre-completion checks when task/checklist integrity is already aligned.

## 4. Recenter Output Contract

Recenter output MUST include:

- active artifact identifier,
- current phase/task,
- next required gate,
- pending validation commands.

## 5. Safety Constraints

- Focus/recenter behavior MUST NOT authorize out-of-scope edits.
- Recenter prompts MUST NOT bypass capability gates.
- Pre-completion recenter is an integrity gate used only when mismatch signals
  appear, not as mandatory re-read overhead.

## 6. Related References

- `ai_ops/.ai_ops/workflows/work.md`
- `ai_ops/AGENTS.md`
- `ai_ops/00_Admin/guides/ai_operations/guide_command_workflows.md`
