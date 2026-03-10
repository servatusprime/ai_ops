---
spec_id: <module_code>  # e.g. analysis_engine, gis_workflow, financial_modeling (matches folder name)
title: <Module Name> - Specification
status: stub
license: Apache-2.0
version: 0.1.0
owner: ai_ops
related: []
last_updated: YYYY-MM-DD
---

<!-- markdownlint-disable MD025 MD051 -->

# <Module Name> - Specification

## AI-First Guidance

- Keep sections concise and skimmable (bullets > paragraphs).
- Prefer explicit requirements over narrative.
- Use consistent REQ IDs for traceability.

## 1. Purpose & Scope

Briefly describe the module or feature and the scope of this specification. Include context, goals, and any boundaries
of what is or is not covered.

## 2. Terminology & References

- Define key terms or acronyms here, or reference the global glossary. Example: **NOI** - Net Operating Income (see
  Glossary).
- List related documents or specs: `[GIS Module Spec](spec_gis.md)`.

## 3. Requirements

### 3.1 <Topic or Feature Area>

**REQ_<module_code>_0001**: *Requirement statement here (an enforceable rule or capability).*  
Rationale: *(optional)* Brief explanation for context or why this requirement exists.  
Links:

- [Parent](#31-topic-or-feature-area)
- [Traceability](../docs/requirements_matrix_<module_code>.md#req-<module_code>-0001)
- [Code](../src/...)

**REQ_<module_code>_0002**: *Next requirement...*  
Rationale: *(optional)* ...  
Links:

- [Parent](#31-topic-or-feature-area)
- [Traceability](../docs/requirements_matrix_<module_code>.md#req-<module_code>-0002)
- [Code](../src/...)

*<!-- Continue listing requirements. Use sub-sections (3.2, 3.3, ...) for different topics as needed. -->*

### 3.2 <Next Topic>

*(Sub-section for another group of requirements.)*  
**REQ_<module_code>_0003**: ...  
Rationale: ...  
Links: [Parent](#32-next-topic) | [Traceability](...) | [Code](...)

## 4. Design Details (Non-normative)

Provide any design or implementation notes that help explain how the module will meet the requirements. Diagrams, data
models, etc., can be included here. This section does not add new requirements.

## 5. Examples

If applicable, provide example scenarios, input/output samples, or user workflows that illustrate the intended use of
the module.

## 6. Local Change Log

- 0.1.0: Initial draft created.
