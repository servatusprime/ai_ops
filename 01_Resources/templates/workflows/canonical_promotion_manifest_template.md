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

## Promote-Forward Contract

Complete this block for each canonical artifact that is promoted in this batch
AND is depended-upon by later phases in the same session before a standalone
commit (see `/closeout` Step 6 promote-forward clause).

```yaml
promote_forward_contract:
  - artifact_path: <repo-relative path of the promoted artifact>
    evidence_ref: <path:line or command confirming the artifact is present and valid>
    rollback_plan: <how to revert if the promotion must be undone>
    actor: <agent or operator who authorized the promote-forward>
    approval_authority: <authority level and gate, e.g. "L4, servatusprime 2026-06-19">
    manifest_sync_batch: <true if manifest sync is in the same commit batch; false + rollback note if deferred>
```

If no artifacts are promoted forward in this batch, record `promote_forward_contract: none`.

## Gates

- [ ] Source and target paths are repo-relative.
- [ ] Every action has explicit approval.
- [ ] `loop_lineage_clean: true` for every promoted artifact.
- [ ] Canonical names and descriptions contain no execution-loop labels.
- [ ] Validation and rollback were exercised or explicitly justified.
- [ ] Cleanup occurs only after promotion validation passes.
- [ ] Promote-forward contract recorded for all depended-upon promoted artifacts
  (or `promote_forward_contract: none` if not applicable).
