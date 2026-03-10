---
title: "Health Report: ai_ops (Option 1 Quick, Full Repo Scoped)"
id: health_ai_ops_option1_quick_2026-03-04
status: active
license: Apache-2.0
version: 0.1.0
created: 2026-03-04
updated: 2026-03-04
owner: ai_ops
target_repo: ai_ops
scope: option_1_quick
routing_profile: health.command_profile
routing_fallback_used: false
routing_fallback_reason: none
context_reset_applied: true
scope_echo: "ai_ops full repo quick health scan excluding 90_Sandbox/** and 99_Trash/**"
output_root_echo: "00_Admin/reports/health"
exclusions_echo: "90_Sandbox/**, 99_Trash/**"
lock_preflight_status: pass
---

<!-- markdownlint-disable-next-line MD025 -->
# Health Report: ai_ops (Option 1 Quick, Full Repo Scoped)

## Summary

Status: Needs Attention

Core baseline files and lock preflight checks pass, but quick structural checks
show index/placement drift in guides surfaces.

## Evidence

- Scoped markdown files: `215`
  (excluded: `90_Sandbox/**`, `99_Trash/**`).
- Baseline files present:
  `README.md`, `CONTRIBUTING.md`, `AGENTS.md`, `HUMANS.md`,
  validator config/scripts, validator runbook.
- Lock preflight:
  create/delete in `00_Admin/reports/health` succeeded.
- Placement conflict signal:
  `guides/runbooks/README.md -> 00_Admin/runbooks/README.md`.
- Guides index drift:
  `missing_in_index=13` guide files.

## Findings

### Warning

- Guides index coverage drift in `00_Admin/guides/README.md`.
  - 13 guide files are not represented in index navigation.
  - Fix stub: add missing links and rerun index checks.

- Duplicate index lane for runbooks.
  - `00_Admin/guides/runbooks/README.md` overlaps canonical
    `00_Admin/runbooks/README.md`.
  - Fix stub: reduce guide-side file to pointer with compliant frontmatter.

### Info

- Baseline root/config/validator assets required by `/health` are present.
- Scoped markdownlint run returned clean (`exit=0`) for this exclusion set.

## Recommended Actions

| Priority | Action | Effort | Impact |
| --- | --- | --- | --- |
| 1 | Repair guides index coverage gaps | S | High |
| 2 | Consolidate runbook index ownership | S | Medium |
| 3 | Keep scope exclusions explicit in future health runs | S | Medium |
