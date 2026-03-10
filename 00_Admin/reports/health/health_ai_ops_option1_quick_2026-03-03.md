---
title: "Health Report: ai_ops (Option 1 Quick)"
id: health_ai_ops_option1_quick_2026-03-03
status: active
license: Apache-2.0
version: 0.1.0
created: 2026-03-03
updated: 2026-03-03
owner: ai_ops
target_repo: ai_ops
scope: option_1_quick
routing_profile: health.command_profile
routing_fallback_used: false
routing_fallback_reason: none
context_reset_applied: true
scope_echo: "Quick health check for ai_ops with active workbook focus"
output_root_echo: "00_Admin/reports/health"
exclusions_echo: "<governed_repo>/** excluded from ai_ops target checks"
lock_preflight_status: pass
---

<!-- markdownlint-disable-next-line MD025 -->
# Health Report: ai_ops (Option 1 Quick)

## Summary

Status: Needs Attention

Quick checks passed for baseline structure and output-path lock preflight, but
two workbook crosscheck stop markers are still open in the active workbundle.

## Evidence

- `git status --porcelain=v1` (from workspace root) -> `ai_ops_changes=1`,
  `governed_repo_changes=20`, `total_changes=21`.
- Root/baseline existence checks -> all required files found:
  `README.md`, `CONTRIBUTING.md`, `AGENTS.md`, `HUMANS.md`,
  validator config/scripts, validator runbook.
- Lock preflight on `00_Admin/reports/health` -> create/delete temp file both
  returned `True`.
- Workbook marker scan:
  `open_crosscheck_markers=2` in
  `wb_root_docs_01.md:191` and `wb_template_reorg_01.md:491`.

## Findings

### Warning

- Two crosscheck gates remain open in active workbook scope.
  - `90_Sandbox/ai_workbooks/wp_oss_doc_visual_01_2026-03-02/wb_root_docs_01.md:191`
  - `90_Sandbox/ai_workbooks/wp_oss_doc_visual_01_2026-03-02/wb_template_reorg_01.md:491`
  - Fix stub: run/record `/crosscheck` for WB2 and WB4, then sync README row.

### Info

- ai_ops baseline files for validator and command health lane are present.
- Output location lock-preflight passed for report generation.
- governed repo has active changes, but excluded for this ai_ops-targeted report.

## Recommended Actions

| Priority | Action | Effort | Impact |
| --- | --- | --- | --- |
| 1 | Close WB2/WB4 crosscheck stop markers with evidence | S | High |
| 2 | Keep ai_ops/governed-repo scope separation explicit in next checks | S | Medium |
