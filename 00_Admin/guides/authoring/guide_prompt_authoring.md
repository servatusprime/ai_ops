---
title: Guide: Prompt Authoring
version: 1.1.0
status: active
license: Apache-2.0
last_updated: 2026-02-07
owner: ai_ops
related:
- 01_Resources/templates/documents/PROMPT_SPEC_TEMPLATE.md
- 00_Admin/guides/authoring/guide_markdown_authoring.md
- 00_Admin/guides/authoring/guide_ai_assistants.md
- 00_Admin/guides/architecture/guide_naming_conventions.md
- 00_Admin/policies/policy_core_doc_structure.md
- 00_Admin/specs/spec_repo_metadata_standard.md
---

--- title: Guide: Prompt Authoring version: 1.0.0 status: active last_updated: 2026-01-12 owner: ai_ops
related:

- 01_Resources/templates/documents/PROMPT_SPEC_TEMPLATE.md
- 00_Admin/guides/authoring/guide_markdown_authoring.md
- 00_Admin/guides/authoring/guide_ai_assistants.md
- 00_Admin/guides/architecture/guide_naming_conventions.md
- 00_Admin/policies/policy_core_doc_structure.md --- <!-- markdownlint-disable MD025 -->

# Guide: Prompt Authoring

## 1. Purpose and Scope

This guide defines how to author prompt documents for <repo_name>. It covers prompt structure, metadata, and style. It
does not cover spec authoring (see `guide_spec.md`).

## 2. Prompt Document Types

- **Prompt outline**: A structured workflow or run definition for an AI agent.
- **Prompt spec**: A prompt outline with explicit inputs, outputs, and constraints.
- **Embedded prompt**: Prompt text embedded in another artifact (spec, runbook) with clear boundaries.

## 3. Front Matter (Required)

Use the template in `01_Resources/templates/documents/PROMPT_SPEC_TEMPLATE.md`. Include at least:

- `title`
- `module` (when module-specific)
- `status`
- `version`
- `owner`
- `last_updated`

## 4. Recommended Sections

- **Summary / Goal**
- **Inputs / Interface**
- **Outputs**
- **Constraints and Guardrails**
- **Steps / Workflow**
- **Example Invocation** (optional)
- **References**

## 4.1 CSCC Execution Addendum (Recommended)

For cold-start, capacity-constrained execution prompts, include:

- explicit read order
- explicit stop conditions
- explicit evidence contract (file path/section or command/key output)

Use the addendum block in
`01_Resources/templates/documents/prompt_spec_template.md`.

## 5. Style Rules

- Separate literal prompt text from editorial notes.
- Use consistent headings and list formatting so agents can parse the structure.
- Reference specs and contracts by ID where available.
- Avoid ambiguous terms; align vocabulary to `guide_ai_ops_vocabulary.md`.

## 6. Templates and References

- Prompt template: `01_Resources/templates/documents/PROMPT_SPEC_TEMPLATE.md`
- Markdown authoring rules: `00_Admin/guides/authoring/guide_markdown_authoring.md`

## 7. Maintenance

- Update `last_updated` and `version` when prompt behavior changes.
- Keep status values aligned to `policy_status_values.md`.
