---
title: Specs Index
version: 1.3.0
status: active
license: Apache-2.0
created: 2025-12-19
updated: 2026-05-05
owner: ai_ops
description: Canonical list of specs in priority reading order
---
<!-- markdownlint-disable-next-line MD025 -->
# Specs Index

## Purpose

Navigation index for all ai_ops specifications in priority reading order. Specs define requirements that
MUST or SHOULD be true across governance artifacts, execution surfaces, and repository structure.

Specs define requirements that MUST or SHOULD be true. Unlike contracts, specs may not be automatically enforced.

## Reading Priority

Read specs in this order:

### Priority 1: Repository Structure

1. `spec_repo_metadata_standard.md` - Metadata requirements for all files

### Priority 2: Artifact Patterns

1. `spec_workbook_structure.md` - Workbook structure and execution pattern
1. `spec_runbook_structure.md` - Runbook structure and governance
1. `spec_workflow_structure.md` - Workflow intent patterns and generation rules
1. `spec_execution_orchestration.md` - Execution lifecycle and state tracking
1. `spec_repository_indices.md` - Index hierarchy and update protocol

### Priority 3: Execution Coordination Contracts

1. `spec_workbundle_dependency_tracking.md` - Workbook dependency and impact declarations
1. `spec_workbundle_placement_suggestion.md` - Placement scoring and decision-echo contract
1. `spec_infrastructure_change_validation_gate.md` - Infrastructure-touching validation gate
1. `spec_context_routing_runtime.md` - Target-state runtime design for context_routing.yaml

### Priority 4: Output Contract Layer

1. `spec_policy_decision_record.md` - PDR schema: structured governance output agents emit at L2+ authority evaluations
1. `spec_async_approval_contract.md` - Async approval contract: PARK flow and CSCC context snapshot for L3/L4 gates
1. `spec_governance_lifecycle.md` - Governance lifecycle map (Before/During/Across) and circuit breaker conditions
1. `spec_cost_governance.md` - Quantitative cost governance: token budgets, model routing preferences, and alert thresholds

## Deprecated Specs (Archived to 99_Trash)

Deprecated tombstone specs are not retained in `00_Admin/specs/`. They are
moved to `99_Trash/` after successor mapping is recorded here.

- `spec_agent_hygiene.md` -> moved to
  `99_Trash/specs_tombstones_2026-03-04/spec_agent_hygiene.md`
  - canonical behavior moved to `AGENTS.md` and
    `spec_execution_orchestration.md`
- `spec_bootstrap_testing_suite.md` -> moved to
  `99_Trash/specs_tombstones_2026-03-04/spec_bootstrap_testing_suite.md`
  - canonical scenarios moved to `00_Admin/runbooks/rb_bootstrap.md`,
    `00_Admin/guides/ai_operations/guide_bootstrap_self_repair.md`, and
    `00_Admin/tests/fixtures/manifests/README.md`

## Spec Characteristics

All specs:

- Define technical and structural requirements
- Use MUST/SHOULD/MAY with intent and precision
- Reserve RECOMMENDED for guides and workflow docs (not specs)
- May or may not be validated
- Are versioned and stable
- Change via governance process

## Spec Archetypes

ai_ops uses four spec archetypes. The archetype determines structure; every spec still follows
the common minimum authoring rules in `00_Admin/guides/authoring/guide_spec.md`.

| Archetype | Use When | Examples |
| --- | --- | --- |
| `module_spec` | Module, feature, data model, API, or implementation surface | module specs in governed repos |
| `governance_spec` | Repository rules, workflow structure, authority behavior, lifecycle rules, or artifact structure | `spec_workbook_structure.md`, `spec_governance_enforcement.md` |
| `output_contract_spec` | Structured agent output, schema blocks, emission rules, or consumption rules | `spec_policy_decision_record.md`, `spec_async_approval_contract.md` |
| `runtime_design_spec` | Target-state runtime behavior that is not fully enforceable yet | `spec_context_routing_runtime.md` |

## Specs vs Contracts vs Policies

<!-- markdownlint-disable MD013 -->
| Aspect | Policy | Spec | Contract |
| --- | --- | --- | --- |
| Definition | Hard rules (how we work) | Requirements (what should be true) | Specs with validation (what + how to verify) |
| Language | MUST/MUST NOT | MUST/SHOULD/MAY | MUST plus validation code |
| Enforcement | Human judgment | Optional validation | Automated validation |
| Location | `00_Admin/policies/` | `00_Admin/specs/` or module docs | `../<work_repo>/01_Resources/<domain_core>/contracts/` |
| Example | Git workflow, naming | Metadata structure, artifact format | <engine_name>/<engine_name> data schema |
<!-- markdownlint-enable MD013 -->

Key insight: Contracts are specs with machine-enforced checks.

## Global vs Module-Specific

Global specs (here) affect all modules and projects. Module specs live in:

`02_Modules/<module>/docs/specs/` and apply only to that module.

## New Specs

To propose a new spec:

1. Create draft in appropriate location
2. Document rationale and examples
3. Create workbook for spec addition
4. Requires human approval (Level 4 governance)

## See Also

- Policies: `00_Admin/policies/README.md` (hard rules)
- Guides: `00_Admin/guides/README.md` (explanatory docs)
- Contracts: `../<work_repo>/01_Resources/<domain_core>/contracts/` (validated specs)
- AI Core: `../<work_repo>/01_Resources/<domain_core>/<domain_core>_index.yaml` (engine specs)
