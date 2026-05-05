---
title: Guide: Spec Authoring
version: 1.1.0
status: active
license: Apache-2.0
last_updated: 2026-05-05
owner: ai_ops
related:
- 01_Resources/templates/documents/spec-template.md
- 01_Resources/templates/documents/requirements_matrix_template.md
- 00_Admin/guides/authoring/guide_markdown_authoring.md
- 00_Admin/guides/architecture/guide_naming_conventions.md
- 00_Admin/policies/policy_requirements_management.md
- 00_Admin/policies/policy_status_values.md
- 00_Admin/specs/spec_repo_metadata_standard.md
---

<!-- markdownlint-disable MD025 -->

# Guide: Spec Authoring

## Purpose

Defines how to author specification documents for the repo. Covers spec archetypes, required frontmatter,
authoring rules, traceability expectations, and the relationship between specs and other governance artifacts.

## 1. Purpose and Scope

This guide defines how to author specification documents for ai_ops and governed repos. It covers common spec
requirements plus archetype-specific structure. It does not cover prompt authoring (see `guide_prompt_authoring.md`).

## 2. Document Types and Roles

- **Specification (Spec)**: Formal requirements, behavior, schema, or governance contract for a module or
  cross-cutting domain.
- **Requirements Matrix**: Traceability table mapping requirements to implementation and verification.
- **Glossary**: Central vocabulary in `../<work_repo>/01_Resources/guides/glossary.md` used across specs and prompts.

## 2.1 Spec Archetypes

Specs are not one-size-fits-all. Select the archetype that matches the artifact's job.

| Archetype | Use When | Required Shape |
| --- | --- | --- |
| `module_spec` | Defining a module, feature, data model, API, or implementation surface | Purpose and scope, terminology, `REQ-*` requirements, traceability links, design notes, examples, change log |
| `governance_spec` | Defining repository rules, workflow structure, authority behavior, lifecycle rules, or artifact structure | Purpose, scope, normative rules, enforcement or validation status, related references, change log |
| `output_contract_spec` | Defining structured agent output, schema blocks, emission rules, or consumption rules | Quick reference, purpose, scope, schema, emission or consumption rules, examples, change log |
| `runtime_design_spec` | Preserving target-state runtime behavior that is not fully enforceable yet | Purpose, current fallback, target-state contract, activation conditions, implementation roadmap, change log |

Use the simplest archetype that makes the spec cold-start useful for an agent. Do not force governance or output-contract
specs into `REQ-*` tables when schema, rules, and examples are more direct.

## 3. General Principles

- **Normative vs. informative**: Requirements and rules use MUST/SHOULD/MAY language; examples and rationale are
  informative.
- **Consistent structure**: Follow the selected spec archetype so sections are predictable for agents and humans.
- **Atomic requirements**: In `module_spec` artifacts, use one testable requirement per ID.
- **Traceability**: Link requirements, rules, or schemas to implementation and verification evidence when such evidence
  exists.
- **Terminology alignment**: Define new domain terms in the shared glossary.
- **AI-first retrieval**: Put the answer an agent needs near the top: purpose, applicability, status, and how to use the
  spec.

## 3.1 Acceptance Criteria (AC) Format

Acceptance Criteria MUST be binary and testable. Use a consistent format:

`GIVEN <precondition>, WHEN <action>, THEN <expected outcome>`

Avoid narrative or subjective AC. Each AC should be verifiable by a check or test.

## 4. Requirement ID Format

Requirement IDs are required for `module_spec` artifacts and optional for other archetypes when they add real
traceability value. Use the canonical pattern from `guide_naming_conventions.md`:

`REQ-<SPEC>-<SECTION>-<NNN>`

Example:

- `REQ-MODULE-3-001`

Where:

- `<SPEC>` is a short uppercase code (e.g., MODULE, ANALYSIS, MODELING).
- `<SECTION>` aligns to the spec section number.
- `<NNN>` is a zero-padded sequence within the section.

## 5. Specification Structure

Use the template in `01_Resources/templates/documents/spec-template.md`. All specs MUST include:

1. YAML frontmatter
2. Visible title
3. Purpose or quick reference
4. Scope or applicability
5. Normative content using MUST/SHOULD/MAY where behavior is required
6. Related references or links where relevant
7. Change log

Archetype-specific minimum sections:

### 5.1 Module Spec

1. Purpose and scope
2. Terminology and references
3. Requirements (with IDs)
4. Design details (non-normative)
5. Examples (non-normative)
6. Local change log

### 5.2 Governance Spec

1. Purpose
2. Scope
3. Rules or criteria
4. Enforcement or validation status
5. Related references
6. Change log

### 5.3 Output Contract Spec

1. Quick reference
2. Purpose
3. Scope
4. Schema
5. Emission, consumption, or lifecycle rules
6. Examples
7. Change log

### 5.4 Runtime Design Spec

1. Purpose
2. Current fallback policy
3. Target-state contract
4. Trigger or activation conditions
5. Implementation roadmap
6. Change log

### Front matter example

```yaml
---
spec_id: GIS
id: spec_gis_workflow
module: gis_workflow
title: Module Workflow Specification
status: active
license: Apache-2.0
version: 0.2.0
created: 2026-01-11
updated: 2026-01-11
owner: ai_ops
ai_generated: true
spec_archetype: module_spec
related:
  - 02_Modules/<module>/docs/specs/spec_<module>.md
---
```

`spec_archetype` SHOULD be present in all new specs. Existing specs should be
normalized opportunistically when touched.

## 6. Requirements Traceability Matrix

- Store matrices near the spec (module-level) or under `00_Admin/specs/` (cross-cutting).
- `module_spec` artifacts SHOULD have a requirements matrix when implementation work is expected.
- `governance_spec`, `output_contract_spec`, and `runtime_design_spec` artifacts MAY omit a matrix if the spec is
  primarily consumed by agents as prose/schema and no implementation pointer exists yet.
- Each matrix row must include: REQ ID, summary, implementation pointer, verification method, status.
- Keep links synchronized whenever requirements change.

## 7. Glossary Usage

Add cross-module terms to `../<work_repo>/01_Resources/guides/glossary.md`. Specs should reference glossary terms rather
than redefine common concepts.

## 8. Templates and References

- Spec template: `01_Resources/templates/documents/spec-template.md`
- Requirements matrix: `01_Resources/templates/documents/requirements_matrix_template.md`

## 9. Maintenance

- Update `last_updated` and `version` whenever requirements change.
- Keep status values aligned to `policy_status_values.md`.
- Record material changes in the local change log.
- When updating an existing spec, preserve its archetype unless the workbook explicitly authorizes a conversion.
