---
spec_id: <module_code_or_contract_id>
id: spec_<topic>
module: <module_or_admin>
title: <Spec Title>
status: stub
license: Apache-2.0
version: 0.1.0
created: YYYY-MM-DD
updated: YYYY-MM-DD
owner: ai_ops
ai_generated: true
spec_archetype: module_spec  # module_spec | governance_spec | output_contract_spec | runtime_design_spec
related: []
---

<!-- markdownlint-disable MD025 MD051 -->

# <Spec Title>

## AI-First Guidance

- Keep sections concise and skimmable (bullets > paragraphs).
- Select the spec archetype before writing.
- Prefer explicit rules, schemas, and requirements over narrative.
- Use `REQ-*` IDs for `module_spec` artifacts and only for other archetypes when they add traceability value.
- Keep purpose, scope, and usage near the top so cold-start agents can orient quickly.

## Archetype Selection

| Archetype | Use When | Required Shape |
| --- | --- | --- |
| `module_spec` | Module, feature, data model, API, or implementation surface | Purpose/scope, terminology, `REQ-*` requirements, traceability, design notes, examples, change log |
| `governance_spec` | Repository rules, workflow structure, authority behavior, lifecycle rules, or artifact structure | Purpose, scope, rules, enforcement or validation status, references, change log |
| `output_contract_spec` | Agent output schema, emission rules, consumption rules, or structured governance output | Quick reference, purpose, scope, schema, emission or consumption rules, examples, change log |
| `runtime_design_spec` | Target-state runtime behavior that is not fully enforceable yet | Purpose, current fallback, target-state contract, activation conditions, roadmap, change log |

Delete archetype sections that do not apply before publishing.

## Common Minimum

All specs MUST include:

1. YAML frontmatter.
2. Visible title.
3. Purpose or quick reference.
4. Scope or applicability.
5. Normative content using MUST/SHOULD/MAY where behavior is required.
6. Related references or links where relevant.
7. Change log.

## Module Spec Pattern

### 1. Purpose and Scope

Briefly describe the module or feature and the scope of this specification. Include context, goals, and any boundaries.

### 2. Terminology and References

- Define key terms or acronyms here, or reference the global glossary. Example: **NOI** - Net Operating Income (see
  Glossary).
- List related documents or specs: `[GIS Module Spec](spec_gis.md)`.

### 3. Requirements

#### 3.1 <Topic or Feature Area>

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

#### 3.2 <Next Topic>

*(Sub-section for another group of requirements.)*  
**REQ_<module_code>_0003**: ...  
Rationale: ...  
Links: [Parent](#32-next-topic) | [Traceability](...) | [Code](...)

### 4. Design Details (Non-normative)

Provide any design or implementation notes that help explain how the module will meet the requirements. Diagrams, data
models, etc., can be included here. This section does not add new requirements.

### 5. Examples

If applicable, provide example scenarios, input/output samples, or user workflows that illustrate the intended use of
the module.

### 6. Local Change Log

- 0.1.0: Initial draft created.

## Governance Spec Pattern

### Governance Purpose

State the governance problem this spec solves.

### Governance Scope

State where the rules apply and what is out of scope.

### Rules or Criteria

Use MUST/SHOULD/MAY for normative rules.

### Enforcement or Validation Status

State whether rules are enforced by validator, template, crosscheck, manual review, or not yet enforced.

### Related References

List canonical upstream and downstream references.

### Governance Change Log

- 0.1.0: Initial draft created.

## Output Contract Spec Pattern

### Quick Reference

- **What:** <one-line description>
- **Field or output:** `<field_name>` if applicable
- **When:** <emission or consumption condition>

### Output Contract Purpose

State why the output contract exists.

### Output Contract Scope

State producers, consumers, and non-goals.

### Schema

```yaml
field_name:
  key: value
```

### Emission or Consumption Rules

Use MUST/SHOULD/MAY for when agents produce or consume this contract.

### Output Contract Examples

Provide one minimal valid example and one realistic example.

### Output Contract Change Log

- 0.1.0: Initial draft created.

## Runtime Design Spec Pattern

### Runtime Design Purpose

State the runtime behavior being preserved.

### Current Fallback Policy

State what agents MUST do until runtime support exists.

### Target-State Contract

Describe the intended machine-readable contract.

### Trigger or Activation Conditions

State what makes the target behavior active.

### Implementation Roadmap

List the minimum steps to activate or enforce the design.

### Runtime Design Change Log

- 0.1.0: Initial draft created.
