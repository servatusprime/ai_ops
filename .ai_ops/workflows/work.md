---
description: Signal that repo rules apply and establish work/run context.
name: work
kind: workflow
version: 0.2.2
status: active
owner: ai_ops
license: Apache-2.0
claude:
  argument-hint: null
  disable-model-invocation: false
  user-invocable: true
  allowed-tools: null
  model: null
  context: null
  agent: null
codex:
  metadata:
    short-description: Signal that repo rules apply and establish work/run context.
  interface:
    display_name: work
    short_description: Signal that repo rules apply and establish work/run context.
  policy:
    allow_implicit_invocation: true
exports:
  claude_plugin:
    enabled: true
    skill_name: work
  codex:
    enabled: true
    skill_name: work
  claude_project:
    enabled: true
    skill_name: work
---

<!-- markdownlint-disable MD013 -->
# /work

## Purpose

Signal that repo rules apply and establish work/run context for execution.
`/work` is the canonical lane for approved edits to canonical ai_ops surfaces.

## Inputs and Preconditions

- No inputs required, but task scope must be confirmed before edits.
- If intent is unclear or illogical, pause and ask clarifying questions.
- If request is a question, answer first; do not convert to edits implicitly.

## Setup-State Guard (Mandatory)

Before `/work` execution beyond intake:

1. Read `required_version` from `00_Admin/configs/setup_contract.yaml`.
2. Read setup receipt from receipt path in `00_Admin/configs/setup_contract.yaml`
   (default: `.ai_ops/local/setup/state.yaml`) when present.
3. If required setup is missing and defaults are insufficient, stop and route
   to `/ai_ops_setup` with path-specific remediation.
4. If defaults are sufficient, proceed and note optional setup hardening.

## Pre-Flight Gates (Mandatory)

Before any broad file exploration:

1. Read `AGENTS.md` first.
2. Do not run recursive scans until context is established.
3. Limit initial exploration to manifest-declared paths and active artifacts.
4. If multiple repos are available, confirm target repo before cross-repo reads.
5. Treat questions as questions until explicit execution is requested.
6. If request text is seed/proposal/datapoint intake without explicit execution
   action, capture in scratchpad first and confirm before edits.

## Lane/Profile Topology Gate (Mandatory)

After bootstrap read order and before execution:

1. Read these `AGENTS.md` sections:
   - `Role Reference`
   - `AI Model Level Reference`
   - `Agent Profiles`
   - `Context Management`
2. Confirm these distinctions explicitly:
   - Canonical lanes (`Coordinator`, `Planner`, `Researcher`, `Executor`,
     `Builder`, `Reviewer`, `Linter`, `Closer`) are the upstream execution
     schema.
   - Legacy broad-role keys (`Coordinator`, `Executor`, `Builder`,
     `Validator`) remain compatibility keys for `role_assignments`.
   - Profiles/riders are behavior presets and do not replace canonical lane
     semantics.
   - `primary agent` is the user-facing session agent; `subagents` are
     delegated workers in multi-agent runs.
   - `/profiles` tunes behavior profiles; workbook `activated_lanes` declare
     canonical participation, while `role_assignments` remain compatibility
     overrides for model-tier hints.
3. For CSCC workbook/workbundle/workprogram lanes, confirm compacted context
   location (workbook body vs bundle/program README).
4. If any distinction is unclear, pause and ask.

## Context Routing Hook

Use `00_Admin/configs/context_routing.yaml` as the canonical onboarding
contract.

1. Apply `commands._defaults.guard_profile` and `commands.work.guard_profile`.
2. Resolve onboarding tier in order: `fresh_bootstrap`,
   `resume_same_scope`, `recenter` (fallback `fresh_bootstrap` when state is
   unknown).
3. Load `always_read`; expand `read_on_demand` only when needed.
4. Emit route metadata in execution output:
   `bootstrap_path`, `resume_basis`, and `reads_applied`.
5. Apply canonical bootstrap guard BRG-01:
   if bootstrap requirements are missing or unverifiable, apply
   `fresh_bootstrap` tier (read `AGENTS.md`) before lane steps.

## Resume Contract (Mandatory)

Use the `resume_same_scope` fast path only when all are true:

- target repo unchanged
- mode unchanged
- no recenter trigger fired

If any condition is unknown or false, use `fresh_bootstrap` or `recenter`.
Do not force heavy topology/routing rereads when `resume_same_scope` is valid.

## Pre-Write Authority Guard (Mandatory)

Canonical source is `AGENTS.md`.

| Path Pattern | Minimum Authority | Required Behavior |
| --- | --- | --- |
| `00_Admin/policies/**`, `00_Admin/specs/**`, `AGENTS.md`, `CONTRIBUTING.md` | Level 4 | Stop and require explicit human approval with rationale. |
| `.ai_ops/workflows/**` | Level 4 | Stop and require explicit approval evidence before edits; record approval source in workbook/scratchpad. |
| `00_Admin/configs/**` | Level 4 | Stop and require explicit human approval. |
| `00_Admin/guides/**` | Level 3 | Require workbook scope and approval before edits. |
| `90_Sandbox/**` | Level 1-2 | Proceed only when in-scope and user-requested. |

If classification is ambiguous, treat as higher authority and ask.

## Mode and Target Selection

Mode depends on target repo:

| Target | Mode | Behavior |
| --- | --- | --- |
| ai_ops repo | Direct | Work directly in ai_ops; workbook artifacts in ai_ops sandbox |
| external repo with ai_ops governance | Governed | Apply ai_ops governance in target repo (validators/linters per validation policy) |
| no ai_ops structure reachable | Standalone | Adapt to target repo conventions |

Default expectation: external repos adopting ai_ops governance should use
Governed mode unless the requestor explicitly identifies as a maintainer
requesting a different mode.

Target repo resolution order:

1. explicit user target
2. open-file context when unambiguous
3. `AGENTS.md` workspace topology (`work_repos`) and local overrides

If still ambiguous, ask: "Which repo do you want to work on?"

## Cross-Repo Reference Contract (Mandatory)

Enforce `spec_work_mode_governed.md` §3.7 cross-repo reference policy during
all `/work` edits. Key rules:

- In `ai_ops` artifacts: use generic placeholders, not concrete governed-repo
  names or paths.
- In governed repos: use repo-relative ai_ops paths (`../ai_ops/...`), not
  machine-local absolute paths.

See `00_Admin/specs/spec_work_mode_governed.md` for the full normative rule.

## Active Work Resolution

`.ai_ops/local/work_state.yaml` `work_context.active_artifacts` is authoritative.

1. If populated, these are active artifacts.
2. If missing/empty, there is no active work context.
3. Do not scan filesystem to infer active artifacts.
4. If file is absent, create from empty template before tracking.

## Workbundle Relevance Gate (Before Workbook Creation) (Mandatory)

Normative spec:
`00_Admin/specs/spec_workbundle_placement_suggestion.md`.

Before creating workbook/workbundle artifacts:

1. Echo request scope and candidate placement.
2. Evaluate relevance: `match`, `mismatch`, or `uncertain`.
3. If `mismatch` or `uncertain`, ask requestor to choose:
   use current, switch existing, or create new.
4. Record placement decision echo before writing artifacts.

## Execution Topology and Delegation Gate (Before Artifact Creation) (Mandatory)

Before creating or substantially rewriting a workbook, runbook, spine, or
pipeline artifact:

1. Classify `execution_topology`:
   `single_agent`, `multi_agent`, or `hybrid`.
2. Declare `activated_lanes` for the run. Default baseline:
   `Coordinator -> Executor -> Reviewer`.
3. Declare `delegation_policy` and any spawn criteria or do-not-delegate
   constraints already known.
4. Decide whether the artifact owns the full
   `execution_topology_contract` (books/runbooks) or only a coordination
   summary (spines/pipelines).
5. If sibling active artifacts may run concurrently, create or reuse
   `parallel_coordination_id`.
6. Record this contract before execution begins; do not leave topology to
   runtime guesswork.

## Workbook Preflight Gate (Before Execution)

Required workbook sections:

- `## Execution Topology Contract`
- `## Cold-Start Execution Contract`
- `## Pre-Execution Readiness Gate`
- `## Ordered Execution Queue`
- `## Verification Checklist`
- `## Selfcheck Results`

Read these routing fields before execution:

- `model_profile` (overall tier)
- `execution_topology`
- `activated_lanes`
- `delegation_policy`
- `convergence_profile`
- `role_assignments` (compatibility overrides, when present)

If missing, patch workbook structure before execution and record evidence.

## Steps

### Direct Mode (ai_ops)

1. Confirm mode/target and apply context routing hook.
2. Run Setup-State Guard and record readiness disposition.
3. Resolve active artifacts from `.ai_ops/local/work_state.yaml`.
4. If active artifacts exist, ask continue vs switch.
5. If no active artifacts, ask whether to use existing artifact or create new.
6. Before creating workbook/workbundle, run Workbundle Relevance Gate.
7. Add selected/created artifact to local active state.
8. If artifact is a workbook, run Workbook Preflight Gate.
9. If a new workbook/runbook/spine/pipeline is being created, run Execution
   Topology and Delegation Gate before writing the artifact body.
10. Execute scoped tasks under authority guard and thrift gate.
11. Use `spec_work_mode_direct.md` for direct-mode specifics.

### Governed Mode (External Repo via ai_ops)

1. Confirm target repo and apply context routing hook.
2. If new repo, add to local `work_repos` and create sandbox if missing.
3. Resolve active artifacts for target repo from local state.
4. If active artifacts exist, ask continue vs switch.
5. If no active artifacts, ask whether to use existing artifact or create new.
6. Before creating workbook/workbundle, run Workbundle Relevance Gate.
7. Add selected/created artifact to local active state with `repo` field.
8. If artifact is a workbook, run Workbook Preflight Gate.
9. If a new workbook/runbook/spine/pipeline is being created, run Execution
   Topology and Delegation Gate before writing the artifact body.
10. Read `customizations.validation_policy.governed_mode` from `.ai_ops/local/config.yaml`.
11. Apply ai_ops governance to target repo execution and validations using the selected policy.
12. Use `spec_work_mode_governed.md` for governed-mode specifics.

### Standalone Mode

1. Confirm target repo root and available context docs.
2. Ask permission before reading beyond provided context artifacts.
3. Handle small-scope requests directly; propose workbook/runbook for larger
   scope.
4. Adapt to target repo conventions without forcing ai_ops structure.

## Pre-Completion Validation Order

Before reporting completion in workbook lanes:

1. Finish scoped deliverables.
2. Complete workbook verification checklist.
3. Run required validators/lint/tests for touched scope.
4. Record command evidence with environment context.
5. Run selfcheck loop (max 3 iterations) from `AGENTS.md`.

If checks fail, keep workbook active, fix, and rerun.

## Outputs

- Current work context summary and next actions.
- Clarifying questions when target/scope is ambiguous.
- Handoff to other command lanes when requested action is out-of-lane.

## Resources

- `00_Admin/specs/spec_work_mode_direct.md`
- `00_Admin/specs/spec_work_mode_governed.md`
- `00_Admin/specs/spec_work_focus_recenter.md`
- `00_Admin/specs/spec_workbundle_placement_suggestion.md`
- `00_Admin/guides/ai_operations/guide_work_programs.md`
- `00_Admin/guides/ai_operations/guide_workflows.md`
- `00_Admin/guides/authoring/guide_workbooks.md`
- `00_Admin/guides/authoring/guide_runbooks.md`

## Lane

Default lane path: Coordinator -> Executor -> Reviewer (activate other lanes
only when task shape requires them).

## Risks and Limits

- Broad scope can cause drift; confirm boundaries before execution.
- Do not execute code or modify files without explicit user intent.
- Do not perform canonical edits outside authority guard requirements.
- Do not assume ai_ops structure in standalone repos.
- Do not assume command folders exist; if missing, read
  `.ai_ops/workflows/work.md` directly.
