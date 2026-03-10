---
title: "Health Report: ai_ops (Option 2 Comprehensive, Full Repo Scoped)"
id: health_ai_ops_option2_comprehensive_2026-03-04
status: active
license: Apache-2.0
version: 0.1.0
created: 2026-03-04
updated: 2026-03-04
owner: ai_ops
target_repo: ai_ops
scope: option_2_comprehensive
dead_chain_depth: 1
routing_profile: health.command_profile
routing_fallback_used: false
routing_fallback_reason: none
context_reset_applied: true
scope_echo: "ai_ops comprehensive health scan excluding 90_Sandbox/** and 99_Trash/**"
output_root_echo: "00_Admin/reports/health"
exclusions_echo: "90_Sandbox/**, 99_Trash/**"
lock_preflight_status: pass
---

<!-- markdownlint-disable-next-line MD025 -->
# Health Report: ai_ops (Option 2 Comprehensive, Full Repo Scoped)

## Summary

Status: Needs Attention

Repo-wide scoped checks show solid lint posture but persistent governance/index
consistency debt in canonical `00_Admin` surfaces.

## Scope Metrics

- Scoped markdown files analyzed: `215`
- Frontmatter/H1 scope files (`00_Admin/guides|policies|runbooks`): `73`
- Placement-audit sections inventoried (Option 3 companion): `2260`

## Findings

### Warning

- Guide index coverage drift (`VS020`-like signal).
  - `00_Admin/guides/README.md` misses `13` guide files.
  - Missing examples:
    `guide_design_tests.md`, `guide_command_workflows.md`,
    `guide_execution_orchestration.md`.
  - Fix stub:
    - Add missing guide links to `00_Admin/guides/README.md`.
    - Re-run index crosscheck.

- Frontmatter compliance gap in guides lane.
  - `00_Admin/guides/runbooks/README.md` is missing frontmatter delimiter.
  - Fix stub:
    - Add compliant YAML frontmatter.
    - Keep file as lightweight pointer to canonical runbooks index.

- H1-shape inconsistencies across governance docs.
  - `13` files have H1 count not equal to 1.
  - High-signal examples:
    `guide_capability_certification.md (6)`,
    `guide_runbooks.md (8)`,
    `rb_repo_validator_01.md (3)`.
  - Fix stub:
    - Normalize to single H1 per file.
    - Downgrade repeated title blocks to H2+.

- Dead-chain candidates (depth 1, no workflow/runbook trigger refs).
  - `spec_agent_hygiene.md`
  - `spec_bootstrap_testing_suite.md`
  - `spec_execution_orchestration.md`
  - `spec_repo_metadata_standard.md`
  - Fix stub:
    - Wire into active workflow/runbook references or deprecate/archive.

- Canonical placement conflict.
  - `00_Admin/guides/runbooks/README.md` overlaps
    `00_Admin/runbooks/README.md`.
  - Fix stub:
    - Preserve canonical runbook index in downstream location.
    - Convert guide-side file to pointer-only.

### Info

- Scoped markdownlint: pass (`markdownlint . --ignore 90_Sandbox/** --ignore 99_Trash/**`).
- Output lock-preflight for reports directory: pass.
- Dead-chain depth used: `1` (candidate signal level).

## Metrics

| field_name | value | period | notes |
| --- | --- | --- | --- |
| `entropy_findings_count` | 31 | current run | 13 index + 13 H1 + 4 dead-chain + 1 placement |
| `seed_velocity_created` | not_applicable | not_applicable | out of scope |
| `seed_velocity_actualized` | not_applicable | not_applicable | out of scope |
| `seed_velocity_ratio` | not_applicable | not_applicable | out of scope |
| `recommended_actions_count` | 5 | current run | see action table |

## Recommended Actions

| Priority | Action | Effort | Impact |
| --- | --- | --- | --- |
| 1 | Fix guide index coverage gaps | S | High |
| 2 | Normalize H1 counts in flagged governance docs | M | High |
| 3 | Resolve runbooks index placement conflict | S | Medium |
| 4 | Triage depth-1 dead-chain specs (wire or retire) | M | Medium |
| 5 | Re-run full scoped `/health` after remediation | S | Medium |
