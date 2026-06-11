---
title: Canonical Promotion Manifest Template
version: 1.0.0
status: active
license: Apache-2.0
created: 2026-06-11
updated: 2026-06-11
owner: ai_ops
description: Reviewable source-to-canonical promotion, validation, rollback, and cleanup contract.
---

<!-- markdownlint-disable-next-line MD025 MD041 -->
# Canonical Promotion Manifest

## Manifest

| Source Path | Target Path | Action | Canonical Basename | Evidence | Approval State | Validation Command | Backup / Rollback | Cleanup Dependency | Loop Lineage Clean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `<relative/path>` | `<relative/path>` | `<copy/replace/merge>` | `<basename>` | `<path:line or command>` | `<pending/approved>` | `<command>` | `<path or action>` | `<dependency or none>` | `<true/false>` |

## Gates

- [ ] Source and target paths are repo-relative.
- [ ] Every action has explicit approval.
- [ ] `loop_lineage_clean: true` for every promoted artifact.
- [ ] Canonical names and descriptions contain no execution-loop labels.
- [ ] Validation and rollback were exercised or explicitly justified.
- [ ] Cleanup occurs only after promotion validation passes.
