---
title: Governance Enforcement Mechanism Spec
id: spec_governance_enforcement
module: admin
status: active
license: Apache-2.0
version: 0.2.0
created: 2026-02-14
updated: 2026-03-24
owner: ai_ops
ai_generated: true
---

<!-- markdownlint-disable-next-line MD025 -->
# Governance Enforcement Mechanism Spec

## Purpose

Define the audit criteria and promotion priority for governance mechanisms in ai_ops.
Governance rules without enforcement teeth should be formalized with validators or
removed to reduce maintenance burden.

## Scope

Applies to all governance mechanisms in ai_ops: validators, template gates, pre-commit
hooks, CI checks, and normative rules in specs/policies/guides. Use this spec when
evaluating whether a rule has sufficient enforcement backing.

## Audit Criteria for Governance Mechanisms

1. **Does this rule have enforcement?**
   - Machine-checkable validator (preferred)
   - Template-level gate or required field
   - Pre-commit hook or CI check
2. **If no enforcement, is it actively preventing issues?**
   - Check recent workbook/review archives for violations
   - If no violations found in 3+ months, consider removing rule
3. **Can it be promoted to validator?**
   - Path authority guard coverage
   - Frontmatter/schema completeness
   - Naming/structure conformance checks

## Promotion Priority (Highest ROI First)

- **High**: Rules frequently violated in reviews (add validator)
- **Medium**: Rules with manual check burden (templatize or automate)
- **Low**: Aspirational rules without active use (defer or remove)

## When Deferring Enforcement Implementation

- Record rationale: why enforcement is deferred
- Set review trigger: milestone or timeframe to revisit
- Document manual fallback: how to check compliance without automation
