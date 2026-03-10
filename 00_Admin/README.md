---
title: 00_admin_readme
version: 0.1.0
status: active
author: chatgpt
owner: ai_ops
created: 2025-12-19
updated: 2026-02-25
ai_generated: true
core_doc_exempt: false
---
## 00_Admin Overview

- Role: canonical governance/context for the repo (policies, guides, specs, configs, logs, runbooks, context/sentinels).
- Key roots:
- `configs/`: only config root (env, qgis, vscode, etc.).
- `logs/`: persistent audit logs and reports.
- `context/`: sentinels, audit trace/reflection/intent/migration, decision_ledger.
- `runbooks/`: reusable execution workflows (prefixed `rb_`) for operations.
- `specs/`, `policies/`, `guides/`: governance documents.
- For AI agents: start with `runbooks/rb_repo_health_review.md` and follow status values/policies in specs.
