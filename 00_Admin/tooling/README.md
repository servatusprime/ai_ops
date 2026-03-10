---
title: tooling_readme
version: 0.4.0
status: active
license: Apache-2.0
owner: ai_ops
created: 2026-02-25
updated: 2026-02-25
---

# Tooling

Tool manifests, scripts, and supporting assets for ai_ops core operations.

## Boundary Contract

- `ai_ops/00_Admin/tooling/` stores core tooling docs/index surfaces only.
- Domain-specific tooling docs/manifests belong in the target work repo under
  `<work_repo>/00_Admin/tooling/`.
- During migration windows, use explicit compatibility notes instead of
  duplicating primary docs across repos.

## Trigger and Ownership

- Trigger: update this folder when ai_ops core tooling behavior changes.
- Owner: ai_ops maintainers.
- Consumer: `/work`, `/health`, and tooling runbooks.
