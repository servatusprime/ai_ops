---
title: Quality Loop Convergence Template
version: 2.0.0
status: active
license: Apache-2.0
created: 2026-06-11
updated: 2026-11-04
owner: ai_ops
description: Loop-control contract for review and quality loops (caps, tiers, budget, residuals, sign-off).
---

<!-- markdownlint-disable-next-line MD025 MD041 -->
# Loop Control Contract

Fill one block per workbook that runs review or quality loops; the rules are in
`.ai_ops/workflows/crosscheck.md` "Loop Control", and the Crosscheck Stop Marker summarizes
this block.

```yaml
loop_control:
  convergence_profile: <iterative_convergence_minimal | iterative_convergence_standard>
  maximum_loop_count: <integer; 1 for iterative_convergence_minimal, 3 or lower for iterative_convergence_standard>
  validators:
    maximum_errors: <integer>
    plausibility_checks:
      - <check>
    allowed_info_residue:
      - <explicitly allowed informational condition>
  tier_1:
    loops_used: <integer>
    reviewer_level_per_loop: [<level>]
  tier_2:
    status: <not_required (Level 0 to 2 work only) | pending | done>
    delta_passes: <per tier-2 Major or Blocker, at most 2, apart from maximum_loop_count; then a decision card>
    reviewer_level: <level>
  budget: <review budget from cost_governance; spend so far>
  residuals:
    - id: <finding id>
      disposition: <fixed | accepted (never for a tier-2 Major or Blocker) | deferred_with_owner | decision_card>
  closeout_eligible_when:
    tier_2_status: <done | not_required (Level 0 to 2 work only)>
    unresolved_blocker_or_major: 0
    unresolved_decisions: 0
    operator_sign_off: <reserved closeout/publication decision; not an interim phase stop>
  operator_decision:
    decision: <accept/rework/pending>
    rationale: <required rationale>
    actor: <operator>
    date: <YYYY-MM-DD>
```

An empty decision or rationale means `pending` and blocks convergence. A tier-2 status of
`pending` also blocks closeout eligibility; `not_required` is valid only for Level 0 to 2 work.
`operator_sign_off` is the reserved closeout/publication decision, not an interim phase stop.
Reaching the maximum loop count requires a decision card; it never implies acceptance.
