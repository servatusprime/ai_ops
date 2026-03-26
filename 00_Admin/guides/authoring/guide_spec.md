---
title: Guide: Spec Authoring
version: 1.0.2
status: active
license: Apache-2.0
last_updated: 2026-03-24
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

Defines how to author specification documents for the repo. Covers spec structure, required frontmatter,
authoring rules, and the relationship between specs and other governance artifacts.

## 1. Purpose and Scope

This guide defines how to author specification documents for <repo_name>. It covers spec structure, requirement IDs, and
traceability expectations. It does not cover prompt authoring (see `guide_prompt_authoring.md`).

## 2. Document Types and Roles

- **Specification (Spec)**: Formal requirements and behavior for a module or cross-cutting domain.
- **Requirements Matrix**: Traceability table mapping requirements to implementation and verification.
- **Glossary**: Central vocabulary in `../<work_repo>/01_Resources/guides/glossary.md` used across specs and prompts.

## 3. General Principles

- **Normative vs. informative**: Requirements use MUST/SHOULD language; examples and rationale are informative.
- **Consistent structure**: Follow the spec template to keep sections predictable for agents and humans.
- **Atomic requirements**: One testable requirement per ID.
- **Traceability**: Link requirements to implementation and verification evidence.
- **Terminology alignment**: Define new domain terms in the shared glossary.

## 3.1 Acceptance Criteria (AC) Format

Acceptance Criteria MUST be binary and testable. Use a consistent format:

`GIVEN <precondition>, WHEN <action>, THEN <expected outcome>`

Avoid narrative or subjective AC. Each AC should be verifiable by a check or test.

## 4. Requirement ID Format

Use the canonical pattern from `guide_naming_conventions.md`:

`REQ-<SPEC>-<SECTION>-<NNN>`

Example:

- `REQ-MODULE-3-001`

Where:

- `<SPEC>` is a short uppercase code (e.g., MODULE, ANALYSIS, MODELING).
- `<SECTION>` aligns to the spec section number.
- `<NNN>` is a zero-padded sequence within the section.

## 5. Specification Structure

Use the template in `01_Resources/templates/documents/spec-template.md`. Minimum sections:

1. Purpose and scope
2. Terminology and references
3. Requirements (with IDs)
4. Design details (non-normative)
5. Examples (non-normative)
6. Local change log

### Front matter example

```yaml
---
spec_id: GIS
title: Module Workflow Specification
status: active
version: 0.2.0
owner: ai_ops
related:
  - 02_Modules/<module>/docs/specs/spec_<module>.md
last_updated: 2026-01-11
---
```

## 6. Requirements Traceability Matrix

- Store matrices near the spec (module-level) or under `00_Admin/specs/` (cross-cutting).
- Each row must include: REQ ID, summary, implementation pointer, verification method, status.
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
