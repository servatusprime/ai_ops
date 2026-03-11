---
title: Log: Schema and Manifest Changes
version: 0.1.0
status: active
owner: ai_ops
created: 2026-01-24
updated: 2026-02-22
---

<!-- markdownlint-disable-next-line MD025 -->
# Log: Schema and Manifest Changes

Track changes to bootstrap-related schemas and manifests (aiops, session, execution state).

## Entry Template (Required Fields)

```yaml
entry:
  date: YYYY-MM-DD
  change_id: change_YYYYMMDD_nn
  files:
    - aiops.yaml
  versions:
    manifest_version: x.y.z
    data_version: x.y.z
  summary: "<short description>"
  compatibility:
    breaking: false
    notes: "<compatibility notes or migration guidance>"
```

## Entries

- 2026-01-24 | change_20260124_01 | Initialized schema/manifest change log. Files: log only. Compatibility: n/a.
- 2026-02-22 | change_20260222_01 | Added optional `modality` section to
  `aiops.yaml` (`active_surface`,
  `installation_target`, `confirmed_at`) and documented it in
  `guide_aiops_manifest.md`. Compatibility: non-breaking (optional fields).
- 2026-02-28 | change_20260228_01 | Retired `aiops.yaml` as bootstrap entry
  point. `AGENTS.md` is now the sole bootstrap entry point. Content migrated:
  workspace topology -> `AGENTS.md`, personal config (modality, work_repos) ->
  `.ai_ops/local/config.yaml`, setup_contract -> `00_Admin/configs/setup_contract.yaml`,
  read orchestration -> `context_routing.yaml` (already owned this).
  `guide_aiops_manifest.md` marked deprecated. Breaking change:
  `aiops.yaml` is deleted in WB2.
