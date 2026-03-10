---
title: "Audit: <repo> Section Reorder Map"
id: audit_<repo>_section_reorder_map_<YYYY-MM-DD>
status: active
license: Apache-2.0
version: 0.1.0
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
owner: ai_ops
authority_level: 0
execution_mode: read_only
scope_mode: option_3_section_placement
target_repo: <repo>
output_root: <resolved_output_path>
---

<!-- markdownlint-disable-next-line MD025 -->
# Audit: <repo> Section Reorder Map

## Purpose

Provide second-pass mapping for in-file content rearrangement after
upstream/downstream placement moves are applied.

## Method Note

State parser assumptions (for example, whether fenced code headings are
excluded).

## Baseline Outcome

- Immediate reorder actions (current state): <none or count>
- Reorder work should be treated as Pass B after placement moves settle.

## Pass B Sequencing Rule

1. Execute placement moves first.
2. Confirm dedup clusters passed nuance-retention checks.
3. Re-open changed files and normalize section order against runtime read path.
4. Re-run `/health` Option 3 section placement audit.

## Nuance Retention Gate (Pass A Exit)

- [ ] Every dedup cluster has canonical target + axis rationale recorded.
- [ ] Nuance-retention status is `pass` or explicitly accepted risk.
- [ ] No critical detail was dropped during dedup consolidation.

## Post-Move Reorder Targets (Conditional)

### Target: `<path>`

1. <order instruction>
2. <order instruction>
3. <order instruction>

## Warranted Duplication Guidance

- <when duplication is justified across related template/workflow families>

## Order Validation Checklist (Pass B)

- [ ] Purpose/objective appears near top.
- [ ] Decision/qualification logic appears before execution steps.
- [ ] Execution steps precede outputs/reporting.
- [ ] Closeout/selfcheck sections remain near end.
- [ ] No appendix/reference sections precede core execution sections.

## Related Artifacts

- `audit_<repo>_section_placement_<YYYY-MM-DD>.md`
- `audit_<repo>_section_placement_inventory_<YYYY-MM-DD>.csv`
