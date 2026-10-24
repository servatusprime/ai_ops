---
title: Artifact Cleanup Manifest Template
version: 1.1.0
status: active
license: Apache-2.0
created: 2026-06-11
updated: 2026-10-23
owner: ai_ops
description: Reviewable retention and cleanup manifest for transient work artifacts.
---

<!-- markdownlint-disable-next-line MD025 MD041 -->
# Artifact Cleanup Manifest

Use before pruning a workbundle with mixed evidence, benchmark, debug, and
generated outputs. Every candidate requires requestor-approved treatment.

## Manifest

| Source Path | Tracked State | Ignore Evidence | Source SHA-256 | Retention Class | Collision Check | Active References | Evidence / Reason | Approved By | Rollback / Recovery | Cleanup Dependency | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `<relative/path>` | `<tracked/ignored/untracked/absent>` | `<git check-ignore result or not_ignored>` | `<sha256 or absent>` | `<class>` | `<clear/blocked + evidence>` | `<none or refs>` | `<why + receipt>` | `<actor/date>` | `<path or not_recoverable>` | `<dependency or none>` | `<pending/approved/executed/parked>` |

Allowed retention classes:

- `canonical_promoted`
- `retain_latest_evidence`
- `benchmark_reference`
- `superseded_loop_output`
- `historical_debug`
- `delete_candidate`

## Gates

- [ ] Every source path exists or is explicitly marked already absent.
- [ ] Every row records tracked state, ignore evidence, and a source hash before movement.
- [ ] `delete_candidate` rows have approval and recovery treatment.
- [ ] Collision and active-reference checks are clear or the row is parked.
- [ ] Canonical promotion is verified before dependent cleanup.
- [ ] Stale references are checked after execution.
- [ ] Cleanup results are recorded row by row.
- [ ] A failed move or validation leaves a partial receipt, named recovery owner,
      and exact resume point; no unresolved row is silently skipped.
