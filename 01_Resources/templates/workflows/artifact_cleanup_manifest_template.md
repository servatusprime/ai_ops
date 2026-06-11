---
title: Artifact Cleanup Manifest Template
version: 1.0.0
status: active
license: Apache-2.0
created: 2026-06-11
updated: 2026-06-11
owner: ai_ops
description: Reviewable retention and cleanup manifest for transient work artifacts.
---

<!-- markdownlint-disable-next-line MD025 MD041 -->
# Artifact Cleanup Manifest

Use before pruning a workbundle with mixed evidence, benchmark, debug, and
generated outputs. Every candidate requires requestor-approved treatment.

## Manifest

| Source Path | Retention Class | Evidence / Reason | Approved By | Rollback / Recovery | Cleanup Dependency | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `<relative/path>` | `<class>` | `<why>` | `<actor/date>` | `<path or not_recoverable>` | `<dependency or none>` | `<pending/approved/executed>` |

Allowed retention classes:

- `canonical_promoted`
- `retain_latest_evidence`
- `benchmark_reference`
- `superseded_loop_output`
- `historical_debug`
- `delete_candidate`

## Gates

- [ ] Every source path exists or is explicitly marked already absent.
- [ ] `delete_candidate` rows have approval and recovery treatment.
- [ ] Canonical promotion is verified before dependent cleanup.
- [ ] Stale references are checked after execution.
- [ ] Cleanup results are recorded row by row.
