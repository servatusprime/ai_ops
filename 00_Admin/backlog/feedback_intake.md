---
title: Feedback Intake Queue
version: 0.1.0
status: active
created: 2026-01-24
updated: 2026-01-24
owner: ai_ops
---

<!-- markdownlint-disable-next-line MD025 -->
# Feedback Intake Queue

Single intake queue for suggestions and critiques. Items are triaged in batches to avoid spam.

## Intake Template

```yaml
item:
  id: feedback_YYYYMMDD_nn
  source: "<agent | human | report>"
  summary: "<one line>"
  scope: "<affected area>"
  proposed_action: "<accept | defer | reject>"
  target:
    workbook: "<id or path>"
    future_work: "<id if moved>"
  notes: "<optional>"
```

## Items

- 2026-01-24 | feedback_20260124_01 | Initialized queue; no items yet.
