---
title: Guide: Execution Orchestration
version: 0.1.1
status: active
license: Apache-2.0
last_updated: 2026-03-04
owner: ai_ops
related:
- ../../specs/spec_execution_orchestration.md
---

# Guide: Execution Orchestration

## Purpose

Advisory guide for how execution state, triggers, and handoffs are managed across workbooks and sessions.
Defers to `spec_execution_orchestration.md` for normative requirements.

This guide provides advisory context for how execution state, triggers, and handoffs are used across workbooks.

## 1) When to use execution state files

Use `execution_state.yaml` when a workbook spans multiple phases, agents, or sessions, or when handoffs are expected.
For single-session runs, a complete Execution Log may be sufficient.

## 2) Trigger expectations

Use explicit triggers by default. Scheduled or event-driven runs are allowed only when documented in the workbook or
program artifacts.

## 3) Handoff guidance

When a handoff is expected, include a compacted context payload with:

- Current phase and status
- Key decisions and blockers
- Output paths
- Active context source path (workbook body vs bundle/program README)

Context placement defaults:

- standalone workbook/runbook: compacted context in artifact body,
- workbundle/runbundle lanes: compacted context in bundle README,
- workprogram/runprogram lanes: compacted context in program README (bundle README may hold local override).

## 4) Governance pointers

Enforceable requirements live in `spec_execution_orchestration.md`.
