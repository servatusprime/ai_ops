---
title: Quality Loop Convergence Template
version: 1.0.0
status: active
license: Apache-2.0
created: 2026-06-11
updated: 2026-06-11
owner: ai_ops
description: Bounded exit contract for iterative quality and adjudication loops.
---

<!-- markdownlint-disable-next-line MD025 MD041 -->
# Quality Loop Convergence Contract

```yaml
quality_loop_convergence:
  validators:
    - command: <command>
      maximum_errors: 0
      maximum_warnings: <integer>
  plausibility_checks:
    - name: <check>
      maximum_failures: 0
  allowed_info_residue:
    - <explicitly allowed informational condition>
  maximum_loop_count: <integer>
  operator_review_required_at: <integer>
  closeout_eligible_when:
    validators_pass: true
    plausibility_failures: 0
    unresolved_decisions: 0
    operator_sign_off: true
  operator_decision:
    decision: <accept/rework/pending>
    rationale: <required rationale>
    actor: <operator>
    date: <YYYY-MM-DD>
```

An empty decision or rationale means `pending` and blocks convergence. Reaching
the maximum loop count requires operator review; it does not imply acceptance.
