---
title: Guide: Runbooks
version: 1.0.6
status: active
license: Apache-2.0
last_updated: 2026-03-14
owner: ai_ops
related:
- ./guide_markdown_authoring.md
- ../ai_operations/guide_workflows.md
- ../ai_operations/guide_ai_ops_vocabulary.md
- 00_Admin/specs/spec_repo_metadata_standard.md
---

# Guide: Runbooks

This guide defines how to author runbooks in <repo_name>. Runbooks are execution workflows: reusable, parameterized, and
safe to run repeatedly.

Enforceable requirements live in `00_Admin/specs/spec_runbook_structure.md`. This guide is advisory; if there is a
conflict, the spec wins.

## 1) Definition and intent

A **Runbook** is a reusable execution workflow. It describes how to execute a task without freezing assumptions or
locking one-off decisions.

Runbooks MUST:

- Be reusable and parameterized.
- Reference pipelines and contracts by ID or path where applicable.
- State preconditions, inputs, and expected outputs.
- State postconditions or expected end state.

Runbooks MUST NOT:

- Freeze assumptions or scope for a single run.
- Encode one-off decisions that should live in a workbook.

## 2) Naming and location

- Prefix: `rb_`
- Location: `00_Admin/runbooks/` (repo-level) or module-specific runbooks under `02_Modules/<module>/docs/runbooks/` if
  used.
- Use lower_snake_case names (e.g., `rb_repo_health_review.md`).
- Terminology note: use `runprogram` in prose, but keep folder paths as `run_program_<program_id>/` until a dedicated
  naming-refactor workbook says otherwise.

## 2.1) Runbundles (Runbook Grouping)

Runbundles group related runbooks the way Workbundles group workbooks, but they are distinct artifact types.

- Folder naming: `rnb_<bundle_name>/`
- Location (when a Runprogram exists): `run_program_<program_id>/run_bundles/rnb_<bundle_name>/`
- Location (when no Runprogram exists): `00_Admin/runbooks/rnb_<bundle_name>/` or
  `02_Modules/<module>/docs/runbooks/rnb_<bundle_name>/`
- Required contents: `README.md` (bundle purpose and inventory) + runbooks for that bundle

Runbundles are optional and should be used when runbooks are frequently executed together.

Bundle README minimums:

- Purpose (why the bundle exists)
- Included runbooks (full paths if outside the bundle folder)
- Parallel Work Guidance (one-line summary of runbooks that can run in parallel)

Template starters:

- `01_Resources/templates/workflows/rb_template_generic.md`
- `01_Resources/templates/workflows/runbundle_readme_template.md`
- `01_Resources/templates/workflows/runbundle_pipeline_template.md`

Recommended internal layout for scalable runbundles:

```text
rnb_<bundle_name>/
  README.md
  rnb_<bundle_name>_<nn>.md          # optional local pipeline artifact
  runbooks/
    rb_<step_00>.md
    rb_<step_01>.md
    rb_<step_02>.md
```

Queue rule:

- Runbundle pipelines SHOULD reference local runbooks using `runbooks/rb_<step>.md`.
- Parent-relative queue entries (`../rb_*.md`) are legacy and should be normalized when touching a bundle.

## 2.2) Runprogram Pipeline (Optional)

Runprogram pipelines are optional execution-queue artifacts for sequencing multiple runbundles in one runprogram.

- Suggested artifact location: `run_program_<program_id>/`
- Suggested file pattern: `runprogram_pipeline_<nn>.md`
- Keep governance commitments in the runprogram execution spine when one exists; use pipeline artifacts for execution
  queueing and gate visibility.
- Keep runprogram root focused on governance/program artifacts; runbook execution files should remain inside each
  `run_bundles/rnb_*` folder.

Template starters:

- `01_Resources/templates/workflows/runprogram_readme_template.md`
- `01_Resources/templates/workflows/runprogram_pipeline_template.md`

## 2.3) Run-Family Development and Promotion Workflow

Use this lane for `rb_`, `rnb_`, and `run_program_*` artifacts:

1. **Develop as candidate artifacts** in a bounded execution lane:
   - workbundle-local runbooks/runbundle when behavior is still stabilizing.
1. **Validate in execution**:
   - pass at least one end-to-end run with explicit evidence.
   - capture blockers and deviations in workbook/tasklist evidence.
1. **Classify promotion target**:
   - reusable in current repo -> promote to canonical runbook paths.
   - one-off endpoint flow -> keep local or delete at closeout.
1. **Promote to canonical (same repo)**:
   - move runbooks to `00_Admin/runbooks/` or `02_Modules/<module>/docs/runbooks/`.
   - keep runbundle structure where repeated grouped execution is expected.
   - update runbook indexes/registries and cross-references.
1. **Promote to target repos (governed rollout)**:
   - canonical operational run artifacts live in the target repo, not in ai_ops.
   - ai_ops keeps governance references, templates, and policy/runbook standards.
   - target repo run artifacts MUST be path-correct for the target repo root.

Promotion should be driven by reuse and stability evidence, not by artifact age.

## 3) Required sections

Include these sections (headings may vary, but content is required):

1. Purpose
2. Scope and authority
3. Inputs
4. Preconditions
5. Planning outputs
6. Steps (execution sequence)
7. Validation commands
8. Outputs
9. Postconditions
10. Validation or checks (tests, validators, or evidence required)
11. Verification checklist

Runbooks MUST include a short Planning Outputs section: assumptions, risks, success criteria, and a planning checklist.

Planning Outputs placement (required):

```markdown
## Planning Outputs

### Assumptions

- <assumption>

### Risks & Mitigations

- Risk: <risk>. Mitigation: <mitigation>.

### Success Criteria

- <success criterion>

### Planning Checklist

- [ ] Assumptions documented
- [ ] Risks and mitigations documented
- [ ] Success criteria defined
```

When program artifacts exist, recommended read order is: Program Spec -> Execution Spine -> Runbook Planning Outputs.

Verification checklist failure handling:

- If the checklist fails, stop execution.
- Record blockers in the runbundle README or runprogram execution spine (if applicable).
- Fix blockers before reporting completion.

Validation Commands placement (required):

`````markdown
## Validation Commands

````markdown
## Validation Commands

```powershell
Example - path checks
Test-Path "00_Admin/runbooks/rb_example.md"

Example - repo validator
python 00_Admin/scripts/validate_repo_rules.py --config 00_Admin/configs/validator/validator_config.yaml
```
````
`````

## 4) Authoring rules

- Follow the markdown authoring rules and linting in `guide_markdown_authoring.md`.
- Keep line length to 120 chars for prose.
- Use `1.` for all ordered list items.
- Keep assumptions and commitments explicit and separate.
- If part of a program, include links to the spec, execution spine, and registry.
- If a handoff is expected, include a compacted context block per
  `00_Admin/guides/ai_operations/guide_ai_operations_stack.md`.
- Before drafting, scan 2-3 similar runbooks and match their depth; keep MVP scope unless a gap is proven.

Parallel work metadata (front matter):

- `execution_mode`: `sequential`, `parallel_safe`, or `parallel_with_locks`
- `depends_on`: list of runbook ids that must complete first
- `shared_files`: list of high-contention files (or empty list)
- `lock_scope`: `none`, `file`, or `section`

Use these fields to express preference and coordination guidance, not hard enforcement unless a validator rule is
enabled.

`model_profile` usage:

- In **runbook templates**: use tier-only descriptors (e.g., `"high"`,
  `"reasoning:high | standard:medium"`). Templates are provider-agnostic.
- In **active runbooks**: provider-specific names are allowed
  (e.g., `"claude-sonnet-4.6:high"`).
- See `00_Admin/specs/spec_runbook_structure.md` §7 for the normative rule.

## 5) Minimal scaffold (lint-safe)

````markdown
## <!-- File: 00_Admin/runbooks/rb_example.md -->

title: Runbook: Example Task version: 0.1.0 status: active last_updated: 2026-01-15 owner: ai_ops execution_mode:
sequential model_profile: "<model_a>:<reasoning_level> | <model_b>:<reasoning_level>" depends_on: [] shared_files: []
lock_scope: none

---

H1: Runbook: Example Task

## Purpose

- One or two bullets that describe the goal.

## Scope and Authority

- In-scope:
- Out-of-scope:
- Approval gates:

## Inputs

- Files, systems, or parameters required to run.

## Preconditions

- What must be true before execution begins.

## Steps

1. First execution step.
1. Second execution step.

## Outputs

- Files or systems that will be updated or created.

## Postconditions

- What must be true after successful execution.

## Validation Commands

```powershell
Example - path checks
Test-Path "00_Admin/runbooks/rb_example.md"

Example - repo validator
python 00_Admin/scripts/validate_repo_rules.py --config 00_Admin/configs/validator/validator_config.yaml
```
````

## Validation

- Checks or validators to confirm success.

## Verification Checklist

- [ ] Postconditions met
- [ ] Outputs created/updated
- [ ] Validation commands executed
- [ ] Steps executed in order
- [ ] Preconditions satisfied

## 6) Workbundle-Local Runbooks (Candidate Lifecycle)

Workbundles and operational workbundles may include runbooks in a local `runbooks/` subfolder. These are **candidates**,
not canonical runbooks.

### Lifecycle states

| State     | Location                                                       | Meaning                                       |
| --------- | -------------------------------------------------------------- | --------------------------------------------- |
| Candidate | `<workbundle>/runbooks/rb_*.md`                                | Draft runbook, not validated end-to-end.      |
| Canonical | `00_Admin/runbooks/rb_*.md` or `02_Modules/<m>/docs/runbooks/` | Validated, reusable.                          |
| Deleted   | (removed)                                                      | Runbook was superseded or deemed unnecessary. |

### Promotion rules

1. Candidate runbooks use `status: stub` and `lifecycle: candidate` until validated.
2. After first successful end-to-end execution, update to `status: active` and `lifecycle: canonical`.
3. If the runbook is reusable across workbundles, promote to canonical location.
4. If the runbook is workbundle-specific and unlikely to be reused, delete after workbundle closeout.

Note: Use canonical status values (`planned`, `stub`, `active`, `deprecated`) and express lifecycle state via the
`lifecycle` front-matter field.

### Tagging

Use front-matter field `lifecycle: candidate | canonical | deprecated` to distinguish.

Workbundle-local runbooks SHOULD include a `runbook_script_decision_matrix.md` or similar artifact in the workbundle
that tracks keep/refactor/delete decisions after first run.

### Request Traceability (Operational Workbundles)

For workbundle-local candidate runbooks, include a short request traceability note in the workbundle workbook or
tasklist:

- request source (who/what asked for the run)
- requested outputs
- approval record for any non-requested "helpful" artifacts

## 7) Runbook-Script Dependencies

Runbooks often depend on scripts. Declare and manage these dependencies explicitly.

### Front-matter declaration

```yaml
script_deps:
  - path: scripts/01_init_project.py
    required: true
  - path: scripts/02_validate_inputs.py
    required: true
used_by_runbooks:
  - rb_example.md
```

### Step-level references

When a runbook step invokes a script, reference it explicitly:

```markdown
## Steps

1. Run initialization: `python scripts/01_init_project.py --config config.yaml`
2. Validate inputs: `python scripts/02_validate_inputs.py`
```

### Template instantiation pattern

When creating a new script from templates, make the copy step explicit in the runbook so agents use a consistent
scaffold:

```powershell
Example: generic Python script
Copy-Item "01_Resources/templates/scripts/script_template_python.py" `
  "02_Modules/<module>/src/<script_name>.py"

Example: desktop GIS script (domain overlay template in target governed repo)
Copy-Item "<work_repo>/01_Resources/templates/scripts/script_template_gis_desktop.py" `
  "<work_repo>/02_Modules/<module>/src/<script_name>.py"
```

Then update:

1. Module docstring and argument contract.
2. Input/output paths and validation checks.
3. Script entry in the runbook `script_deps` block.

### Runbook vs Script Decision

Use this matrix to decide when logic belongs in a runbook vs a script:

| Condition                            | Prefer                              | Rationale                      |
| ------------------------------------ | ----------------------------------- | ------------------------------ |
| Deterministic and fully automatable  | Script                              | Maximize repeatability.        |
| Human judgment or manual QA required | Runbook                             | Steps and gates stay explicit. |
| High churn or early exploration      | Workbook or checklist               | Avoid lock-in.                 |
| Logic reused across contexts         | Parameterized script + thin runbook | Max reuse.                     |
| One-off endpoint flow                | Workbundle-local runbook            | No promotion needed.           |

For complex workbundles with many runbooks and scripts, maintain a `runbook_script_decision_matrix.md` to track
keep/refactor/delete decisions.

### Validation hook/path expectations

For runbook-script linkage to be machine-checkable:

1. Declare script paths in `script_deps`.
2. Reference the same script paths in Steps (no hidden script calls).
3. Run validator + markdownlint and capture evidence in workbook/selfcheck.

Validation path:

```powershell
python 00_Admin/scripts/validate_repo_rules.py --config 00_Admin/configs/validator/validator_config.yaml
markdownlint <changed_paths>
```

## 8) Pre-Authorization and Validation

Once a runbook is approved for execution, the executing agent is pre-authorized to run required validation and linting
steps without pausing for additional approvals.

Required before reporting completion:

- Run the repo validator:
  `python 00_Admin/scripts/validate_repo_rules.py --config 00_Admin/configs/validator/validator_config.yaml`

- Run `markdownlint` on changed paths.
- If canonical files or directories were added/removed, update structure maps:
  `00_Admin/scripts/generate_repo_structure.ps1`

Fix all validator or linting errors before reporting "done".
