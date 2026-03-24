---
title: Guide: AI Workbooks
version: 1.8.9
status: active
license: Apache-2.0
last_updated: 2026-03-24
owner: ai_ops
related:
- ./guide_markdown_authoring.md
- ../architecture/guide_repository_structure.md
- 00_Admin/specs/spec_repo_metadata_standard.md
- ../../specs/spec_workbook_structure.md
---

<!-- markdownlint-disable MD013 -->
<!-- markdownlint-disable-next-line MD025 -->
# Guide: AI Workbooks

This guide defines the expected structure and lint-safe practices for AI workbooks in `90_Sandbox/ai_workbooks/`. Use
it alongside the markdown authoring guide and the repo lint configuration.

Related specs and template:

- `00_Admin/specs/spec_workbook_structure.md` (governance)
- `00_Admin/specs/spec_repo_metadata_standard.md` (front-matter fields)
- `00_Admin/specs/spec_workbundle_dependency_tracking.md` (depends_on/affects contract)
- `00_Admin/specs/spec_workbundle_placement_suggestion.md` (placement decision echo contract)
- `00_Admin/specs/spec_infrastructure_change_validation_gate.md` (infra-touching validation gate)
- `01_Resources/templates/workflows/wb_template_generic.md` (starter template)
- `01_Resources/templates/workflows/workbundle_readme_template.md` (workbundle README)
- `01_Resources/templates/workflows/workprogram_readme_template.md` (workprogram README)
- `01_Resources/templates/workflows/workbundle_pipeline_template.md` (workbundle pipeline)
- `01_Resources/templates/workflows/workprogram_pipeline_template.md` (workprogram pipeline)
- `01_Resources/templates/workflows/runprogram_readme_template.md` (runprogram README)
- `01_Resources/templates/workflows/runbundle_readme_template.md` (runbundle README)
- `01_Resources/templates/workflows/runbundle_pipeline_template.md` (runbundle pipeline)
- `01_Resources/templates/workflows/runprogram_pipeline_template.md` (runprogram pipeline)
- `01_Resources/templates/workflows/governed_repo_bootstrap.md` (governed-repo bootstrap starter)

Note: The spec defines mandatory requirements; this guide provides practical authoring guidance. If there is a
conflict, the spec wins.

Terminology shorthand:

- `CSCC` = cold-start, capacity-constrained. Canonical definition: `guide_ai_ops_vocabulary.md` §9 Operational Vocabulary.

## Template Selection Addendum

This guide is downstream of `00_Admin/guides/ai_operations/guide_workflows.md`.
Keep governance upstream and use this guide/templates for workbook-specific
execution context.

Use this matrix for template selection:

| Template | Use When | Authority Fit |
| --- | --- | --- |
| `wb_template_first_run.md` | First reliable lane run with unstable behavior | L3; L4 with approved proposal |
| `wb_template_lite.md` | Bounded single-run lane with known behavior and low coordination overhead | Level 3 |
| `wb_template_generic.md` | Multi-phase, higher-risk, or governance-heavy execution | L3/L4-touching execution lanes |

First-run exploratory means first reliable execution for a lane
configuration, not "first task in a chat session." Its output should
stabilize into lite or generic usage, or explicitly escalate blocked
conditions.

For heavy edits/replacements of canonical guidance artifacts, maintain a
relocation map (`keep/move/remove/derive`) before removing canonical sections.

Shape checkpoint:

- If one objective starts spreading across multiple sibling workbooks or
  workbundles, stop and reassess whether the work should consolidate under one
  control bundle or escalate to a workprogram.
- Initial design crosschecks should verify this placement choice explicitly
  instead of only reviewing the local artifact in isolation.

## 1) Structure and lint rules

- Front matter first, then keep exactly one H1 that matches the `title`; use lower-level headings for sections.
- Blank lines around headings, lists, and blockquotes; use ASCII dashes (no control characters).
- Avoid file-wide markdownlint disables for new workbooks; use narrow, block-scoped disables only if required.
- Save with LF endings; set IDE EOL to `LF`.
- Run `pre-commit run --all-files` or `npx markdownlint .` before staging.
- When touching workbook files, convert CRLF to LF so linting remains consistent.
- Before drafting, scan 2-3 similar workbooks and match their depth; keep MVP scope unless a gap is proven.
- Before execution, confirm the requestor's pre-approval preference (whole workbook vs per phase) and record it in the
  workbook or workbundle README.
- For newly created workbooks, run an initial-draft selfcheck before handoff:
  required sections present, section order sane, and markdownlint pass recorded
  in `Selfcheck Results` as iteration `0`.

## 2) Required workbook sections

- **Status Checklist**: at-a-glance phase progress; checkbox items per phase; MUST appear first.
- **Approvals and Decisions**: pre-authorizations and open items; MUST appear before the execution queue.
- **Execution Topology Contract**: orchestration and delegation metadata; MUST
  appear after Approvals and Decisions and before the execution queue. For
  fully single-agent lanes, the contract may be minimal but is still required
  in new ai_ops workbook templates.
- **Ordered Execution Queue**: primary navigation aid; Phase 0 (cold-start) is always first.
- Overview (or Scope): what the workbook does and where it applies.
- Inputs/assumptions: files, datasets, or context the AI can rely on.
- Pre-Execution Readiness Gate: preflight checks before any task execution.
- Tasks/Steps: explicit actions for the executor to perform.
- Outputs/deliverables: paths and files to create or update.
- Section applicability contract: classify optional/conditional sections as
  `execute`, `skip`, or `not_applicable`, with rationale.
- Do-not-execute/Future items: clearly label non-execution or deferred work.
- Scope boundaries and deferred work: when deferring in-scope work, include
  rationale and explicit decision owner approval.
- Validation Commands: required when automated checks must be run (place after Tasks or before Outputs).
- Crosscheck stop marker: required before `/closeout`; workbook must explicitly
  block closeout until crosscheck is non-blocking and synchronized with selfcheck.
- Scoped targets: optional. If included, list repo IDs or paths that already exist in
  `AGENTS.md` workspace topology and do not redefine work/resource repo classes.
- Work summary: required for workbundle closeout (see Section 3.3).
- Parallel work guidance: include execution metadata in front matter and a short README note when relevant.

Recommended execution-oriented section order for CSCC lanes:

1. Status Checklist (Sec.2 -- required; at top)
2. Approvals and Decisions (Sec.3 -- required; before execution queue)
3. Execution Topology Contract (Sec.4 -- required; near-top)
4. Ordered Execution Queue (Sec.5 -- required; Phase 0 first)
5. Cold-Start Execution Contract
6. Pre-Execution Readiness Gate
7. Placement Decision Record
8. Scope and authority
9. Inputs and preconditions
10. Target files / Outputs
11. Design Principles / Rules
12. Validation commands
13. Verification checklist
14. Selfcheck Results
15. Crosscheck Stop Marker
16. Requestor Review Gate

## 2.0.1 Approvals and Decisions

The `## Approvals and Decisions` section is a mandatory near-top section that front-loads all
pre-authorizations and open decisions before execution begins.

**Format:**

```markdown
## Approvals and Decisions

**Resolve all open items in Phase 0 before proceeding to Phase 1.**

### Pre-Authorized

- [x] [What is already approved] -- authorized by requestor [date]

### Open Items (resolve in Phase 0)

- [ ] [Open question needing resolution] -- @requestor

### Locked Design Decisions

- **[Decision label]:** [Decision and rationale]
```

**Execution rule:** If any Open Item remains unresolved at the end of Phase 0, the workbook MUST
NOT proceed to Phase 1. The Phase 0 Ambiguity Stop Gate (task 0.5) enforces this.

**Dual benefit:**

1. Executor is hard-stopped on unresolved decisions -- no guessing mid-execution.
2. Pre-authorized items allow the executor to run without intermediate stop-approvals.

**Placement:** Between `## Status Checklist` (Sec.2) and `## Ordered Execution Queue` (Sec.4).
See templates: `01_Resources/templates/workflows/wb_template_lite.md`,
`01_Resources/templates/workflows/wb_template_generic.md`,
`01_Resources/templates/workflows/wb_template_first_run.md`.

## 2.1 Capability-Gated Execution

Use a capability-gated execution profile when one or more execution steps have
low reliability for the current executor (tooling, modality, or model
capability limits). See template section "Capability-Gated Execution Profile"
for the gate definition table.

Rules:

- Each gate MUST state who executes the gated step and who confirms acceptance.
- Approver sign-off evidence is required regardless of whether the approver is
  human or a higher-capability agent. Record the sign-off in the workbook
  execution notes or selfcheck table.
- Gates may appear at any workflow step, not only at phase boundaries.
- Domain extension rule: downstream repos consume the capability-gate profile
  via reference to `C41` and only add domain-specific gates. Do not duplicate
  the gate type definitions or actor-neutral role vocabulary.

## 2.2 Parameter Manifest Contract

When a workbook or runbook depends on business parameters, define a parameter
manifest per template section "B4. Parameter Manifest Contract."

Business-logic parameters/values are values that change deliverable content
(for example geometry, classification, stationing) rather than runtime behavior
(for example log level, thread count, retry timing).

Parameter authority rule (precedence, highest to lowest):

1. Approved customization overrides (when approved).
2. Explicit requestor-provided run inputs.
3. Canonical baseline values (persisted manifest/config fallback).

Resolved effective values MUST be written to the manifest before dependent
execution begins. Scripts and runbooks MUST reference manifest or explicit
input parameters -- never hidden internal defaults for business-logic values.

Lifecycle note: the parameter manifest may be run-scoped/transient, but
resolved effective business values MUST be preserved in execution evidence
(run manifests/log outputs).

Additional guidance:

- Workbooks and runbooks MUST state required requestor-provided inputs before
  execution begins. If inputs are missing, gate the run as blocked.
- Hardcoded defaults for business-logic parameters are prohibited. Technical
  and runtime defaults (e.g., thread count, log level) are permitted only when
  explicitly labeled as such.
- Use YAML for hierarchical parameter configs. Use CSV only for tabular
  repeated records (not primary contract authority).
- Domain boundary rule: domains map `C42` contract fields to domain-specific
  parameter names. Domains do not weaken the contract behavior (e.g., domains
  must not silently fall back to hidden defaults).

## 2.3 Export Bundle Contract

When a workbook produces a portable deliverable bundle, apply the export bundle
contract per template section "G1. Export Bundle Contract."

Portability and privacy guardrails:

- No project-file patching while the authoring tool has the file open.
- Relative datasource paths only -- no absolute or user-specific paths.
- Metadata scrub before bundling.
- Domain-specific close-file edit guards where applicable.

Keep governance wording tool-agnostic so equivalent controls apply to non-GIS
project bundles. Domain repos reference `C40` for normative rationale and only
add domain-specific implementation details.

## 2.4 Project and Naming Contract Checks

When a workbook touches project architecture or module naming:

- Treat display/product naming as mutable, but filesystem module paths as
  stable unless a migration workbook is explicitly approved.
- If project suitcase folders are in scope, include verification for
  `project_metadata.yaml` baseline keys:
  `project_id`, `storage_prefix`, `crs`, `aoi_source`,
  `data_contract_version`.
- Ensure run provenance artifacts are written to
  `<work_repo>/Projects/<project>/admin/run_logs/`.

## 2.5 Execution Root Invariant

Workbooks with command examples MUST declare `execution_root` in front matter
and normalize command blocks to that root.

Rules:

- Validate current CWD against `execution_root` before running relative-path
  commands.
- If the active CWD differs, commands MUST include explicit root handling
  (`Push-Location`/`Pop-Location` or equivalent).
- Validation evidence should record the environment and root used.

## 2.6 Runtime Import Gate

Workbooks that run scripts with non-stdlib dependencies MUST include a
preflight runtime import gate before execution steps.

Rules:

- List critical modules explicitly (for example `fitz`, `geopandas`, `yaml`).
- Run import smoke checks in the target execution environment:
  - `python -c "import <module>; print(<module>.__name__)"`
- If any required module import fails, mark the run blocked until dependency
  remediation is complete.
- Record module gate evidence in `Selfcheck Results` with environment tags.

## 2.7 Offline Dependency Staging Contract

When package-index/network access is constrained, workbooks MUST declare an
offline dependency mode before execution.

Rules:

- Declare dependency mode: `online`, `offline`, or `hybrid`.
- For `offline`/`hybrid`, declare artifact source:
  - internal mirror URL, or
  - wheelhouse path.
- Provide reproducible install commands (for example
  `pip install --no-index --find-links <wheelhouse> <package>`).
- Record dependency-source evidence in execution notes and selfcheck rows.

## 2.8 CLI Contract Drift Gate

Workbooks that include Python script command blocks SHOULD run CLI drift checks
before execution to catch stale flag names.

Rules:

- Run `python 00_Admin/scripts/validate_workbook_cli_contracts.py` against the
  active workbook.
- Treat unknown CLI flags as blocking.
- Treat unresolved script paths and Python parse failures as warnings by
  default; upgrade to blocking in strict lanes.

## 2.9 Planning Outputs

Workbooks MUST include a short Planning Outputs section: assumptions, risks, success criteria, and a planning
checklist.

For Planning Outputs vs Program Spec vs Execution Spine boundaries, use the table in
`00_Admin/guides/ai_operations/guide_workflows.md`.

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

When program artifacts exist, recommended read order is: Program Spec -> Execution Spine -> Workbook Planning Outputs.

## 2.10 CSCC Placement and Dependency Contracts

For CSCC readiness and downstream context placement, workbooks SHOULD include
these contracts when applicable:

- **Placement decision record** for new workbook/workbundle creation:
  - `requested_scope_echo`
  - `candidate_workbundle_echo`
  - `relevance_result`
  - `placement_decision_echo`
- **Dependency impact declarations** in frontmatter:
  - `depends_on`
  - `affects.artifacts`
  - `affects.workbooks`
- **Infrastructure change validation gate** whenever infra surfaces are touched
  (`.ai_ops/workflows/**`, `00_Admin/scripts/**`, `00_Admin/configs/**`,
  validator schemas).

Normative sources:

- `00_Admin/specs/spec_workbundle_placement_suggestion.md`
- `00_Admin/specs/spec_workbundle_dependency_tracking.md`
- `00_Admin/specs/spec_infrastructure_change_validation_gate.md`

## 3) Naming and file layout

- Name files `wb_<topic>_<phase>.md` (e.g., `wb_gis_data_source_discovery_combined_final.md`).
- Keep workbooks in `90_Sandbox/ai_workbooks/`; reference other repo paths explicitly.

## 3.1) Workbundles and companion artifacts

A Workbundle is a transient folder that groups a workbook with any companion artifacts required for execution.

- Folder pattern: `wb_<workbook_id>_<YYYY-MM-DD>/`.
- If a Workprogram exists, place workbundles under
  `90_Sandbox/ai_workbooks/work_program_<program_id>/work_packets/`.
- If no Workprogram exists, place workbundles under
  `90_Sandbox/ai_workbooks/wb_<workbook_id>_<YYYY-MM-DD>/`.
- The workbook file MAY live in the workbundle or be referenced from the workbundle README.
- Companion artifacts are allowed only when execution needs supporting material (notes, draft guides, comparisons,
  scratch analyses).

- For each companion artifact, declare intent at creation time:
- `lifecycle: transient` means it MUST be routed to `99_Trash/` after execution.
- `lifecycle: promote` means it MUST be mirrored to its permanent repo location during execution.
- Use the companion front matter fields defined in `00_Admin/guides/ai_operations/guide_workflows.md`.

Workbundles are only used when the workbook depends on companion artifacts; otherwise a standalone workbook file is
preferred.

Optional pipeline artifact:

- For multi-workbook or multi-phase workbundle execution, add a workbundle
  pipeline artifact instantiated from
  `01_Resources/templates/workflows/workbundle_pipeline_template.md`.
- For multi-workbundle workprogram execution, add a workprogram pipeline
  artifact instantiated from
  `01_Resources/templates/workflows/workprogram_pipeline_template.md`.
- Keep governance commitments in the execution spine when one exists; use
  pipeline artifacts as execution queues.

Frontmatter self-check (required before marking "done"):

- [ ] Required fields present (title, id, status, version, created, updated,
      owner, ai_role, authority_level, description)
- [ ] Orchestration routing fields present (`execution_topology`,
      `activated_lanes`, `delegation_policy`, `convergence_profile`; plus
      `parallel_coordination_id` when needed)
- [ ] Frontmatter matches repo conventions (status values, date formats, LF endings)

Registry tables MUST use full, copy-pasteable paths so agents can locate artifacts without guessing.

Parallel work metadata (front matter):

- `execution_mode`: `sequential`, `parallel_safe`, or `parallel_with_locks`
- `depends_on`: list of workbook ids that must complete first
- `shared_files`: list of high-contention files (or empty list)
- `lock_scope`: `none`, `file`, or `section`

Use these fields to express preference and coordination guidance, not hard enforcement unless a validator rule is
enabled.

### Execution Topology Routing Fields

Use these frontmatter fields for early execution classification before a reader
enters the full workbook body:

```yaml
execution_topology: single_agent | multi_agent | hybrid
activated_lanes:
  - Coordinator
  - Executor
  - Reviewer
delegation_policy: none | explicit_only | conditional | proactive_allowed
convergence_profile: iterative_convergence_minimal | iterative_convergence_standard | <custom>
parallel_coordination_id: <string-or-omit>
```

Rules:

- `execution_topology` declares whether the run stays in one lead agent,
  explicitly uses subagents, or mixes both patterns.
- `activated_lanes` declares only the canonical lanes actually participating in
  this run. It is not an inventory of every lane ai_ops knows about.
- `delegation_policy` describes how child work may be spawned. It is not a
  permission override.
- `convergence_profile` names the review/rework loop posture for the lane.
- `parallel_coordination_id` is conditional. Use it only when sibling active
  artifacts may run concurrently and need a shared coordination identifier.

Canonical lanes:

- `Coordinator`
- `Planner`
- `Researcher`
- `Executor`
- `Builder`
- `Reviewer`
- `Linter`
- `Closer`

Single-agent default:

- Use `Coordinator -> Executor -> Reviewer` unless the task shape clearly
  requires additional lanes.

### `role_assignments` (optional; compatibility field)

Declares per-role model tier overrides for legacy compatibility while the
canonical lane model is being promoted. When present, it allows a workbook to
specify different model tiers for the broad compatibility keys
(`coordinator`, `executor`, `validator`, `builder`). All fields are optional;
absent fields inherit `model_profile`.

```yaml
role_assignments_values: low | medium | high
role_assignments:
  coordinator: medium   # orchestrates; plans and manages handoffs
  executor: medium      # executes current workbook steps (most common field to set)
  validator: high       # evaluates outputs; use high for quality-critical crosscheck
  builder: low          # writes/edits tools and configs; usually lightweight
```

**Common pattern:** Set `executor: medium` and `validator: high` to enable
Elevated Crosscheck while `activated_lanes` expresses the richer canonical lane
path.

**model_level_map:** If your environment uses non-standard model IDs, declare a
`model_level_map` in `.ai_ops/local/config.yaml` under
`customizations.model_capabilities.model_level_map` (via `/customize`). This
binding resolves `model_profile` level references to concrete model IDs at runtime.
See `AGENTS.md §AI Model Level Reference`.

| Field | Type | Description |
| --- | --- | --- |
| `role_assignments` | optional object | Per-role compatibility overrides (`low`/`medium`/`high`) for the legacy broad-role keys |

### Delegation Intent Markers (conditional)

When a workbook or canonical template needs to express delegated execution
intent, keep the syntax surface-agnostic.

Use this pattern on delegated steps:

```markdown
- [ ] 1.2 Map current state **[Agent: Researcher | medium]**
      Delegation Brief: Return findings only, include file references, and do not edit files.
```

Rules:

- Use canonical lane names such as `Planner`, `Researcher`, `Executor`,
  `Builder`, `Reviewer`, `Linter`, and `Closer`.
- Keep model tiers to `low`, `medium`, or `high`.
- Add a one-line `Delegation Brief:` directly below the delegated step so the
  task objective, boundaries, and expected output shape travel with the step.
- Do not embed provider-specific runtime vocabulary in canonical templates or
  workbook guidance.
- Put surface-specific delegation recipes in skills, governed-repo runbooks,
  or runtime-local artifacts instead of canonical templates.

### Execution Topology Contract (required)

Place this section after `## Approvals and Decisions` and before
`## Ordered Execution Queue`.

Template:

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

- Frontmatter handles early routing. The `execution_topology_contract` handles
  auditable task shaping.
- Books and runbooks are the authoritative home for the full contract.
  Spines/pipelines should carry only the coordination summary and references to
  child execution artifacts.
- Selective-subagent rule: use subagents only for bounded sidecar tasks where
  delegation is actually efficient.
- Keep sequencing, architecture judgment, final integration, and authority-
  surface review in the lead lane.

### `model_profile` Usage

`model_profile` declares the AI model tier for the workbook or runbook.

- **In templates**: use tier-only descriptors (e.g., `"high"`,
  `"reasoning:high | standard:medium"`). Templates are provider-agnostic.
- **In active workbooks and runbooks**: provider-specific names are allowed
  (e.g., `"claude-sonnet-4.6:high"`).
- **In specs and guides**: document both levels; abstract tiers for templates,
  concrete names for artifact examples.

When loading a workbook for cold-start execution, read both `model_profile`
(tier) and `role_assignments` (per-role overrides) from frontmatter to
determine the correct execution tier for each role.

### Execution Lane Semantics (CSCC Lanes)

When a CSCC agent executes a workbook, lane labels are functional execution
lanes, not personality labels:

- `Coordinator`: sets scope, sequencing, approvals, and handoffs.
- `Planner`: converts approved scope into executable task sequencing.
- `Researcher`: gathers bounded discovery findings and evidence.
- `Executor`: performs workbook tasks and records evidence.
- `Builder`: performs tool/config/script implementation when needed.
- `Reviewer`: evaluates outputs, decisions, and governance fit.
- `Linter`: performs mechanical validation and reports evidence-backed defects.
- `Closer`: finalizes completion and closeout readiness.

Legacy compatibility:

- `Coordinator`, `Executor`, `Builder`, and `Validator` remain the compatibility
  keys for `role_assignments`.
- Profile labels (`ai-ops-planner`, `ai-ops-reviewer`, `ai-ops-closer`, etc.)
  are derivative subagent presets. They do not replace canonical lanes.

### CSCC Context Contract (Workbook Execution)

Before executing workbook tasks, confirm these context artifacts are loaded and path-valid:

- active workbook file (`wb_*.md`);
- parent workbundle `README.md` (when workbook is bundled);
- program authority artifacts when present (`execution_spine.md`, `spec_<program_id>.md`, `workbooks_registry.md`);
- active compacted context location (workbundle/program README, or workbook body when standalone);
- `.ai_ops/local/work_state.yaml` active artifact entry for the current run context.

If any required context artifact is missing, execution MUST stop until context is restored.

Before executing workbook tasks, confirm the near-top orchestration contract is
loaded in addition to the context artifacts above:

- frontmatter routing fields:
  `execution_topology`, `activated_lanes`, `delegation_policy`,
  `convergence_profile`
- `execution_topology_contract` section in the workbook body

If the workbook is in a workbundle, add a "Parallel Work Guidance" section to the workbundle README with a one-line
summary (e.g., "WB-02 and WB-04 may run in parallel; WB-03 must follow WB-01").

Compacted Context placement: the workbundle README is the canonical handoff record. If there is no workbundle or
workprogram, the workbook MUST include a compacted context section for handoff continuity. Treat compacted context
as persistent domain memory tied to the workbook; update it when decisions, scope, or constraints change.

Legacy note: older workprograms may use `wp_<program_id>_<YYYY-MM-DD>/`.
New workprograms should use `work_program_<program_id>/` per
`00_Admin/guides/ai_operations/guide_workflows.md`. Workbundles should use the
canonical `wb_` prefix.

## 3.2) Procedural Workbooks

Procedural workbooks are single-run, step-by-step sequences with preconditions, postconditions, and validation gates.
They are workbook artifacts (not runbooks) and MUST live inside a workbundle rather than the sandbox root. Reusable
procedures are runbooks; single-run procedures are workbooks.

Example:

- Procedural workbook: "Execute GIS layer QC sequence" (step-by-step checks, pre/postconditions).
- Execution workbook: "Apply approved governance updates" (bounded edits with requestor review gate).

## 3.3) Work Summary Pattern

When a workbundle is complete, add `work_summary.md` at the workbundle root with:

- Scope completed (bullet list)
- Files touched (paths)
- Validation results
- Open risks or follow-ups
- Links to log entries or decisions (if applicable)

Template:

- `01_Resources/templates/workflows/work_summary_template.md`

## 3.4) Task Count Guidance

Workbook complexity thresholds:

- **1-14 tasks**: Single workbook, flat task list. No phases needed.
- **15-24 tasks**: Consider organizing into execution phases (see template section F1).
- **25+ tasks**: Split into multiple workbooks grouped in a workbundle; use a workprogram when coordinating
  multiple workbundles.

These are guidelines, not hard rules. A workbook with 20 simple tasks may not need phases, while one with
12 complex tasks may benefit from phasing.

## 3.5) Workspace-Root Shared Artifact Classification

Treat these as workspace-root shared artifacts when touched:

- `.agents/`
- `.claude/`
- `.codex/`

Rules:

- Do not classify these as repo-canonical by default.
- Prefer patching canonical source/generator surfaces first.
- If direct workspace edits are required, record sync intent and owner in the
  active workbook.
- For governed repos, keep ai_ops governance references repo-relative
  (`../ai_ops/...`) and avoid machine-local absolute paths.

## 4) Authoring in Chat

- Emit one fenced block per file with a language hint (e.g., ```markdown).
- Include the intended path as an HTML comment on the first line inside the fence.
- Keep content lint-safe (blank lines, single H1, ASCII separators).

## 5) Minimal Scaffold

```markdown
<!-- File: 90_Sandbox/ai_workbooks/wb_example_phase_1.md -->
---
title: Example Workbook
version: 0.1.0
updated: 2025-12-05
status: active
owner: ai_ops
---

## Example Workbook

## Overview

- Purpose and scope in 2-3 bullets.

## Tasks

1. Step one.
2. Step two.

## Outputs

- List expected files/paths to create or update.

## Do Not Execute / Future

- Items to defer or keep non-executable.

```text

## 6) When adding new workbooks

- Cross-link to related workbooks and guides.
- Note required scripts or validators so execution passes without ad-hoc cleanup.
- Keep source content aligned to `.markdownlint.json`; if a rule must be disabled, explain why in the workbook.
- If the request is ambiguous, follow the Request Clarification Gate in `CONTRIBUTING.md` and
  `00_Admin/guides/ai_operations/guide_workflows.md` before drafting.
- If you add a new canonical guide/spec/runbook, update the corresponding index README in the same execution.

## 7) Required References and Deprecation

When authoring or updating a workbook, include `related_refs` in front matter for any applicable guides/specs:

| Topic                | Guide                                                                              |
| :------------------- | :--------------------------------------------------------------------------------- |
| Markdown formatting  | `00_Admin/guides/authoring/guide_markdown_authoring.md`                            |
| YAML front matter    | `00_Admin/guides/authoring/guide_yaml_authoring.md`                                |
| Naming conventions   | `00_Admin/guides/architecture/guide_naming_conventions.md`                         |
| Repository structure | `00_Admin/guides/architecture/guide_repository_structure.md`                       |
| AI Ops Stack         | `00_Admin/guides/ai_operations/guide_ai_operations_stack.md`                      |
| Vocabulary           | `00_Admin/guides/ai_operations/guide_ai_ops_vocabulary.md`                        |

If a workbook deprecates or supersedes files, it MUST:

- Mark the old file `status: deprecated` and point to the replacement.
- Archive the full content (or move to `99_Trash` if appropriate) and leave a stub at the original path.
- Update any internal references to the canonical path.

After execution and verified completion, sandbox workbooks and their associated sandbox artifacts MUST be moved from
`90_Sandbox/` to `99_Trash/` unless explicitly retained by a follow-up workbook.

Before moving a completed workbook to `99_Trash/`, log its Future Work items in
`00_Admin/backlog/future_work_registry.yaml`.

If a handoff is expected, include a `compacted_context` block in the Future Work registry entry for the next agent.

Workbook decisions and run logs:

- Workbook-level decisions are short-lived and may remain only in the workbook.
- Repo-level decisions (cross-cutting governance) MUST be promoted to `00_Admin/decisions/` or
  `00_Admin/reports/` as appropriate (for example, `00_Admin/decisions/decision_ledger.md`).

- After execution, add a concise run entry to `00_Admin/logs/log_workbook_run.md` referencing the workbook and any
  promoted decisions.

## 8) Execution-Local Enforcement Model

This guide defines authoring intent and structure. Execution mechanics are
enforced downstream in workflow and template surfaces to reduce read-hop burden.

Use this split:

- Upstream (this guide): naming, artifact boundaries, workbook qualification.
- Downstream (workflows/templates): pre-execution gates, validation sequence,
  selfcheck loops, and crosscheck readiness checks.

| Requirement | Enforcement Surface |
| --- | --- |
| workbook preflight sections | `01_Resources/templates/workflows/*.md` |
| execution gate order | `.ai_ops/workflows/work.md` + template execution blocks |
| selfcheck loop + evidence rules | templates (`K`/`J`) and workflow closeout checks |
| crosscheck readiness | template QA blocks + `.ai_ops/workflows/crosscheck.md` |
| validation commands | active workbook body (task-local) + `/closeout`/`/health` |

If a rule is repeated in both a guide and a template, keep normative contract
upstream and executable checklist downstream.

## 9) Verification Contract

Workbook authors MUST ensure every execution workbook includes:

- explicit pre-execution readiness gate,
- ordered execution queue,
- verification checklist,
- selfcheck results table,
- requestor review gate.
- initial-draft selfcheck evidence row (iteration `0`) when the workbook is new
  in the current execution lane.

Detailed command sequences, smoke-pass choreography, and retry loops belong in
the workbook template and command workflow artifacts, not repeated prose here.

When a workbook uses a draft bundle for promotion, `DRAFT_INDEX.md` MUST include
section-level delta precision:

- `key_edits`: explicit adds/edits/removals by section heading;
- `reviewed_no_change`: rationale when a file was reviewed and intentionally
  left unchanged.

## 10) Concise Workbook Authoring

Workbooks should be executable without bloat:

- prefer targeted deltas over full-file replacements;
- keep context summaries compact and decision-oriented;
- reference canonical contracts instead of duplicating long guidance blocks;
- place repeatable execution checks in templates for machine-like reuse.

## 11) Anti-Patterns

- workbook-sized execution proposed without a workbook;
- vague scope with no measurable completion evidence;
- duplicating workflow/template execution checks in guide prose;
- replacing sections without relocation proof.

## 12) Between-Workbook Transition

For multi-workbook workbundles:

- update compacted context/checkpoint status,
- confirm next workbook and shared-file locks,
- archive transient artifacts once migrated into durable logs.

## 13) Pre-Flight Checklist: Do I Need a Workbook?

Before starting work, ask:

- [ ] Are there 6+ file operations?
- [ ] Do changes affect 3+ directories?
- [ ] Is this multi-step work that could need resumption?
- [ ] Could this fail partway requiring rollback?
- [ ] Might someone ask "what is the status?"
- [ ] Did my analysis produce action items?
- [ ] Do changes span multiple artifact types?
- [ ] Are there cross-module or cross-layer changes?

If any box is checked, create a workbook.

If fewer than 6 operations in the same directory, confirm with the decision tree in CONTRIBUTING.md.

## 14) Work Proposals vs Execution Workbooks

Work Proposals are governance-only artifacts for Level 4 changes.

- Use Work Proposals to document scope, rationale, and approvals.
- Use Execution Workbooks to perform the approved edits.
- Do not execute a Work Proposal directly.

Location:

- Work Proposals live inside their Workbundle or Workprogram folder.
- Use `status: stub` while pending approval.
- Move proposals to `99_Trash/` with the rest of the workbundle artifacts after execution.

Pattern:

1. Draft Work Proposal in the workbundle/program folder.
2. Obtain human approval.
3. Draft Execution Workbook referencing the approved proposal.
4. Execute the workbook and log the run.

Level 4 changes MUST start with a Work Proposal and execution workbooks MUST reference the approved proposal. Use
`work_proposal_*.md` naming and keep proposals inside the workbundle or workprogram folder.

Approval details MUST be recorded in both the Work Proposal and the execution workbook.

Work Proposal sync rule: The governing work proposal MUST be kept in sync with execution
state. Update the proposal when approval is granted, when execution begins (record execution
start and executing agent), and when execution completes (record final status and scope
summary). A proposal that diverges from actual execution state is a governance gap.

Reference: `00_Admin/guides/ai_operations/guide_work_proposals.md`.

Terminology guardrail: use **work proposal** (not "implementation plan") for Level 4 governance changes.

### Proposal Necessity Threshold

Use this threshold before creating a work proposal:

- **Required**:
  - Level 4 scope touching canonical governance surfaces
    (`00_Admin/policies/**`, `00_Admin/specs/**`, `.ai_ops/workflows/**`,
    `00_Admin/configs/**`, `AGENTS.md`, `CONTRIBUTING.md`).
- **Usually not required**:
  - Level 3 workbook/template/guidance updates already approved inside an
    active workbook lane.
- **Not required**:
  - sandbox-only evidence artifacts and transient notes.

If uncertain, record a `proposal_seed` disposition and request requestor
confirmation before execution.

## 15) Pre-Review for New Artifact Types

If an artifact type does not have a guide/spec/template, use a pre-review step:

1. Draft the new artifact as a companion file inside the workbundle.
2. Reference any closest guides/specs/templates that exist.
3. Ask for review/approval before promotion to `00_Admin/`.
4. Promote the approved draft to its canonical location.

This avoids implicit interpretation when creating new artifact types.

## 16) Execution Models for Multi-Phase Workbundles

Single-agent execution (recommended):

- Read Phase 1 as the authoritative change definition
- Execute Phase 2 steps using Phase 1 content
- Update execution log as you go

Multi-agent handoff (when needed):

- Agent A reviews Phase 1 and documents adjustments
- Agent B executes Phase 2 using Phase 1 outputs
- Use workbundle README as the handoff checkpoint

Phase 1 is definitional and does not require separate execution unless changes are needed.

## 17) Handoff Payload

When work moves between lanes or agents, include a compacted context block per
`00_Admin/guides/ai_operations/guide_ai_operations_stack.md`. Treat compacted context as persistent domain memory
for the workbook (keep it current, not exhaustive). For Level 4 work, the handoff MUST include:

- `proposal_id`
- `target_files`
- `status_checksum`
- `validation_commands`

## 18) Workbundle Status vs Phase Status

Workbundle status reflects orchestration readiness. Phase status reflects
completion of each phase. A workbundle can be active while Phase 1 is stub and
Phase 2 is active. This is expected for multi-phase workbundles.

## 19) Verification Command Guidance

Verification commands are examples. If tooling or output differs, use equivalent checks and document the substitution.
The intent is to verify presence, correctness, and link integrity, not to enforce a specific regex pattern.

## Appendix A: Anti-Patterns

> Decision: Kept inline (WB-03b). Extraction would add a new file and cross-reference overhead; these examples
> are directly contextual to workbook authoring.

### Anti-Pattern 1: Implementation Without Workbook

Wrong:

```text

I found 35 issues in the audit. Here are PowerShell commands to fix them:

mv file1.md file2.md
mv file3.md file4.md
... (30 more commands)

```text

Right:

```

I completed the audit and identified 35 issues (report in outputs/).

Based on repository patterns, I recommend creating a workbook:

- ID: wb_repo_consistency_remediation_01
- Scope: Address 8 critical issues from audit
- Authority: File renames, moves per audit recommendations
- Inputs: audit_report_2026-01-12.md
- Preconditions: Clean working dir, backup branch

Should I draft this workbook?

```text

### Anti-Pattern 2: Skipping Verification

Wrong: "Changes applied successfully!"

Right:

```

Step 3 completed. Verification:

- Files renamed: [list with old->new names]
- Cross-references updated: [list of files updated]
- Tests passing: [output or link to results]
- Next step ready: [yes/no with blockers if any]

```text

### Anti-Pattern 3: Assuming Authority

Wrong: "I'll update all the policies to match the new standard..."

Right:

```

This change affects policies (Level 4 - governance). Requires human approval. Should I:

1. Document rationale in 90_Sandbox/
2. Create proposal for your review
3. Wait for approval before proceeding?

```text

### Anti-Pattern 4: Vague Scope

Wrong: "Fix the naming issues"

Right:

```

Scope: Standardize runbook references and update documentation

- Context: rb_is the canonical runbook prefix per guide_naming_conventions.md
- Changes: Update references in guides and documentation to use rb_ prefix
- Verification: No broken links, tests pass
- Out of scope: Renaming any existing rb_*.md files (covered by separate workbook if needed)

```text

Note: `rb_` is the canonical prefix for runbooks per `guide_naming_conventions.md`. Do not confuse this with legacy
`runbook_` naming, which is deprecated.

### Anti-Pattern 5: Over-Documenting Workbundles

Wrong:

```

Workbundle Structure:
README.md (context)
wb_workbook_phase_01.md
wb_workbook_phase_02.md
CROSSCHECK_CHECKLIST.md
MANIFEST.md
LESSONS_LEARNED.md
HANDOFF_GUIDE.md

```text

This creates documentation bloat and breaks the portable coordination unit principle.

Right:

```

Workbundle Structure:
README.md (compacted context, all guidance in one place)
wb_workbook_phase_01.md (Phase 1)
wb_workbook_phase_02.md (Phase 2)

```text

Principle: Workbundles are suitcases. Keep them lean and portable. Canonical references are fine, but avoid creating
extra companion files unless they are required for execution. If you need large replacement content, store it as a
patch file inside the workbundle (companion artifact).

Test: Could you zip this folder and hand it to someone as a runnable unit (with canonical references available)? If
yes, you have the right amount of documentation. If no, you have too much.

### Anti-Pattern 6: Inferring Architecture Over Explicit Requirements

Wrong:

```

I see that specs live in 00_Admin/specs/ as individual files with an index. I see that guides live in 00_Admin/guides/
as individual files with an index. Therefore, workbundles should follow the same pattern:

- Workbundle folder references external workbooks
- Workbooks stay in parent directory

```text

Then when told "make it a portable suitcase," ignore that explicit requirement because your inferred model says it
should be a reference container instead.

Right:

```

Explicit requirement: "portable suitcase"

This overrides any pattern inference. Move workbooks into the workbundle folder. If the pattern contradicts the
requirement, the requirement wins.

```text

Principle: Explicit requirements override pattern inference. Patterns describe common practice; requirements describe
this specific case. When they conflict, ask for clarification rather than choosing the pattern.

Test: Did someone give you an explicit instruction? If yes, that is your authority. Pattern inference is useful for
filling gaps, not for overriding explicit direction.
