---
title: "<Workbook title>"
id: wb_<topic>_<scope>
status: planned
license: Apache-2.0
version: 0.1.0
created: YYYY-MM-DD
last_updated: YYYY-MM-DD
owner: ai_ops
ai_role: executor
model_profile: "medium"  # low | medium | high | maximum; see AGENTS.md "AI Model Level Reference"
authority_level: 3
execution_mode: parallel_safe
execution_topology: single_agent  # change only for material delegation (trigger table)
activated_lanes: [Coordinator, Executor, Reviewer]
delegation_policy: coordinator_judgment  # none | explicit_only | coordinator_judgment | conditional | proactive_allowed
convergence_profile: iterative_convergence_minimal  # tier-1 cap 1 loop; iterative_convergence_standard: up to 3 (crosscheck.md "Loop Control")
parallel_coordination_id: null
depends_on: []  # ids of workbooks that must complete first
affects: {artifacts: [], workbooks: []}
execution_root: .
path_basis: repo_root
description: >-
  <One or two lines: what this workbook changes and where. Read by /work_status and reviewers.>
related_refs:
  - 00_Admin/specs/spec_workbook_structure.md
cost_governance:  # review budget per crosscheck.md "Loop Control"; null = thrift judgment
  session_token_budget: null
  model_routing: {review: null}
  exceeded_action: PARK
---
<!-- markdownlint-disable MD013 MD025 MD041 -->
# <Workbook title>

<!-- Fill every <...> cue with your own text; the cue names what goes there and which step reads it, so nothing of it stays. Required headings: 00_Admin/specs/spec_workbook_structure.md section 4. Match the depth of the surrounding template and keep filled sections short: per-resume blocks, not narration; evidence as a path to a receipt, not pasted output. -->

## Status Checklist

- [ ] **Ph 0: Cold start and pre-flight**
- [ ] **Ph 1: <phase name>** -- <one-line outcome; VS035 reads these boxes>
- [ ] **Completion:** selfcheck, crosscheck, requestor review

## Approvals and Decisions

- [ ] **Execution authorized:** <status only; the verbatim requestor quote, date and scope go in the Requestor Review Gate; approving this workbook's creation does not authorize execution>
- [ ] **Open item:** <question, owner; Phase 0 stops while one is open; write none when there is no open item>
- [ ] **Reserved gate (optional):** <decision a later phase needs from the requestor, the phase, and what it unlocks; omit this row when no later decision exists; this is not an open item and does not stop Phase 0>
- **Locked decision:** <decision and reason>

## Trigger Table

Evaluate each row when drafting this workbook and again in Phase 0 (task 0.4). When a condition is true, read the named block and record the result where the row says; skip the rest. Paths in this table are repo-root-relative and must be used exactly as written.

| Condition (observable) | Read | Record in |
| --- | --- | --- |
| Delegation is write-capable, shared-state, authority-sensitive, long-running or independently resumable | `00_Admin/guides/authoring/guide_workbooks.md` 3.1 "Execution Topology Contract (material delegation only)" | an `## Execution Topology Contract` section; set `execution_topology` |
| A new workbook or workbundle is being placed | `00_Admin/specs/spec_work_mode.md` section 4 | the four echo fields under Scope and Authority |
| `depends_on` or `affects` is not empty | `00_Admin/guides/authoring/guide_workbooks.md` 2.10 | Scope and Authority |
| A required tool, model capability or runtime may be missing | `00_Admin/guides/authoring/guide_workbooks.md` 2.1 | Readiness Gate |
| Inputs are set per run (parameters) | `00_Admin/guides/authoring/guide_workbooks.md` 2.2 | Scope and Authority |
| Output is a deliverable bundle for someone else | `00_Admin/guides/authoring/guide_workbooks.md` 2.3 | Outputs and Target Files |
| Project naming or folder conventions are in scope | `00_Admin/guides/authoring/guide_workbooks.md` 2.4 | Verification Checklist |
| Commands depend on a working directory, non-stdlib imports, offline installs or a Python CLI | `00_Admin/guides/authoring/guide_workbooks.md` 2.5 to 2.8 | Readiness Gate |
| Derived files are regenerated, or a refactor must keep behavior | `00_Admin/guides/authoring/guide_workbooks.md` 2.11 and 2.12 | Verification Checklist |
| No plan exists yet, or a new capability may already exist | `00_Admin/guides/authoring/guide_workbooks.md` 2.9 and 2.13 | a `## Planning Outputs` section (2.9); Scope and Authority (2.13) |
| `.ai_ops/workflows/**`, `00_Admin/scripts/**` or `00_Admin/configs/**` is touched | `00_Admin/specs/spec_infrastructure_change_validation_gate.md` | Readiness Gate |
| Cross-repo references are in scope | `00_Admin/specs/spec_work_mode.md` section 5 (VS028) | Validation Commands |
| First reliable run of a lane configuration (no earlier run of this kind of lane setup) | `00_Admin/guides/authoring/guide_workbooks.md` 2.14 to 2.17 | Execution Notes |
| Parallel work writes shared files | `00_Admin/guides/ai_operations/guide_parallel_execution.md` | frontmatter: add `shared_files` and `lock_scope` |
| An operator profile is activated | `.ai_ops/workflows/profiles.md` and `AGENTS.md` "Rider Archetypes" | Approvals and Decisions |
| No workbundle or workprogram README holds the context | `00_Admin/specs/spec_workbook_structure.md` section 4 | a `## Compacted Context` section |
| An iterative quality loop runs | `.ai_ops/workflows/crosscheck.md` "Loop Control" and `01_Resources/templates/workflows/quality_loop_convergence_template.md` | Crosscheck Stop Marker |

## Ordered Execution Queue

### Phase 0: Cold start and pre-flight (Agent -- Level 0)

- [ ] 0.1 Record the session model ID; stop if it is below `model_profile`
- [ ] 0.2 Read this workbook, then the bundle README or spine if one exists
- [ ] 0.3 Run the section check (`spec_workbook_structure.md` section 4) and the Readiness Gate
- [ ] 0.4 Evaluate the Trigger Table and read only the blocks of rows that fire; stop while an open item or a fired row is unresolved (ambiguity stop gate)

### Phase 1: <phase name> (Agent -- Level <n>)

- [ ] 1.1 <verb, target path, expected result; the Verification Checklist checks it> **[Agent]**

**-> Ph 1 complete when:** <observable condition>

### Completion

- [ ] C.1 Sweep the boxes; leave `status` unchanged while any box below is open (VS035)
- [ ] C.2 Selfcheck loop per `AGENTS.md` (max 3), then crosscheck per `crosscheck.md` "Loop Control"; record both below

## Cold-Start Execution Contract

1. Authorization first: <the approval this run needs and where it is recorded>.
2. Read order: <files, in order; stop reading when the task is clear>.
3. Write scope: <paths this workbook may change>; anything else is a stop.
4. Stop conditions: <conditions that return the run to the requestor>. Evidence is a path and line, or a command with its key output; record each resume as one Execution Notes block.

## Pre-Execution Readiness Gate

- [ ] Authorization (quote, date) and tree state (branch, HEAD, `git status --short`) recorded
- [ ] Validation commands identified (below) and fired trigger rows listed with their results
- [ ] Rollback or safe stop: <how to undo the change set>

## Scope and Authority

- **In scope:** <what changes>
- **Out of scope and deferred:** <item, reason, owner approval>
- **Authority:** Level <n>, <reason>; pre-write path guard per `AGENTS.md`
- **Inputs:** <file, data or prior result the run relies on; read-only or editable>

## Outputs and Target Files

| Path | Change | Proven by |
| --- | --- | --- |
| <path> | <create, edit or move> | <validator or check> |

## Validation Commands

- `<command, run from execution_root>`

## Verification Checklist

- [ ] Every output above exists and its check passes
- [ ] No path outside Outputs and Target Files changed (`git status --short`)
- [ ] <acceptance condition specific to this work>

## Execution Notes

<!-- One block per session or resume: prior claimed state, live evidence checked, deltas corrected, checks rerun or owed, gates still open, model ID. -->

## Selfcheck Results

- Iteration 0: <initial draft: required headings present, markdownlint result; then one line per iteration with findings, fixes and evidence>

## Crosscheck Stop Marker

- **Status:** <pending, blocking or non-blocking>; closeout waits for non-blocking
- **Convergence profile:** <frontmatter value>
- **Tier 1:** <loops used> of <cap: 1 for `iterative_convergence_minimal`, up to 3 for `iterative_convergence_standard`, or a lower declared cap>; reviewer level per loop <levels>
- **Tier 2:** <not required (Level 0 to 2 work only), pending or done>; delta passes per tier-2 Major or Blocker <n> of 2; reviewer level <level>
- **Budget:** <from `cost_governance`, set once; spend so far>
- **Residuals:** <finding ID: fixed, accepted with reason (never for a tier-2 Major or Blocker), deferred with owner, or decision card>

## Requestor Review Gate

- [ ] Execution approved: <verbatim quote, date>
- [ ] Result accepted: <verbatim quote, date>
