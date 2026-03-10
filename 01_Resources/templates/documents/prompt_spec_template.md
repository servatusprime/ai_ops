---
title: Prompt Specification Template
module: example_module
status: stub
license: Apache-2.0
prompt_id: example_prompt
last_updated: YYYY-MM-DD
---

<!-- markdownlint-disable MD012 MD025 -->

# Prompt Specification Template

Use this template to author prompt specifications in Markdown. Keep documents AI-friendly, traceable, and aligned to
module specs.

## AI-First Guidance

- Prefer explicit inputs/outputs over narrative.
- Keep steps short and ordered.
- For CSCC execution, require explicit read order and stop conditions.

---

## 1. Front Matter

Include YAML front matter at the top of every prompt spec:

```yaml
---
title: <Prompt Title>
module: <module_code>          # lower_snake_case, matches folder name
status: planned                # planned | stub | active | deprecated
prompt_id: <prompt_id>         # lower_snake_case identifier
related_spec: <path_to_spec>   # e.g. 02_Modules/gis_workflow/docs/specs/spec_gis_workflow.md
related_plan: <path_to_plan_or_prompt_if_any>
last_updated: YYYY-MM-DD
---
```

---

## 2. Document Structure

```markdown
# <Prompt Title>

## Purpose
What the prompt is meant to achieve (non-normative).

## Inputs
List inputs, schemas, roles, and assumptions.

## Outputs
Describe expected outputs, formats, and quality bars.

## Steps / Workflow
Ordered steps the AI should follow. Reference spec REQs where applicable (e.g., REQ_example_module_0001).

## Guardrails
Constraints, safety checks, and prohibitions.

## Examples (optional)
Sample invocations or dialogues.

## TODOs (optional)
Open items to flesh out later.
```

### Recommended addendum for CSCC prompts

When targeting cold-start, capacity-constrained execution, add:

```markdown
## Read Order (Required)
1. <file_1>
2. <file_2>
3. <file_3>

## Stop Conditions (Required)
- Stop if required file is missing.
- Stop if scope conflict is found.
- Stop if validation command fails twice.

## Evidence Contract (Required)
- For each task: cite file path + section, or command + key output line.

## Required Inputs (Required for parameterized prompts)
- List all requestor-provided inputs needed before execution.
- Reference the parameter manifest contract (`C42`) when business parameters
  are involved. Scripts must not use hidden defaults for business-logic values.
```

---

## 3. Requirement IDs (when referencing specs)

- Use spec requirement IDs in the format `REQ_<module_code>_<numeric_id>`.
- Example: `REQ_example_module_0001`
- `<module_code>` = lower_snake_case module name.
- `<numeric_id>` = zero-padded integer (0001, 0002, ...).

---

## 4. Status Values

- `planned`: referenced but not yet started.
- `stub`: placeholder file exists with minimal content.
- `active`: implemented and reasonably complete.
- `deprecated`: being phased out; avoid new use.

---

## 5. Authoring Checklist

- [ ] Front matter present with canonical fields.
- [ ] Single H1 immediately after front matter.
- [ ] Inputs/Outputs/Workflow/Guardrails clearly described.
- [ ] References to spec REQs use `REQ_<module_code>_<numeric_id>`.
- [ ] Status reflects document maturity (planned/stub/active/deprecated).
