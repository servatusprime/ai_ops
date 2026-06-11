---
title: Reverse Crosscheck: ai_ops Last Pushed Governance Uplift
id: review_ai_ops_last_pushed_changes_reverse_crosscheck_2026-05-05
status: completed
created: 2026-05-05
reviewer: Codex
target_commit: aca0a5f05cefdf497c8d6f4f166b1a29747c1b79
target_repo: ai_ops
review_type: reverse_crosscheck
---

<!-- markdownlint-disable MD013 -->
# Reverse Crosscheck: ai_ops Last Pushed Governance Uplift

## Scope

Reviewed latest pushed ai_ops commit:

- `aca0a5f feat(governance): wb_platform_governance_uplift_01 closeout`

Focus:

- New governance specs and their examples.
- Template and AGENTS.md integration.
- Backlog, scorecard, and decision ledger updates.
- Validation against current repo rules.

## Evidence

| ID | Type | Evidence |
| --- | --- | --- |
| E-01 | git | `git show --stat --name-only --pretty=fuller HEAD` shows commit `aca0a5f` with 26 changed files. |
| E-02 | validator | `python 00_Admin/scripts/validate_repo_rules.py --config 00_Admin/configs/validator/validator_config.yaml` completed with warnings only. |
| E-03 | lint | `pre-commit run markdownlint --all-files` passed. |
| E-04 | generated artifact | Regenerating scorecard with repo-relative input/output changed only frontmatter `updated` and `source_registry`. |
| E-05 | path check | `Test-Path 90_Sandbox/ai_workbooks/wb_platform_governance_uplift_01_2026-04-12/wb_platform_governance_uplift_01.md` returned `False`. |
| E-06 | path check | `Test-Path 00_Admin/policies/policy_authority_levels.md` returned `False`. |
| E-07 | archive check | Closed workbook exists at `99_Trash/wb_platform_governance_uplift_01_2026-04-12/wb_platform_governance_uplift_01.md`. |

## Findings

### Critical

None.

### Medium

#### F-01: PDR spec examples contain broken evidence references

- `00_Admin/specs/spec_policy_decision_record.md:125` and `:141` cite `AGENTS.md#authority-levels`, but the current headings are `Authority Quick Reference` and `Authority Detail`.
- `00_Admin/specs/spec_policy_decision_record.md:142` cites missing path `00_Admin/policies/policy_authority_levels.md`.
- `00_Admin/specs/spec_policy_decision_record.md:160` cites `wb_platform_governance_uplift_01.md#phase-2-gate` without a repo-resolvable path.
- Enforcement type: `doc_only`.
- Disposition: `patch_now`.
- Fix: replace example references with resolvable repo-relative references, such as `AGENTS.md#authority-quick-reference`, `AGENTS.md#authority-detail`, and a generic active workbook placeholder where the example is intentionally illustrative.

#### F-02: Async approval examples point to a closed workbook path that no longer exists

- `00_Admin/specs/spec_async_approval_contract.md:132` and `:150` use `90_Sandbox/ai_workbooks/wb_platform_governance_uplift_01_2026-04-12/wb_platform_governance_uplift_01.md`.
- That path does not exist; the closed workbook is archived under `99_Trash/`.
- This conflicts with the same spec at `00_Admin/specs/spec_async_approval_contract.md:65`, which says `context_snapshot_path` MUST point to an artifact that enables cold resume.
- Enforcement type: `doc_only`.
- Disposition: `patch_now`.
- Fix: make examples generic and active-path based, for example `90_Sandbox/ai_workbooks/<active_workbook_packet>/<active_workbook>.md`, or update to an existing archived evidence path only if the example is explicitly labeled historical.

#### F-03: Future work registry source workbook paths are stale after closeout/archive

- `00_Admin/backlog/future_work_registry.yaml:379` and `:418` point to `90_Sandbox/ai_workbooks/wb_platform_governance_uplift_01_2026-04-12/wb_platform_governance_uplift_01.md`.
- The source workbook now exists in `99_Trash/wb_platform_governance_uplift_01_2026-04-12/wb_platform_governance_uplift_01.md`.
- These entries are future-work seeds and should remain cold-start useful after closeout.
- Enforcement type: `doc_only`.
- Disposition: `patch_now`.
- Fix: update `source_workbook` to the archived path or replace it with a self-contained compacted context block that does not depend on a sandbox path.

#### F-04: Generated scorecard carries a machine-local absolute source path

- `00_Admin/backlog/future_work_scorecard.md:6` has `source_registry: C:/RE_Projects/ai_ops/00_Admin/backlog/future_work_registry.yaml`.
- Regenerating with repo-relative paths produced `source_registry: 00_Admin/backlog/future_work_registry.yaml`.
- Canonical ai_ops artifacts should remain portable across machines.
- Enforcement type: `process_gap`.
- Disposition: `patch_now`.
- Fix: regenerate the scorecard from the ai_ops repo root with repo-relative arguments:
  `python 00_Admin/scripts/generate_future_work_scorecard.py --registry 00_Admin/backlog/future_work_registry.yaml --output 00_Admin/backlog/future_work_scorecard.md`.

### Low

#### F-05: New governance additions increased VS022 non-ASCII validator warnings

- Validator warnings include new or touched governance files such as `00_Admin/specs/spec_async_approval_contract.md`, `spec_cost_governance.md`, `spec_governance_lifecycle.md`, `spec_policy_decision_record.md`, `spec_runbook_structure.md`, `spec_workbook_structure.md`, AGENTS.md, and workbook templates.
- Examples include em dashes, section signs, arrows, and greater-than-or-equal symbols in new spec/template content.
- Some VS022 warnings predate this commit, but the pushed change adds warnings in newly created specs.
- Enforcement type: `code_enforced`.
- Disposition: `patch_now` for newly added specs; `follow_on_workbook` for wider legacy cleanup.
- Fix: normalize newly added governance specs and template additions to ASCII unless the repo intentionally relaxes VS022 for governance docs.

## Proposal vs Verified Guard

- Verified defects: 4 medium, 1 low.
- Improvement proposals: 0.
- Speculative recommendations explicitly marked as proposal seeds: no.

## Scope Integrity

- The commit scope is coherent with the governance-uplift closeout.
- The primary drift is reference hygiene after closeout/archive and portability of generated metadata.
- No destructive or out-of-scope changes were observed in the sampled diff.

## Validation Summary

- Repo validator: pass with warnings.
- Markdownlint: pass.
- Registry YAML parse: pass, 12 entries.
- Scorecard regeneration: deterministic content except expected date and source path frontmatter.

## Review Status

Status: Needs revision.

## Patch Follow-Up

Patch applied 2026-05-05 after review:

- F-01 patched: PDR examples now cite resolvable `AGENTS.md` anchors and use an active-workbook placeholder instead of a missing path.
- F-02 patched: async approval examples now use generic active workbook paths rather than the archived governance-uplift workbook path.
- F-03 patched: future-work registry source workbook paths now point to the archived `99_Trash` workbook.
- F-04 patched: scorecard regenerated with repo-relative `source_registry`.
- F-05 patched for the governance-uplift touched files: non-ASCII characters were normalized in new specs, touched templates, and touched governance docs. Remaining VS022 warnings are legacy files outside this patch scope.

Validation after patch:

- `python 00_Admin/scripts/validate_repo_rules.py --config 00_Admin/configs/validator/validator_config.yaml` passed with legacy warnings only.
- `pre-commit run markdownlint --all-files` passed.
- `python -c "... yaml.safe_load(...)"` passed for `future_work_registry.yaml`.

Additional upstream/downstream spec-consistency patch applied 2026-05-05:

- `guide_spec.md`, `spec-template.md`, and `specs/README.md` now define spec archetypes:
  `module_spec`, `governance_spec`, `output_contract_spec`, and `runtime_design_spec`.
- All `00_Admin/specs/spec_*.md` files now declare `spec_archetype` in frontmatter.
- Legacy specs were normalized with explicit Change Log sections; two specs received explicit scope/applicability sections.
- Downstream audit confirmed no missing `spec_archetype`, purpose/quick reference, scope/applicability, or Change Log sections across `00_Admin/specs/spec_*.md`.
