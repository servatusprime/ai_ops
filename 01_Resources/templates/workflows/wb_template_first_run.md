---
title: AI Workbook First-Run Template: <short_title>
id: wb_<topic>_first_run
status: planned
license: Apache-2.0
version: 0.3.2
created: YYYY-MM-DD
last_updated: 2026-03-21
owner: ai_ops
ai_role: executor
model_profile: "<model_a>:<reasoning_level> | <model_b>:<reasoning_level>"
authority_level: 3
execution_mode: sequential
execution_topology: single_agent  # single_agent | multi_agent | hybrid
activated_lanes:  # List canonical lane names. Add Planner, Researcher, Builder, Linter, Closer as needed.
  - Coordinator
  - Executor
  - Reviewer
delegation_policy: explicit_only  # explicit_only | coordinator_judgment | open
convergence_profile: iterative_convergence_standard
parallel_coordination_id: null
depends_on: []
affects:
  artifacts: []
  workbooks: []
execution_root: .
description: >
  First-run workbook template for unknown execution lanes with explicit recovery
  loops and defect capture.
related_refs:
  - 00_Admin/guides/authoring/guide_workbooks.md
  - 01_Resources/templates/workflows/wb_template_generic.md
  - 00_Admin/specs/spec_workbundle_dependency_tracking.md
  - 00_Admin/specs/spec_workbundle_placement_suggestion.md
  - 00_Admin/specs/spec_infrastructure_change_validation_gate.md
---

# AI Workbook First-Run Template: <short_title>

## Template Intention

- Use for first-run exploratory execution where behavior is not yet stable and
  recovery loops are expected.
- Authority fit: Level 3 default. Level 4 changes require approved work
  proposal and explicit gates.
- `execution_topology` defaults to `single_agent`. For multi-agent or hybrid
  runs, change to `multi_agent` or `hybrid` and declare delegation contracts
  explicitly — first-run lanes carry higher uncertainty so spawn criteria
  must be explicit. See AGENTS.md §Role Reference.

## Upstream Governance Pointer

- Placement, approval, and handoff governance remain upstream in:
  - `00_Admin/guides/ai_operations/guide_workflows.md`
  - `00_Admin/guides/ai_operations/guide_ai_operations_stack.md`
- This template captures first-run workbook profile behavior.

---

## Status Checklist

- [ ] **Ph 0: Cold-Start and Pre-flight** -- readiness gate passed, no ambiguity
- [ ] **Ph 0a: Initial Draft Selfcheck** -- for newly created workbook: required
  sections verified and markdownlint evidence recorded in Selfcheck iteration 0
- [ ] **Ph 1: <phase_name>** -- brief status note
- [ ] **Ph N: Completion Finalization** -- checkboxes swept, README updated, frontmatter bumped
- [ ] **Ph N+1: Selfcheck** -- selfcheck loop complete, evidence recorded
- [ ] **Ph N+2: Crosscheck** -- crosscheck executed, findings resolved

---

## Approvals and Decisions

**Resolve all open items in Phase 0 before proceeding to Phase 1.**

<!-- Fill in Pre-Authorized items during workbook origination or Phase 0.
     Any item not yet authorized becomes an Open Item to resolve in Phase 0. -->

### Pre-Authorized

- [ ] Workbook scope: [echo the scope in one sentence] -- authorized by requestor [date]

<!-- Add one line per pre-authorized decision or approval -->

### Open Items (resolve in Phase 0)

- [ ] [Open question or decision needing requestor input before execution begins]

<!-- If none, write: "- None -- all scope confirmed before execution" -->

### Locked Design Decisions

<!-- Record any design choices locked before execution. These should not change
     mid-execution without a new approval entry above. -->

- **[Decision label]:** [Decision and rationale]

---

## Ordered Execution Queue

### Phase 0: Cold-Start and Pre-flight (Agent -- Level 0)

- [ ] 0.0 Initial Draft Selfcheck Gate (new workbook only): verify required
      sections and record iteration 0 evidence in Selfcheck Results **[Agent]**
- [ ] 0.1 Verify model profile meets authority level declared in frontmatter **[Agent]**
- [ ] 0.2 Read this workbook fully **[Agent]**
- [ ] 0.3 Read workbundle README (or execution spine if present) **[Agent]**
- [ ] 0.4 Run Pre-Execution Readiness Gate -- confirm all checklist items pass **[Agent]**
- [ ] 0.5 **Ambiguity Stop Gate** -- if any instruction is unclear, stop and ask requestor;
  do not proceed **[Agent/Requestor]**

**-> Ph 0 complete when:** All readiness checks passed; no ambiguity flagged.

### Phase 1: <phase_name> (Agent)

- [ ] 1.1 Step 1: <command/action> -> expected output **[Agent]**
- [ ] 1.2 Step 2: <command/action> -> expected output **[Agent]**
- [ ] 1.3 Step 3: <command/action> -> expected output **[Agent]**

**-> Ph 1 complete when:** <gate condition>

### Phase N: Completion Finalization (Agent)

- [ ] N.1 Sweep this workbook; update all checkboxes to reflect actual completion state **[Agent]**
- [ ] N.2 Update workbundle README status row for this workbook **[Agent]**
- [ ] N.3 Update execution spine artifact status entry (if spine is present) **[Agent]**
- [ ] N.4 Bump `version`, `last_updated`, and `status` in YAML frontmatter **[Agent]**

### Phase N+1: Selfcheck

- [ ] N+1.1 Run selfcheck loop per AGENTS.md standard (max 3 iterations) **[Agent]**
- [ ] N+1.2 Record evidence in Selfcheck Results section **[Agent]**

### Phase N+2: Crosscheck

- [ ] N+2.1 Execute `/crosscheck` on this workbook's scope **[Requestor or Agent]**
- [ ] N+2.2 Record findings in Crosscheck Stop Marker **[Agent]**
- [ ] N+2.3 Resolve any blocking findings **[Agent/Requestor]**

---

## Cold-Start Execution Contract

1. Read this workbook and confirm first-run intent still applies.
2. Confirm unknowns/hotfix expectations and defect-capture scope.
3. Confirm pre-execution readiness gate before first command.
4. Execute steps in sequence; use recovery loop only when triggered.

---

## Pre-Execution Readiness Gate

- [ ] Inputs are available and validated
- [ ] Environment checks passed
- [ ] Dependency checks passed
- [ ] Placement decision record is captured when this workbook/bundle is newly created
- [ ] `depends_on` and `affects` fields are populated when shared surfaces are touched
- [ ] Section applicability contract is complete
- [ ] Rollback approach documented
- [ ] If workbook is newly created in this lane, Selfcheck iteration 0 evidence
      exists (required sections + markdownlint pass)

---

## Placement Decision Record (Required for new workbook/bundle)

Record:

- `requested_scope_echo`
- `candidate_workbundle_echo`
- `relevance_result`
- `placement_decision_echo`

Reference: `00_Admin/specs/spec_workbundle_placement_suggestion.md`

---

## Scope and Authority

- In-scope:
- Out-of-scope:
- Capability gates:

---

## Inputs and Preconditions

- Required inputs:
- Preconditions:
- Blockers:

---

## Dependency Impact Contract (Conditional)

When touching shared or infrastructure surfaces, declare:

- `depends_on`
- `affects.artifacts`
- `affects.workbooks`

Reference: `00_Admin/specs/spec_workbundle_dependency_tracking.md`

---

## Outputs and Target Files

Executor may modify or create:

- `<path>` -- create/update

---

## Profile Eligibility Gate (Required)

- [ ] Level 3 scope confirmed (or Level 4 with approved work proposal)
- [ ] Baseline evidence is missing or insufficient for this lane configuration
- [ ] Unknowns likely in sequencing/dependencies/acceptance checks
- [ ] Hotfix/recovery loop likely needed
- [ ] Explicit disposition target is defined at start

## First-Run Semantics

- "First-run" does not mean "first task in a session". It means first reliable
  execution attempt for this lane configuration.
- Primary objective is controlled learning with audit evidence, not maximum
  throughput.
- Unknowns discovered during run must be captured in defect log and converted
  into explicit follow-on controls.

## Section Applicability Contract (Required)

Classify conditional sections at start so first-run evidence is explicit.

| Section ID | Applicability (`execute`/`skip`/`not_applicable`) | Rationale | Evidence / Trigger |
| --- | --- | --- | --- |
| `Placement Decision Record` | `<state>` | `<why>` | `<new workbook/bundle condition>` |
| `Dependency Impact Contract` | `<state>` | `<why>` | `<shared-surface condition>` |
| `Infrastructure Change Validation Gate` | `<state>` | `<why>` | `<infrastructure touch condition>` |
| `Parameter Manifest Contract` | `<state>` | `<why>` | `<manifest path or not_applicable>` |
| `Export Bundle Contract` | `<state>` | `<why>` | `<bundle condition>` |

---

## Hotfix and Recovery Loop

- Trigger: unexpected failure or output mismatch
- Recovery actions:
  - capture failure evidence
  - apply minimal fix
  - rerun failed step only
- Exit condition: step passes or blocker escalated

## Defect Log

| Defect ID | Step | Symptom | Root Cause | Fix | Status |
| --- | --- | --- | --- | --- | --- |

## Seed Capture Log

| Seed ID | Observation | Proposed Scope | Disposition |
| --- | --- | --- | --- |

---

## Infrastructure Change Validation Gate (Conditional)

If touched scope includes `.ai_ops/workflows/**`, `00_Admin/scripts/**`,
`00_Admin/configs/**`, or validator schemas, record:

- affected surface inventory
- baseline validation results
- post-change validation results
- rollback action

Reference: `00_Admin/specs/spec_infrastructure_change_validation_gate.md`

## Parameter Manifest Contract (Conditional)

Required when business-logic parameters or requestor-provided values affect
deliverable content.

Authority order:

1. Approved customization overrides
2. Explicit requestor-provided run inputs
3. Canonical baseline values

Minimum contract fields:

- `parameter_name`
- `resolved_value`
- `source_authority`
- `resolved_at`

## Export Bundle Contract (Conditional)

If this first-run lane outputs a portable deliverable bundle, include:

- bundle structure declaration
- bundle README manifest with artifact list
- portability check result
- privacy scrub check result

If no portable bundle is produced, record `not_applicable`.

---

## Validation Commands

```powershell
python 00_Admin/scripts/validate_repo_rules.py --config 00_Admin/configs/validator/validator_config.yaml
markdownlint <changed_paths>
```

---

## Verification Checklist

- [ ] All first-run steps executed or blocked with evidence
- [ ] Recovery loops documented where used
- [ ] Defect log complete
- [ ] Seed capture log complete
- [ ] Final disposition recorded (`stabilize_to_lite`, `stabilize_to_generic`, or `escalate_blocked`)
- [ ] Selfcheck table updated with concrete evidence

---

## Execution Notes

### Operator Snapshot (Optional)

Use when operator pre-execution context is needed for post-execution reconstruction or audit:

- **Branch**: current git branch
- **Commit**: HEAD commit hash (short)
- **Staged artifacts**: uncommitted changes summary
- **Active work context**: current active artifacts from `.ai_ops/local/work_state.yaml`
- **Environment notes**: runtime dependencies, tooling versions if relevant

### Execution Friction Log

Use this table to capture recurring execution friction that should be promoted
into better guidance, templates, specs, or validators.

| Step | Friction | Root Cause | Suggested Fix |
| --- | --- | --- | --- |
| `<step_id>` | `<what slowed or blocked work>` | `<why it happened>` | `<contract/template/validator improvement>` |

---

## Selfcheck Results

| Iteration | Check | Status | Evidence | Environment |
| --- | --- | --- | --- | --- |
| 0 | Initial Draft Selfcheck Gate | pending | `<required sections + markdownlint evidence>` | `<env_name>` |
| 1 | First-run completion | pending | pending | pending |

---

## Crosscheck Stop Marker

Do not mark this workbook complete until all of the following are true:

- [ ] `/crosscheck` has been executed for this workbook scope.
- [ ] Crosscheck status is not `Blocking issues`.
- [ ] Blocking findings are either fixed or explicitly deferred with requestor approval.
- [ ] Defect log, seed log, and selfcheck rows are synchronized with latest crosscheck.

If any item is unchecked, stop and keep workbook status non-complete.

---

## Requestor Review Gate

- [ ] First-run summary, defects, and open risks provided.
- [ ] Explicit requestor approval obtained.
