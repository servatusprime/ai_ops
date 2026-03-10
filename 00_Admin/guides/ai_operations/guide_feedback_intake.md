---
title: Guide: Feedback Intake
version: 0.1.0
status: active
license: Apache-2.0
last_updated: 2026-02-03
owner: ai_ops
related:
  - ./guide_workflows.md
  - ../../backlog/future_work_registry.yaml
---

# Guide: Feedback Intake

## Purpose

Define a lightweight, repeatable intake path for suggestions and review findings.

## Intake Flow

1. Capture feedback in active workbook/scratchpad.
2. Classify as in-scope now, future work, or reject.
3. Route accepted future items to `future_work_registry.yaml`.
4. Record rationale for deferred/rejected items.

## Triage Criteria

- Benefit (high/medium/low)
- Effort (XS-XL)
- Readiness (ready/partial/blocked/deferred)
- Risk if deferred

## Batch Review Cadence

- Quick pass during closeout.
- Full pass on scheduled governance reviews.
