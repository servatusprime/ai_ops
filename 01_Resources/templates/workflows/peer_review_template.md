---
title: Crosscheck Review - <subject>
version: 0.3.0
status: active
license: Apache-2.0
created: YYYY-MM-DD
owner: ai_ops
reviewer: <agent_name>
review_type: completion  # design | mid_execution | completion
scope: <one-line description of what is being reviewed>
review_direction: top-down  # top-down | bottom-up | hybrid
review_strictness: strict  # standard | strict
workbook_ref: <path/to/workbook.md>  # workbook under review; enables routing to scope/authority
authority_level: 3  # authority level of the reviewed artifact (0-4)
path_basis: workspace_root  # path anchor used in evidence refs: workspace_root | repo_root | relative
evidence_schema: path_line_or_command  # required evidence format: path:line OR command + key output
---

<!-- markdownlint-disable-next-line MD025 MD041 -->
# Crosscheck Review - <subject>

## AI-First Guidance

- Keep findings concise and actionable.
- Use severity ordering to reduce review time.
- Thrift is not minimalism. Thrift is efficiency -- the minimum cost to achieve
  the required outcome.
- **Checklists are mandatory gates.** Verify each item explicitly; mark pass or fail with evidence.
  Do not publish a review until every checklist item is verified.
- In `strict` reviews, every finding must cite evidence (`path:line` or command output snippet).
- Distinguish verified defects from improvement proposals.

## Executive Summary

<2-3 sentences summarizing overall assessment and key findings.>

## Review Context

- **Artifact(s) reviewed**: <paths or IDs>
- **Review type**: <design | mid_execution | completion>
- **Review direction**: <top-down | bottom-up | hybrid>
- **Review strictness**: <standard | strict>
- **Reviewer**: <agent name>
- **Date**: YYYY-MM-DD

## Evidence Ledger (Required)

Evidence schema: every finding citation must reference an entry in this ledger.
Acceptable forms: `path:line` (file evidence) or `command -> key output line` (command evidence).
Narrative-only evidence is not acceptable in `strict` reviews.

| Evidence ID | Type | Location/Command | Key Output |
| --- | --- | --- | --- |
| E-01 | file | `<path/to/file.md:42>` | `<observed content>` |
| E-02 | command | `<command>` | `<key line>` |

## CSCC Readiness Audit

| Check | Status | Evidence |
| --- | --- | --- |
| Cold-start read order explicit | pass/fail | E-xx |
| Manual gates are explicit | pass/fail | E-xx |
| Validation evidence machine-verifiable | pass/fail | E-xx |
| No hidden defaults for business parameters | pass/fail | E-xx |

## Source Control Traceability (Bottom-Up)

Use this section for `bottom-up` and `hybrid` reviews. Keep it concise.

### Changed Files Inventory

| File | Change Type | Authorized By | Track/Task |
| --- | --- | --- | --- |
| `<path/to/file.md>` | modified | `A3` | Track A |
| `<path/to/new.md>` | new | `B11` | Track B |
| `<path/to/untraced.md>` | modified | **UNTRACED** | -- |

### Traceability Summary

- Total files changed: N
- Traced to workbook tasks/scope: N
- Untraced changes: N

### Untraced Changes (Requires Justification)

1. `<path/to/file.md>` - Reason: <why change is acceptable or remediation needed>

### VS025 Disposition (If Applicable)

- VS025 warnings found: N
- Disposition:
  - `<path>` - intentional | oversight - <short reason>

## Findings (Ordered by Severity)

### Critical (Blocking)

<Items that must be resolved before proceeding. If none, write "None.">

### Medium (Should Fix)

1. **<Finding title>**
   - <Description of the issue>
   - Evidence: `E-xx`
   - Enforcement type: `<code_enforced | doc_only | process_gap>`
   - Disposition: `<patch_now | proposal_seed | follow_on_workbook>`
   - Fix: <Recommended resolution>

### Low (Non-Blocking)

1. **<Finding title>**
   - <Description>
   - Evidence: `E-xx`
   - Enforcement type: `<code_enforced | doc_only | process_gap>`
   - Disposition: `<patch_now | proposal_seed | follow_on_workbook>`
   - Fix: <Recommended resolution>

## Proposal vs Verified Guard

- Verified defects (must fix now): <count>
- Improvement proposals (not defects): <count>
- Speculative recommendations explicitly marked as proposal seeds: yes/no

## Scope Integrity

- <Confirm no scope drift beyond intended work>
- <Note any unintended side effects>

## Scope Verification (Bottom-Up)

- [ ] All changed files are accounted for in workbook scope
- [ ] No files outside declared `shared_files` were modified without justification
- [ ] New files are referenced in appropriate indexes/guides/runbooks
- [ ] No policy/spec changes occurred without required approval level
- [ ] Collateral edits are documented and minimal

## Repo Axis Compliance

### Clarity Pass (Cold-Start Read)

- [ ] A low-context reader can follow inputs, steps, and outputs without inference.
- [ ] Required files/templates are named with explicit paths.
- [ ] Ambiguous terms are clarified or linked.
- [ ] Mode differences (inside vs external) are explicit where applicable.

### Thrift Pass

- [ ] No bloat introduced (remove redundancy, tighten wording).
- [ ] Unnecessary additions identified and flagged.
- [ ] Execution scope is minimal (no processing of trash/archived items without cause).
- [ ] Internal cycle burden check: touched docs do not add avoidable read hops.
- [ ] Relocation check: moved content has explicit landing zone and valid pointer.

### Context Pass (Downstream Placement)

- [ ] Operational context is placed downstream, near consumers (not in upstream governance).
- [ ] No upstream files carry operational detail that belongs in downstream docs.
- [ ] Downstream artifacts reference upstream governance by path, not by inline copy.
- [ ] Context routing is centralized where applicable (config YAML, not per-file duplication).

### Governance Pass (Upstream Placement)

- [ ] Governance rules are placed upstream (specs, policies, guides), not in downstream operational docs.
- [ ] Authority gates are explicit and referenced from canonical upstream sources.
- [ ] No downstream artifacts introduce governance rules without upstream backing.
- [ ] Enforcement surfaces (validators, linters) are aligned with upstream rule sources.

### Streamlining Pass

- [ ] Touched docs reduce or preserve execution efficiency for cold-start agents.
- [ ] Required read order is explicit and does not force unnecessary backtracking.
- [ ] No duplicate normative rule blocks remain without a provenance note.

## Smoke Pass Checklist

- [ ] Terminology alignment: canonical terms used correctly
- [ ] Scope integrity: no unapproved expansions or orphaned references
- [ ] Reference integrity: all cited paths resolve
- [ ] Artifact completeness: required sections/deliverables present

## Reviewer Integrity Check

- [ ] Review is objective and evidence-based
- [ ] Findings are actionable (each has a recommended fix)
- [ ] Severity classifications are appropriate
- [ ] No personal preferences disguised as findings

## Review Status

Status: <Acceptable | Acceptable with minor cleanup | Needs revision | Blocking issues>

---

## Review Timing Patterns

Use this section as guidance for when to conduct reviews (delete from actual reviews):

| Review Type | When | Focus | Output |
| --- | --- | --- | --- |
| Design | Before execution begins | Architecture, scope, approach | Approve/revise plan |
| Mid-execution | After significant milestones | Progress, direction, early issues | Course corrections |
| Completion | After all tasks done | Quality, completeness, compliance | Accept/reject deliverables |

Choose review type based on workbook complexity:

- **Simple (1-5 tasks)**: Completion review only
- **Medium (6-14 tasks)**: Completion review, optional mid-execution
- **Complex (15+ tasks)**: Design review + mid-execution checkpoint + completion review
