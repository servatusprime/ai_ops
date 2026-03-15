---
title: 01_resources_readme
version: 0.3.0
status: active
author: chatgpt
owner: ai_ops
created: 2025-12-19
updated: 2026-03-14
ai_generated: true
core_doc_exempt: false
---
<!-- markdownlint-disable-next-line MD025 -->
# 01_Resources Overview

- Purpose: shared, mostly read-only resource library for authoring and execution
  across commands and workflows (not a single-command folder).
- Current top-level subfolders:
  - `prompts/`: reusable workflow starter prompts by domain.
  - `templates/`: reusable templates for operational artifacts.
    See `01_Resources/templates/README.md` for the full template catalog.
  - `licenses_disclaimers/`: reusable legal/disclaimer snippets for outward-facing deliverables.
    Definition: text blocks for attribution, legal notice, and usage disclaimers in generated outputs.
    Warrant: keep only if there is a plausible export/distribution use case that needs repeatable legal text.
    Trigger: use when a workbook/runbook includes packaging artifacts for external sharing and requires
    license/disclaimer insertion.
- Optional subfolders (created on first real governed asset; not pre-created as empty placeholders):
  - `guides/`: cross-cutting reference guidance for resource usage.
- Current `templates/` families: `documents/`, `scripts/`, `workflows/`.
  See `01_Resources/templates/README.md` for the per-family catalog with consumer and audience notes.
- Command-agnostic usage:
  - Resources in this folder may be consumed by `/work`, `/health`,
    `/crosscheck`, `/closeout`, and non-command authoring lanes.
  - Do not imply that any single command exclusively owns this folder.
- Maintenance:
  - Sandbox clones are non-canonical unless promoted; mark duplicates with
    pointers.
  - Align status values and schemas with policies/specs; log conflicts in
    future-work tracking.
  - Update this README when top-level folders or template families change.
