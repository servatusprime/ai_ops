---
title: AI Workbook Template: <short_title>
id: wb_<topic>_<scope>
status: planned
license: Apache-2.0 # keep by default; inherit repo license unless repo policy says otherwise
version: 0.9.6
created: YYYY-MM-DD
last_updated: 2026-03-25
owner: ai_ops
ai_role: executor
model_profile: "medium"  # Reasoning level: low | medium | high | maximum. Provider-model mapping is operator-declared. See AGENTS.md §AI Model Level Reference.
authority_level: 3
execution_mode: parallel_safe
execution_topology: single_agent  # single_agent | multi_agent | hybrid
activated_lanes:  # List canonical lane names. Add Planner, Researcher, Builder, Linter, Closer as needed.
  - Coordinator
  - Executor
  - Reviewer
delegation_policy: explicit_only  # explicit_only | coordinator_judgment | open
convergence_profile: iterative_convergence_minimal
parallel_coordination_id: null  # Set only when sibling active artifacts must coordinate early
depends_on: []
affects:
  artifacts: []
  workbooks: []
shared_files: []
lock_scope: none
execution_root: .  # Required command CWD anchor; relative to repo root
path_basis: workspace_root  # Anchor for path claims: workspace_root | repo_root | relative
description: >
  Short 1-2 line description of what this workbook does.
related_refs:
  - 00_Admin/guides/authoring/guide_markdown_authoring.md
  - 00_Admin/guides/authoring/guide_yaml_authoring.md
  - 00_Admin/guides/architecture/guide_naming_conventions.md
  - 00_Admin/guides/architecture/guide_repository_structure.md
  - 00_Admin/guides/ai_operations/guide_ai_operations_stack.md
  - 00_Admin/guides/ai_operations/guide_ai_ops_vocabulary.md
  - 00_Admin/specs/spec_workbook_structure.md
  - 00_Admin/specs/spec_workbundle_dependency_tracking.md
  - 00_Admin/specs/spec_workbundle_placement_suggestion.md
  - 00_Admin/specs/spec_infrastructure_change_validation_gate.md
cost_governance:  # Work-family: MAY self-impose limits. Run-family: SHOULD populate. null = thrift judgment. See spec_cost_governance.md.
  session_token_budget: null
  workpacket_token_budget: null
  model_routing:
    planning: null
    execution: null
    review: null
  alert_threshold_pct: 80
  exceeded_action: PARK
---
<!-- markdownlint-disable MD013 MD033 -->
<!-- VALIDATION: Run markdownlint and validate_repo_rules.py before commit. -->
<!-- GUIDANCE: See 00_Admin/guides/authoring/guide_workbooks.md for patterns and anti-patterns. -->
<!-- markdownlint-disable-next-line MD025 MD041 -->
# AI Workbook Template: <short_title>

## Template Usage Notes

- NOTE: This is a template. Replace all placeholders before use.
- NOTE: Delete any sections that are not applicable, but keep required gates.
- NOTE: This template is the default for multi-phase or governance-heavy
  single-run execution work.
- NOTE: Authority fit is Level 3 baseline and Level 4-touching work when
  paired with approved work proposal rationale.
- NOTE: `execution_topology` defaults to `single_agent`. For multi-agent
  or hybrid runs, change to `multi_agent` or `hybrid`, expand `activated_lanes`,
  and fill out the full `Execution Topology Contract` block with spawn criteria,
  delegation contracts, and per-lane return shapes. See AGENTS.md §Role Reference.
- NOTE: Keep delegation guidance surface-agnostic in canonical templates. Use
  canonical lane names such as `Researcher`, `Planner`, `Executor`,
  `Reviewer`, `Linter`, or `Closer`; do not
  embed provider-specific runtime labels here.

## Upstream Governance Pointer

- Placement, approval, and handoff governance are upstream and canonical in:
  - `00_Admin/guides/ai_operations/guide_workflows.md`
  - `00_Admin/guides/ai_operations/guide_ai_operations_stack.md`
- This template captures workbook execution commitments and evidence checks.

---

## Status Checklist

- [ ] **Ph 0: Pre-execution readiness** -- model verified; workbook read; Approvals and Decisions reviewed;
  pre-flights complete; no ambiguity
- [ ] **Ph 0a: Initial Draft Selfcheck** -- for newly created workbook: required
  sections verified and markdownlint evidence recorded in Selfcheck iteration 0
- [ ] **Ph 1: <phase_name>** -- brief status note
- [ ] **Ph 2: <phase_name>** -- brief status note
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

## Execution Topology Contract

Use this section to declare the execution/delegation contract near the top of
the artifact. Frontmatter handles early routing; this block handles auditable
task shaping.

```yaml
execution_topology_contract:
  lead_lane: Coordinator
  task_brief: "<one-line mission for the lead lane>"
  spawn_criteria:
    - "<when delegation is justified>"
  do_not_delegate_when:
    - "<when the lead must retain the work>"
  required_context_pack:
    must_read:
      - "<artifact>"
    may_consult:
      - "<artifact>"
  permission_envelope:
    delegated_default: "<read-only findings support|...>"
    lead_agent: "<final integration and authority-surface writes>"
  tool_surface:
    delegated_allowed:
      - "<tool category>"
    delegated_disallowed:
      - "<tool category>"
  skill_surface:
    delegated_allowed:
      - "<skill>"
  lane_return_contracts:
    Reviewer: "<expected return shape>"
  standard_loopbacks:
    - "Reviewer -> Executor"
  escalation_loopbacks:
    - "Any ambiguity -> Requestor"
  surface_interpretation_notes:
    codex: "<explicit delegation expectation>"
    claude: "<auto-delegation constraint>"
```

Rules:

- **Single-agent** (`execution_topology: single_agent`): keep the block minimal —
  declare `lead_lane`, `task_brief`, and stop conditions only. The agent sequences
  through all `activated_lanes` in its own context.
- **Multi-agent** (`execution_topology: multi_agent`): use the full block. Declare
  `spawn_criteria`, `do_not_delegate_when`, `permission_envelope`, `tool_surface`,
  and `lane_return_contracts` for every delegated lane. Each spawned subagent
  receives its own scoped task brief and return contract.
- **Hybrid** (`execution_topology: hybrid`): primary agent handles most lanes;
  specific phases delegate to subagents. Declare which phases delegate and which stay local.
- Selective-subagent rule: delegate only when specialization meaningfully improves
  outcome or reduces token overhead — not as a default.
- See AGENTS.md §Role Reference and §Execution Topology Terms for topology definitions.

---

## Ordered Execution Queue

Use an explicit ordered queue. If reprioritized, log who requested the change and why.

<!-- Delegation-intent rule (conditional):
For delegated or specialized execution steps, replace the bare marker
`**[Agent]**` with `**[Agent: <canonical_lane> | <model_tier>]**` and add an
indented `Delegation Brief:` line immediately below the step.
Keep `<canonical_lane>` to ai_ops lane names (for example `Researcher`,
`Planner`, `Executor`, `Reviewer`, `Linter`, `Closer`) and keep
`<model_tier>` to `low`, `medium`, or `high`. Do not embed provider-specific
runtime labels in canonical templates.
See `00_Admin/guides/authoring/guide_workbooks.md` section
`Delegation Intent Markers (conditional)` for full rules. -->

### Phase 0: Cold-Start and Pre-flight (Agent -- Level 0)

- [ ] 0.0 Initial Draft Selfcheck Gate (new workbook only): verify required
      sections and record iteration 0 evidence in Selfcheck Results **[Agent]**
- [ ] 0.1 Verify model profile meets authority level declared in frontmatter **[Agent]**
- [ ] 0.2 Read this workbook fully **[Agent]**
- [ ] 0.3 Read workbundle README (or execution spine if present) **[Agent]**
- [ ] 0.4 Run Pre-Execution Readiness Gate -- confirm all checklist items pass **[Agent]**
- [ ] 0.5 **Ambiguity Stop Gate** -- if any instruction is unclear, stop and ask requestor;
  do not proceed **[Agent/Requestor]**
- [ ] 0.6 If a governing work proposal exists: update its approval status and execution note
  to reflect that execution has begun. **[Agent]**

**-> Ph 0 complete when:** All readiness checks passed; no ambiguity flagged.

### Phase 1: <phase_name> (Agent)

- [ ] 1.1 <task> **[Agent]**
- [ ] 1.2 <task> **[Agent]**

<!-- Example delegated step:
- [ ] 1.3 Map the current state **[Agent: Researcher | medium]**
      Delegation Brief: Return findings only, include file references, and do not edit files.
-->

**-> Ph 1 complete when:** <gate condition>

### Phase 2: <phase_name> (Agent)

- [ ] 2.1 <task> **[Agent]**
- [ ] 2.2 <task> **[Agent]**

**-> Ph 2 complete when:** <gate condition>

### Phase N: Completion Finalization (Agent)

- [ ] N.1 Sweep this workbook; update all checkboxes to reflect actual completion state **[Agent]**
- [ ] N.2 Update workbundle README status row for this workbook **[Agent]**
- [ ] N.3 Update execution spine artifact status entry (if spine is present) **[Agent]**
- [ ] N.4 Bump `version`, `last_updated`, and `status` in YAML frontmatter **[Agent]**
- [ ] N.5 If a governing work proposal exists: update its status, scope summary, and execution
  note to reflect completion. **[Agent]**

### Phase N+1: Selfcheck

- [ ] N+1.1 Run selfcheck loop per AGENTS.md standard (max 3 iterations) **[Agent]**
- [ ] N+1.2 Record evidence in Selfcheck Results section **[Agent]**

### Phase N+2: Crosscheck

- [ ] N+2.1 Execute `/crosscheck` on this workbook's scope **[Requestor or Agent]**
- [ ] N+2.2 Record findings in Crosscheck Stop Marker **[Agent]**
- [ ] N+2.3 Resolve any blocking findings **[Agent/Requestor]**

**Role marker convention:**

- **Agent**: step executed by AI agent
- **Agent: <canonical_lane> | <model_tier>**: optional delegated-step marker;
  add a one-line `Delegation Brief:` directly under the step
- **Operator**: step executed by human operator
- **Agent + Operator**: collaborative step requiring both

**Role-cycling verification (required at each gate/handoff):**

1. Completing role records evidence in workbook notes before handing off.
2. Receiving role confirms context received and gate condition is met.
3. No phase advances until both conditions are logged.

Phase gate expectation:

- end-of-phase validation run completed
- end-of-phase evidence logged in workbook Selfcheck

---

## Cold-Start Execution Contract

Define how a newly assigned agent should execute this workbook with no prior session context.
This contract should be readable by a `CSCC` executor (cold-start,
capacity-constrained).

- Required read order:
  1. `README.md` (workbundle root, if present)
  2. this workbook
  3. active scratchpad/review notes (if present)
- Execution boundaries:
  - in scope
  - out of scope
  - explicit stop conditions
- Evidence requirement for each completed step:
  - file path + heading/section, or
  - command + key output line(s)

### Read Strategy Contract

For CSCC executor efficiency:

- **Minimum read behavior**: Read minimum necessary sections from referenced files.
- **Batch reads**: When multiple files are needed, batch read calls when possible.
- **Write-direct for stubs**: When replacing full stub files from explicit contract,
  write directly without read-before-write overhead.
- **Reference classification**: Use `must_read` vs `may_consult` in `related_refs`
  to distinguish required-for-execution from optional background.
- **Reference depth limit**: Maximum two-level reference chain for required
  execution context (workbook -> ref1 -> ref2 max).

### Freshness Guard

Before reusing prior-session context or memory:

- Check freshness of volatile artifacts:
  - active workbook (this file)
  - workbundle/workprogram registry
  - scratchpad
  - execution spine (if present)
- If any volatile artifact changed since last read, re-read before proceeding.
- Use `work_context.updated_at` timestamp from `.ai_ops/local/work_state.yaml`
  to check active artifact freshness.

---

## Pre-Execution Readiness Gate

Must pass before any task execution:

- [ ] Scope and out-of-scope sections are explicit and current
- [ ] `execution_root` is declared and current shell CWD is validated against it
- [ ] `execution_topology`, `activated_lanes`, `delegation_policy`, and
      `convergence_profile` are declared in frontmatter
- [ ] `Execution Topology Contract` is present, current, and aligned with the
      Ordered Execution Queue
- [ ] Executor role confirmed and appropriate for task authority level
- [ ] If multi-agent scope: lane assignments and handoff conditions are explicit for each phase
- [ ] If parallel sibling artifacts exist: `parallel_coordination_id` is set or
      explicitly omitted with rationale
- [ ] Runtime import gate is declared when non-stdlib dependencies exist
- [ ] Offline dependency mode is declared when network/package index is constrained
- [ ] CLI drift check is declared when Python script command blocks are present
- [ ] Placement decision record is captured when this workbook/bundle is newly created
- [ ] Dependency impact declarations (`depends_on`, `affects`) are explicit for shared surfaces
- [ ] Target files and dependencies are reachable
- [ ] Validation commands for touched artifact types are listed
- [ ] Validation evidence format includes environment qualifier
- [ ] Ordered execution queue is populated and feasible
- [ ] Section applicability contract is complete; skipped sections include rationale
- [ ] Start checkpoint recorded in workbook notes or scratchpad
- [ ] Project run-log destination (`admin/run_logs/`) is explicit when project files are touched
- [ ] Critical-seed disposition: if workbook actualizes any `critical` priority
  seeds, explicit disposition gate is defined (`actualize_now`,
  `approve_deferral`, `split_scope`)
- [ ] If workbook is newly created in this lane, Selfcheck iteration 0 evidence
      exists (required sections + markdownlint pass)
- [ ] If any `.ai_ops/workflows/` files are in scope, export drift check is
      scheduled before first edit (run `python 00_Admin/scripts/generate_workflow_exports.py`
      after editing; pre-commit export-drift hook will block commit if skipped)
- [ ] If this workbook edits files used in the same execution (dogfood pattern),
      working-tree vs. committed authority boundary recorded in Phase 0

---

## Placement Decision Record (Required for new workbook/bundle)

Record placement-gate outputs from `/work` when creating a new workbook or
workbundle.

Template:

```yaml
placement_decision:
  requested_scope_echo: "<one-line request scope>"
  candidate_workbundle_echo: "<target path + purpose>"
  relevance_result: "<match|mismatch|uncertain>"
  placement_decision_echo: "<approved placement decision>"
```

Reference: `00_Admin/specs/spec_workbundle_placement_suggestion.md`

---

## Scope and Authority

- **Purpose:** What this workbook is meant to achieve.
- **In-scope:** Bullet list of modules/files it may touch.
- **Out-of-scope:** Things explicitly excluded.
- **Supersedes (if any):**
  - `wb_old_workbook_id_01`
  - `wb_old_workbook_id_02`

### Rewrite Lineage (Required for full rewrites)

When replacing most of an existing workbook, record lineage explicitly.

- `rewrite_mode`: `none` | `partial` | `full`
- if `full`, include:
  - prior workbook id/path,
  - replacement rationale,
  - reference-retention decision (`kept`, `redirected`, `retired`).

Template:

| Rewrite Mode | Prior Artifact | Rationale | Reference Retention |
| --- | --- | --- | --- |
| `<none\|partial\|full>` | `<path_or_id>` | `<why>` | `<kept\|redirected\|retired>` |

### Workspace-Root Artifact Classification (Conditional)

When scope touches workspace-root shared artifacts, classify them explicitly:

- `.agents/`
- `.claude/`
- `.codex/`

Rules:

- treat as shared workspace surfaces, not repo-canonical content by default;
- patch canonical generator/source surfaces first when available;
- if direct edits are required, log sync intent and downstream update owner.

### Scope Boundaries and Deferred Work (Required)

For any deferred in-scope work, provide:

- deferred item
- rationale for deferral
- owner/approver
- target follow-on artifact (workbook/runbook/registry id)

Template:

| Deferred Item | Rationale | Decision Owner | Follow-On |
| --- | --- | --- | --- |
| `<item>` | `<why deferred>` | `<owner>` | `<artifact_id_or_path>` |

---

## Inputs and Preconditions

### Required Files / Artifacts

List files that must already exist, with paths (e.g., `02_Modules/...`, `01_Resources/...`).

**Snapshot freshness note:** When referencing snapshot inputs (scratchpads,
registries, external data sources), note: "(point-in-time; refresh at milestone
boundaries)" to signal that inputs may drift during long-running execution.

### Companion Artifact Sync (Required when applicable)

When this workbook has companion artifacts in external repos or cross-repo
workbooks/scratchpads, record sync events to prevent drift:

| Companion Path | Sync Event | Last Sync | Sync Owner | Notes |
| --- | --- | --- | --- | --- |
| `<governed_repo>/scratchpad_*.md` | `sync_required` | `YYYY-MM-DD` | `<agent>` | `<sync status>` |

Sync rule: If scratchpad or workbundle state changes, update companion
artifacts within the same execution session or record deferred sync with
explicit owner.

### Machine Check Preconditions

Executor must stop and report if any of the following are not true
(e.g., file/dir existence, workbook status).

#### Execution Root Invariant (Required)

- Declare `execution_root` in front matter (for example `.` or `ai_ops`).
- Normalize command examples against `execution_root`.
- Validate CWD before running commands that rely on relative paths.
- If CWD does not match, either:
  - switch to the declared root (`Push-Location <execution_root>`), or
  - run commands with explicit working-directory handling.

#### Runtime Import Gate (Required for non-stdlib dependencies)

- List required non-stdlib modules for this workbook run.
- Run import smoke checks in the target environment before execution:
  - `python -c "import <module>; print(<module>.__name__)"`
- If any required module import fails, mark run blocked until remediated.

Template table:

| Module | Check Command | Required | Result |
| --- | --- | --- | --- |
| `<module_name>` | `python -c "import <module_name>"` | `yes/no` | `pass/fail` |

#### Offline Dependency Staging Contract (Required when constrained)

- Declare dependency mode: `online`, `offline`, or `hybrid`.
- For `offline`/`hybrid`, declare dependency source:
  - wheelhouse path, and/or
  - internal mirror URL.
- Provide reproducible install commands for constrained environments.

Template snippet:

```text
dependency_mode: <online|offline|hybrid>
dependency_source:
  wheelhouse: <path-or-none>
  mirror: <url-or-none>
install_commands:
  - python -m pip install --no-index --find-links <wheelhouse> <package>
```

#### CLI Contract Drift Gate (Required for Python command blocks)

- If this workbook contains Python script commands, run:
  - `python 00_Admin/scripts/validate_workbook_cli_contracts.py --workbook <path> --repo-root .`
- Treat unknown flags as blocking.
- Record validator output summary in `Selfcheck Results`.

### Planning Outputs (Required if no plan exists)

If there is no plan artifact for this effort, include the planning outputs here:

#### Assumptions

- <assumption>

#### Risks and Mitigations

- Risk: <risk>. Mitigation: <mitigation>.

#### Success Criteria

- <success criterion>

#### Planning Checklist

- [ ] Assumptions documented
- [ ] Risks and mitigations documented
- [ ] Success criteria defined

---

## Dependency Impact Contract (Conditional -- omit if not needed)

Declare forward and impact dependencies so closeout and crosscheck can query
scope without inference.

Required frontmatter keys:

- `depends_on` for upstream workbook dependencies
- `affects.artifacts` for impacted files/surfaces
- `affects.workbooks` for impacted workbook lanes

Optional manifest-level reverse index:

- search `affects.artifacts` across workbooks for infrastructure reverse lookup

Reference: `00_Admin/specs/spec_workbundle_dependency_tracking.md`

---

## Outputs and Target Files

Executor may modify or create:

- `<path/to/file_1>` -- create/update
- `<path/to/file_2>` -- create/update

Executor must not modify:

- `<path/to/file_3>` -- read-only/out-of-scope

### Artifact Traceability (Required for multi-file changes)

For each touched file, record:

- task ID or phase that modified it
- disposition (`created`, `updated`, `deleted`, `deprecated`, `superseded`)
- authorization level verified

Template:

| Artifact Path | Task/Phase | Disposition | Auth Level | Notes |
| --- | --- | --- | --- | --- |
| `<path>` | `<task_id>` | `updated` | L3 | `<brief context>` |
| `<path>` | `<task_id>` | `created` | L3 | `<brief context>` |

---

## Design Principles and Rules

### Naming Conventions

Describe required naming (`snake_case`, prefixes, etc.).

### Classification Rules

How to decide where entries go (e.g., REST vs WMS vs XYZ).

### Deduplication Rules

How to treat duplicate keys/URLs.

### Validation Rules

What scripts exist and what pass vs fail looks like.

---

## Capability-Gated Execution Profile (Required)

When one or more execution steps require capabilities the current executor may
lack (tooling, modality, or model limits), define a capability-gate profile.
Lanes that do not require capability gates MUST include this section with
`not_applicable` and a one-line rationale.

### Gate Definitions

For each gate, specify:

| Gate ID | Step | Type | Executor | Confirmer | Rationale |
| --- | --- | --- | --- | --- | --- |
| `G-01` | `<step description>` | `handoff` / `checkpoint` | `<role>` | `<role>` | `<why gated>` |

**Gate types:**

- `handoff`: the step is passed to a different role (requestor, external
  operator, higher-capability agent) for execution. The current executor stops
  and resumes only after the gated role reports completion.
- `checkpoint`: the step output is produced by the current executor but must be
  confirmed by another role before downstream execution continues.

**Actor-neutral roles:** `requestor`, `executor`, `approver`,
`external_operator`. Use these instead of specific tool or agent names.

Gates may be placed at any workflow step where risk warrants control -- not only
at phase boundaries.

### Model Selection Guidance

When spawning subagents or selecting model for a new session, apply:

| Task Type | Recommended Tier | Rationale |
| --- | --- | --- |
| Research / read-only exploration | low | low complexity; cost-efficient |
| Implementation / file writes | medium | balanced capability and cost |
| High-stakes / architectural decisions | high | maximum reasoning depth |

Record the model tier used in capability-gate rows when it is a constraint factor.

### CSCC Gate Snippet

When a CSCC executor reaches a gated step it cannot perform, record:

```text
GATE REACHED: <gate_id>
  Step: <step description>
  Gate type: <handoff|checkpoint>
  Current executor cannot proceed because: <specific limitation>
  Required action: <what the gated role must do>
  Resume condition: <what must be true before executor resumes>
```

---

## Profile Activation Gate (Required)

- [ ] Multi-phase, higher-risk, or higher-coordination scope confirmed
- [ ] Lite template is not sufficient for current risk/coordination profile
- [ ] Level 4 touching scope has approved work proposal when applicable
- [ ] Required validators/checklists are known before execution starts

## Section Applicability Contract (Required)

Complete this contract before execution so optional/conditional sections are
explicitly classified.

| Section ID | Applicability (`execute`/`skip`/`not_applicable`) | Rationale | Evidence / Trigger |
| --- | --- | --- | --- |
| `Placement Decision Record` | `<state>` | `<why>` | `<placement gate condition>` |
| `Companion Artifact Sync` | `<state>` | `<why>` | `<companion path or not_applicable>` |
| `Dependency Impact Contract` | `<state>` | `<why>` | `<depends_on/affects condition>` |
| `Parameter Manifest Contract` | `<state>` | `<why>` | `<manifest path or not_applicable>` |
| `Infrastructure Change Validation Gate` | `<state>` | `<why>` | `<infrastructure touch condition>` |
| `Execution Phases` | `<state>` | `<why>` | `<phase gate condition>` |
| `Execution Friction Log` | `<state>` | `<why>` | `<friction capture condition>` |
| `Deliverable Manifest` | `<state>` | `<why>` | `<deliverable condition>` |
| `Export Bundle Contract` | `<state>` | `<why>` | `<bundle condition>` |
| `Do Not Execute / Future` | `<state>` | `<why>` | `<future/deferred scope>` |
| `Compacted Context` | `<state>` | `<why>` | `<workbundle/workprogram condition>` |

---

## Validation Commands

```powershell
python 00_Admin/scripts/validate_repo_rules.py --config 00_Admin/configs/validator/validator_config.yaml
markdownlint <changed_paths>
yamllint <changed_yaml_paths>

## Governed path contract checks (when cross-repo references are in scope)
rg -n "C:/Users|C:\\\\Users|/Users/|/home/" <changed_paths>
rg -n -P "(?<!\\.\\./)ai_ops/" <governed_repo_changed_paths>
```

### Self-Review Smoke Pass Checklist

- Terminology alignment (AI-first wording, canonical terms).
- Interface clarity (structured contracts over CLI-only output).
- Recovery paths (safe-mode/self-repair where needed).
- Artifact completeness (required sections/deliverables present).
- Scope integrity (no orphaned references, no unapproved expansions).
- Reference integrity (all required paths resolve).
- Clarity pass (cold-start read: inputs, steps, outputs are explicit).

Smoke-pass command quick reference (run as applicable for touched scope):

<!-- markdownlint-disable MD013 -->

| Check | Command | Notes |
| --- | --- | --- |
| Repo validator (`VS025` coverage) | `python 00_Admin/scripts/validate_repo_rules.py --config 00_Admin/configs/validator/validator_config.yaml` | Include findings disposition in evidence notes. |
| Markdown lint | `markdownlint <changed_paths>` | Use repo config/default rules. |
| YAML lint | `yamllint <changed_yaml_paths>` | Run when YAML files are touched and lint config exists. |

---

## Verification Checklist

- [ ] Intended files changed only
- [ ] Required validations passed
- [ ] No authority violations
- [ ] Evidence recorded
- [ ] Selfcheck completed before status update
- [ ] Crosscheck readiness confirmed
- [ ] Governed-reference contract verified (ai_ops generic-only; governed repos use `../ai_ops/...`)

### Pre-Completion Checks (Required)

Apply the four **Quality Axes** defined in
`00_Admin/guides/ai_operations/guide_ai_operations_stack.md`:

#### Clarity Axis

- [ ] A cold-start reader can follow inputs, steps, and outputs without inference.
- [ ] Required files/templates are named with explicit paths.
- [ ] Ambiguous terms are clarified or linked.
- [ ] Mode differences (Direct/Governed/Standalone) are explicit where applicable.

#### Thrift Axis

- [ ] No bloat introduced (remove redundancy, tighten wording).
- [ ] Each change is purposeful; unnecessary additions identified and flagged.
- [ ] Compacted context updated (workbundle README if applicable).

#### Context Axis

- [ ] Handoff/resumption is enabled (compacted context current).
- [ ] Session notes captured if applicable.
- [ ] Scope integrity: no unapproved expansions or orphaned references.

#### Governance Axis

- [ ] Authority levels respected throughout.
- [ ] Terminology alignment: canonical terms used correctly.
- [ ] Reference integrity: all cited paths resolve.
- [ ] Artifact completeness: required sections/deliverables present.
- [ ] Workbook `status` is synchronized with checklist state.
- [ ] Companion review/status artifacts are synchronized before closeout.

#### Reviewer Integrity Check

- [ ] Review is objective and evidence-based
- [ ] Findings are actionable (each has a recommended fix)
- [ ] Severity classifications are appropriate
- [ ] No personal preferences disguised as findings

### Repo Axes Review (Required)

Record pass/fail for each touched file.

| File | Clarity | Thrift | Context | Governance | Notes |
| --- | --- | --- | --- | --- | --- |
| `<path_1>` | pending | pending | pending | pending | pending |
| `<path_2>` | pending | pending | pending | pending | pending |

### Crosscheck Readiness (Required)

- [ ] Selfcheck rows include concrete evidence (path or command output).
- [ ] Validation evidence includes environment qualifiers.
- [ ] Repo Axes Review table is complete for all touched files.
- [ ] No placeholder state remains for completed tasks.
- [ ] Workbook is ready for independent `/crosscheck` without prep.
- [ ] If dual ledgers/manifests exist, sync check evidence is recorded.

---

## Execution Notes

Track progress, blockers, and decisions during execution.

### Session YYYY-MM-DD Agent

| Task | Outcome / Notes | Decision / Blocker |
| :--- | :--- | :--- |
| Task 1 | Completed. Created file X. | None |
| Task 2 | Blocked. | Dependency missing (WB-03). |
| <Ref> | Checkpointed. | Paused for review. |

### Execution Friction Log (Optional)

Use this table to capture recurring execution friction that should be promoted
into better guidance, templates, specs, or validators.

| Step | Friction | Root Cause | Suggested Fix |
| --- | --- | --- | --- |
| `<step_id>` | `<what slowed or blocked work>` | `<why it happened>` | `<contract/template/validator improvement>` |

---

## Selfcheck Results

This section MUST be filled in before marking the workbook complete. Trace each
task and record verification. Do not leave `pending` values when workbook
`status` is changed to `completed`.

<!-- markdownlint-disable MD013 -->

<!-- NOTE: Iteration-0 evidence MUST cite a lint/validator command output (e.g., npx markdownlint-cli2 and VS024), not narrative prose. -->

Evidence schema: each entry requires **path:line** or **command + key output** -- narrative-only evidence is not acceptable.

| Iteration | Task | Status | Verification (path:line or command output) | Environment |
| --- | --- | --- | --- | --- |
| 0 | Initial Draft Selfcheck Gate | pending | `npx markdownlint-cli2 <workbook>.md → 0 errors; VS024 required sections verified` | `<env_name>` |
| 1 | Task 1: `<name>` | pending | `<path:line or command:key_output>` | `<env_name>` |
| 1 | Task 2: `<name>` | pending | `<path:line or command:key_output>` | `<env_name>` |

**Gaps identified:** (list any issues found during selfcheck, or "None")

**Smoke pass result:** PASS / FAIL (if FAIL, list issues fixed)

**Selfcheck exit condition:** clean / blocked / max_iterations

**Closeout sync check:** PASS / FAIL (if FAIL, keep `status: active`)

---

## Crosscheck Stop Marker

Do not run `/closeout` until all of the following are true:

- [ ] `/crosscheck` has been executed for this workbook scope.
- [ ] Latest crosscheck verdict is not `Blocking issues`.
- [ ] Blocking findings are either fixed or explicitly deferred with requestor approval.
- [ ] `Selfcheck Results` and companion review artifacts are synchronized.

If any item is unchecked, stop and keep workbook status non-complete.

---

## Requestor Review Gate

Before commit/push:

- [ ] Change summary provided (files touched, key edits, validation results).
- [ ] Explicit requestor approval obtained.
- [ ] Approval recorded in `00_Admin/logs/log_workbook_run.md`.

<!-- Optional: fill in when gate is cleared -->
<!-- sign_off_date: YYYY-MM-DD -->
<!-- sign_off_by: <requestor_id> -->

---

## Optional and Conditional Sections

### Operator Snapshot (Optional)

Use when operator pre-execution context is needed for post-execution
reconstruction or audit:

- **Branch**: current git branch
- **Commit**: HEAD commit hash (short)
- **Staged artifacts**: uncommitted changes summary
- **Active work context**: current active artifacts from `.ai_ops/local/work_state.yaml`
- **Environment notes**: runtime dependencies, tooling versions if relevant

### Pre-Flight Checklist (Optional)

Before creating this workbook, verify:

- [ ] This work requires 6+ file operations OR affects 3+ directories
- [ ] This is not a single atomic edit (Level 1)
- [ ] This is not a small 2-5 change batch (Level 2)
- [ ] I checked the decision tree in CONTRIBUTING.md
- [ ] All referenced artifacts exist (no placeholder files)
- [ ] Proposed edits are deltas (avoid full replacements unless required)
- [ ] Authority level identified: [0/1/2/3/4]
- [ ] If Level 4, rationale documented and approval pending
- [ ] Validation/lint steps are pre-authorized once the workbook is approved
- [ ] Logging steps are pre-authorized once the workbook is approved
- [ ] Index updates identified if new canonical docs are added (guides/specs/runbooks)
- [ ] If module naming is touched, display-name vs filesystem-path scope is explicit
- [ ] If project structure is touched, `project_metadata.yaml` contract keys are in scope

### Thrift Check (Optional)

- [ ] Reuse or extend existing guides/templates where possible
- [ ] Avoid duplicate definitions; reference canonical sources
- [ ] Policy locks live in one authority doc; other artifacts reference (not duplicate)
- [ ] Keep new sections minimal unless complexity requires more

### Authority Self-Check (Optional)

- [ ] I am operating at the correct authority level for this work
- [ ] Scope is explicitly defined (what is in, what is out)
- [ ] Preconditions are clear and verifiable
- [ ] Verification criteria are defined
- [ ] I know what "done" looks like
- [ ] (Level 3+ only) I have confirmed my understanding of: authority model, canonical
  vocabulary, decision tree

### Parameter Manifest Contract (Required for parameterized work)

When a workbook or runbook depends on business parameters (values that affect
deliverable content, not just runtime behavior), define a parameter manifest.
Workbooks with no business parameters MUST note `parameters: none` in this
section.

#### Parameter Authority Order

Resolved values follow this precedence (highest to lowest):

1. **Approved customization override** -- requestor-approved deviations from
   baseline, documented in the workbook or manifest.
2. **Explicit requestor-provided run inputs** -- values supplied at run start
   (CLI args, config file, or workbook front matter).
3. **Canonical baseline values** -- persisted in the project manifest or
   domain config as the default starting point.

**Rule:** resolved effective values MUST be written to the manifest before any
dependent execution begins. Scripts and runbooks MUST reference manifest or
explicit input parameters -- never hidden internal defaults for business-logic
values.

#### Manifest Template

```yaml
parameter_manifest:
  contract_id: '<C42 or domain contract ID>'
  contract_version: '<version>'
  parameters:
    required:
      - name: '<param_name>'
        source: '<baseline | requestor | override>'
        value: '<resolved value>'
    optional:
      - name: '<param_name>'
        source: '<baseline | requestor | override>'
        value: '<resolved value or null>'
        default_label: '<runtime | technical>'
  override_source: '<path to override document or "none">'
```

### Infrastructure Change Validation Gate (Conditional)

Run this gate when touched scope includes infrastructure surfaces:
`.ai_ops/workflows/**`, `00_Admin/scripts/**`, `00_Admin/configs/**`,
validator schemas.

Checklist:

- [ ] affected surface inventory captured
- [ ] baseline validation results captured
- [ ] post-change validation results captured
- [ ] rollback action documented
- [ ] closeout evidence recorded

Reference: `00_Admin/specs/spec_infrastructure_change_validation_gate.md`

### Export Bundle Contract (Required for deliverable bundles)

When a workbook produces a portable deliverable bundle (suitcase export),
define the bundle structure and portability requirements. Workbooks that do not
produce export bundles MUST omit this section.

#### Required Bundle Structure

```text
<bundle_id>/
  README.md          # bundle manifest (required)
  <artifacts>/       # deliverable files
```

#### Minimum Manifest Fields for README.md

```yaml
bundle_manifest:
  bundle_id: '<unique identifier>'
  created_at: '<ISO 8601 timestamp>'
  artifacts:
    - path: '<relative path within bundle>'
      type: '<file type description>'
  portability_check: '<pass | fail | not_run>'
  privacy_check: '<pass | fail | not_run>'
```

#### Portability and Privacy Guardrails

Bundles MUST satisfy the following before delivery:

1. **No project-file patching while authoring tool has the file open** --
   close the authoring tool before any automated edits to its project file
   (e.g., no `.qgz` patching while a GIS authoring tool is open; no `.xlsx` patching
   while Excel is open).
2. **Relative datasource paths** -- all internal references use relative
   paths; no absolute or user-specific paths in committed bundle artifacts.
3. **Metadata scrub** -- remove user-specific metadata (home paths, browse
   history, machine-specific config) before bundling.
4. **Domain-specific close-file edit guards** -- where applicable, document
   the specific tool and file-lock behavior (domains define their own
   concrete guards per `C40` contract).

#### Bundle Verification

- Portability check: confirm all datasource paths are relative.
- Privacy check: confirm no user-specific metadata remains.
- Completeness check: confirm all manifest artifacts exist at declared paths.

### Deliverable Manifest (Optional)

Concrete output paths for tracking deliverables:

```yaml
deliverables:
  - path: '<output_path_1>'
    type: created # created | updated | validated | deleted
    status: pending # pending | complete | deferred
  - path: '<output_path_2>'
    type: updated
    status: pending
```

### Do Not Execute / Future

- Items to defer or keep non-executable.

### Compacted Context (Required if no workbundle/workprogram)

If this workbook is not in a workbundle or workprogram, include compacted
context here for handoff continuity. If a workbundle README already contains
compacted context, omit this section from the workbook body. Treat compacted
context as persistent domain memory for this workbook and keep it current as
decisions change.

```yaml
compacted_context:
  strategic_goal: '<one sentence>'
  current_focus: '<what is in progress>'
  key_decisions:
    - '<decision 1>'
```

### Post-Execution Archival

- After execution and verification, move this workbook and its workbundle from
  `90_Sandbox/` to `99_Trash/` unless explicitly retained.
- Log any Future Work items in `00_Admin/backlog/future_work_registry.yaml`
  before moving the workbundle.
- If a commit/push is performed, add a run entry to `00_Admin/logs/log_workbook_run.md`.
- Add `work_summary.md` to the workbundle root before archiving (see guide_workbooks.md).

### Output Summary Format

Executor should respond with a summary like:

- Files modified:
  - `path/to/file_1`: added N entries, updated M entries.
  - `path/to/file_2`: created.
- Changelog:
  - updated `01_Resources/.../CHANGELOG.md` with date.
- Scripts to run next:
  - `test_rest_endpoints.ps1`

### Pre-Authorization

This workbook inherits pre-authorization and validation rules from:

- `00_Admin/guides/authoring/guide_workbooks.md`
- `00_Admin/policies/policy_git_workflow_conventions.md`

See `00_Admin/guides/authoring/guide_workbooks.md` for workbook patterns and
anti-patterns.

> **For:** AI executor **User Repo:** `<repo_name>` **Location of this file:**
> `90_Sandbox/ai_workbooks/wb_<topic>_<scope>.md`
