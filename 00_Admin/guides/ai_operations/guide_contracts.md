---
title: Guide: Contracts
version: 1.0.0
status: active
license: Apache-2.0
last_updated: 2026-01-12
owner: ai_ops
related:
  - ./guide_ai_operations_stack.md
  - ./guide_ai_ops_vocabulary.md
promoted_from: 90_Sandbox/AI_Operations_Drafts/guide_contracts.md
---

<!-- markdownlint-disable-next-line MD025 -->

# Guide: Contracts

This guide defines **Contracts** within the AI Operations Stack. It is normative.

## Definition

A **Contract** is a verification-first artifact that defines:

- What is allowed
- What is required
- What constitutes success

Contracts provide **behavioral guarantees**. They are the primary safety boundary in the system.

## Contract Responsibilities

Contracts MUST define:

- Constraints (hard safety rules)
- Checks (assertions that define success)

Contracts MAY define:

- Required state
- Preconditions
- Outputs

Contracts MUST NOT define:

- Strategy
- Orchestration
- Tool selection logic

## Execution Policy

A Contract may specify an execution policy:

- **Strict** - all conditions must be met exactly
- **Flexible** - implementation details may vary within constraints

Execution policy governs *how much freedom* an executing agent has, not what is allowed.

## Relationship to Other Artifacts

- Workflows reference Contracts by ID
- Pipelines sequence work that must satisfy Contracts
- Tools implement behavior hidden behind Contracts

## Contracts vs Tools

- Contracts define guarantees
- Tools implement behavior
- Tools may change without invalidating Contracts

## Governance Rules

- Contracts are reusable and long-lived
- Changes require deliberate review
- Contracts should evolve more slowly than code

## Existing Contracts in Repository

- Interface pattern: `../<work_repo>/01_Resources/<domain_core>/contracts/spec_interface_contract_design_pattern.md`
- Engine handoffs:
- `spec_contract_zle_to_fle_v0_1_0.md`
- `spec_contract_fle_to_ele_v0_1_0.md`
- `spec_contract_ele_to_mle_v0_1_0.md`
- Operational:
- `spec_contract_qa_ruleset.md`
- `spec_contract_coverage_matrix.md`
- Data schema:
- `schema_zle_fle_exchange_v0_1_0.yaml`

## Contract Discovery

- Primary location: `../<work_repo>/01_Resources/<domain_core>/contracts/`
- Indices: `../<work_repo>/01_Resources/<domain_core>/<domain_core>_index.yaml` (phase context), `../<work_repo>/01_Resources/<domain_core>/ai_workbook_index.yaml`
  (workbook references).
- Modules may reference contracts in their docs; prefer the canonical files above.

## Versioning Guidance

- Use semantic versioning in filenames and front matter.
- Prefer additive changes; breaking changes SHOULD trigger new version within 90 days of approval.
- Reference by ID/path, not by inference; old versions remain for traceability until formally deprecated.

## Design Principle

**Constraints and checks are hard. Implementations are soft.**

This principle allows the system to evolve safely while remaining enforceable by AI agents.
