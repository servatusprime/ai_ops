---
title: "Health Report: ai_ops (Option 2 Comprehensive)"
id: health_ai_ops_option2_comprehensive_2026-03-03
status: active
license: Apache-2.0
version: 0.1.0
created: 2026-03-03
updated: 2026-03-03
owner: ai_ops
target_repo: ai_ops
scope: option_2_comprehensive
dead_chain_depth: 1
routing_profile: health.command_profile
routing_fallback_used: false
routing_fallback_reason: none
context_reset_applied: true
scope_echo: "Comprehensive ai_ops health checks: consistency, metadata, dead-chain depth-1"
output_root_echo: "00_Admin/reports/health"
exclusions_echo: "<governed_repo>/** excluded from ai_ops target checks"
lock_preflight_status: pass
---

<!-- markdownlint-disable-next-line MD025 -->
# Health Report: ai_ops (Option 2 Comprehensive)

## Summary

Status: Unhealthy

Comprehensive checks found substantial existing validator debt and index
coverage drift, plus depth-1 dead-chain candidates without workflow/runbook
triggers.

## Findings

### Critical

- Repository validator fails with high issue volume.
  - Command: `python 00_Admin/scripts/validate_repo_rules.py --config 00_Admin/configs/validator/validator_config.yaml`
  - Signal: `validator_issue_lines=188`
  - Top issue codes: `VS022(39)`, `VS003(29)`, `VS008(26)`, `VS005(20)`, `VS023(15)`.
  - Fix stub:
    - Create a scoped validator-debt workbook lane for VS003/VS005/VS020/VS023.
    - Address structural blockers first (status/frontmatter/index consistency).

### Warning

- Guides index coverage drift in `00_Admin/guides/README.md`.
  - 12 `ai_operations` guides are not listed in index navigation.
  - Missing examples include:
    `guide_design_tests.md`, `guide_command_workflows.md`,
    `guide_skills_commands_classification.md`.
  - Fix stub:
    - Add missing `ai_operations` guide links to guides index.
    - Re-run validator and confirm VS020 reductions.

- Dead-chain candidates (depth 1) with zero workflow/runbook trigger refs.
  - `spec_agent_hygiene.md`
  - `spec_bootstrap_testing_suite.md`
  - `spec_execution_orchestration.md`
  - `spec_repo_metadata_standard.md`
  - Fix stub:
    - Either wire each spec into active workflows/runbooks or deprecate/archive.

- Active workbundle still has 2 open crosscheck markers.
  - `wb_root_docs_01.md:191`
  - `wb_template_reorg_01.md:491`
  - Fix stub: execute final crosscheck lane and synchronize workbook status rows.

### Info

- Baseline command surfaces are present:
  `.ai_ops/workflows` (13 files), `00_Admin/runbooks` (10 files),
  `00_Admin/specs` (18 files).
- Git remote synchronization is clean (`origin/main..main = 0`).
- Output lock preflight succeeded for report location.

## Metrics

| field_name | value | period | notes |
| --- | --- | --- | --- |
| `entropy_findings_count` | 188 | current run | validator issue-line count |
| `seed_velocity_created` | not_applicable | not_applicable | seed tracking not in this scope |
| `seed_velocity_actualized` | not_applicable | not_applicable | seed tracking not in this scope |
| `seed_velocity_ratio` | not_applicable | not_applicable | unavailable without seed ledger query |
| `recommended_actions_count` | 4 | current run | actions table below |

## Recommended Actions

| Priority | Action | Effort | Impact |
| --- | --- | --- | --- |
| 1 | Stand up validator-debt remediation workbook | L | High |
| 2 | Repair `00_Admin/guides/README.md` coverage gaps | M | High |
| 3 | Resolve dead-chain candidates (wire or retire) | M | Medium |
| 4 | Close remaining WB2/WB4 crosscheck gates | S | Medium |
