---
description: Signal that repo rules apply and establish work/run context.
name: work
kind: workflow
version: 0.4.0
status: active
owner: ai_ops
license: Apache-2.0
claude:
  argument-hint: null
  disable-model-invocation: false
  user-invocable: true
  allowed-tools: null
  model: null
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

Signal that repo rules apply and establish work/run context for execution. `/work` is the canonical lane for
approved edits to canonical ai_ops surfaces. Mode rules live in `00_Admin/specs/spec_work_mode.md`; required
workbook sections live in `00_Admin/specs/spec_workbook_structure.md` section 4.

## Inputs and Preconditions

- No inputs are required, but task scope must be confirmed before edits.
- If intent is unclear or illogical, pause and ask clarifying questions.
- If the request is a question, answer it; do not convert it to edits.
- A seed, proposal or datapoint without an explicit execution action is captured in the scratchpad first and
  confirmed before edits.

## Setup-State Guard (Mandatory)

Before work beyond intake, read `required_version` from `00_Admin/configs/setup_contract.yaml` and, when present, the
setup receipt at the receipt path that file names (default `.ai_ops/local/setup/state.yaml`). If required setup is
missing and the defaults are insufficient, stop and route to `/ai_ops_setup` with path-specific remediation; if the
defaults suffice, proceed and note optional hardening.

## Context Routing Hook

Use `00_Admin/configs/context_routing.yaml` as the canonical onboarding contract. Read only `commands._defaults`,
`commands.work` and `policy.global_execution_gates`, by key search, not the whole file.

1. Apply `commands._defaults.guard_profile` and `commands.work.guard_profile`.
2. Resolve onboarding tier in order: `fresh_bootstrap`, `resume_same_scope`, `recenter` (fallback `fresh_bootstrap`
   when state is unknown). `context_routing.yaml` marks `resume_same_scope` unreachable until `fw_20260315_01` lands
   session state, so apply `fresh_bootstrap` or `recenter`.
3. Load `always_read`; expand `read_on_demand` only when needed.
4. Emit route metadata in execution output: `bootstrap_path`, `resume_basis`, and `reads_applied`.
   The optional side-effect-free helper `python 00_Admin/scripts/emit_work_route_metadata.py`
   validates and emits the complete `/work` block, including `context_reset_applied`
   and `scope_echo`; the caller preserves its JSON output in the run record.
5. Apply canonical bootstrap guard BRG-01: if bootstrap requirements are missing or unverifiable, apply
   `fresh_bootstrap` tier (read `AGENTS.md`) before lane steps.

### Run-Family Graph Hook

When scope creates, changes, resolves, or migrates a runprogram, runbundle, or runbook, load
`spec_artifact_graph_identity.md`, `spec_run_family_composition.md`, and `run_family_registry.yaml` on demand.
Resolve affected declared consumers before a shared-artifact write; name one merge owner and require a validation
receipt or operator-approved disposition for each consumer. Generated registry/graph views never grant write
authority.

## Scope Block: Intake Classification and Boundary Statement (Mandatory)

Before execution, record one scope block:

1. **Target and mode:** resolve the mode with `AGENTS.md` "Mode Detection", then the target: explicit user target,
   open-file context when unambiguous, then the `AGENTS.md` workspace topology (`work_repos`) and local overrides.
   If still ambiguous, ask: "Which repo do you want to work on?" External repos adopting ai_ops use Governed mode
   unless the requestor, as a maintainer, asks for another. Until context is established, run no recursive scans and
   limit reads to manifest-declared paths and active artifacts.
2. **Intake class:** `design_reference`, `execution`, `execution_resume`, `validation`, `state_sync` or
   `approval_gate`.
3. **Boundary statement:** the lanes and actions that may run inline under the current approval, those that stay
   hard-gated, and whether canonical writes, runtime or network checks, commit or push, or unresolved holds need
   separate approval. For `execution_resume`, name the previously gated phases now authorized and the stop
   conditions that stay hard-gated regardless of blanket approval. Approval to create a workbook does not authorize
   its execution; commit and push stay separate human gates.

Guards that apply throughout (each has one home):

- **Pre-write authority guard:** `AGENTS.md` "Path-Based Authority Guard (Pre-Write)", read before any file write;
  an ambiguous classification is treated as higher authority and asked.
- **Cross-repo references:** `spec_work_mode.md` section 5 (VS028).

## Resume Contract (Mandatory)

For any resumed or multi-surface run, write a resume-delta block before changing state surfaces or advancing
completion claims. Write it to the existing state surface -- the workbook Execution Notes, or the workbundle README
when the bundle coordinates the run -- as one block per resume, not one per phase. Do not create a new file or
ledger for it: prior claimed state, live evidence checked, deltas found and corrected, validators or checks rerun or
owed, and gates still open. If prior claims and live evidence disagree, repair stale wording before moving the run
forward. See `00_Admin/specs/spec_cross_surface_coordination.md`.

## Active Work and Placement

`.ai_ops/local/work_state.yaml` `work_context.active_artifacts` is authoritative; never scan the filesystem to infer
active artifacts. If the file is absent, create it from the empty template before tracking. Before creating a
workbook or workbundle, echo the request scope and candidate placement and evaluate relevance (`match`, `mismatch`
or `uncertain`; `spec_work_mode.md` section 4). On `mismatch` or `uncertain`, ask the requestor to use the current
artifact, switch to an existing one or create a new one, and record the placement decision echo (in the workbook's Scope and Authority or the bundle README) before writing.
Register a new artifact in `work_state.yaml` before work starts.

## Execution Topology and Delegation Gate (Before Artifact Creation) (Mandatory)

Before creating or substantially rewriting a workbook, runbook or spine, classify `execution_topology`
(`single_agent`, `multi_agent` or `hybrid`), declare `activated_lanes` (baseline `Coordinator -> Executor ->
Reviewer`) and `delegation_policy` with any known spawn criteria, and reuse or create `parallel_coordination_id`
when sibling active artifacts may run concurrently. Books and runbooks own the contract (the expanded block only for material delegation,
`spec_workbook_structure.md` section 4); spines carry only a coordination summary. Record this before execution; do not leave topology to runtime guesswork.

## Workbook Preflight Gate (Before Execution)

Run one section check on any workbook selected or created, in Direct and Governed mode alike, before its first
phase: the headings and gate behaviors in `00_Admin/specs/spec_workbook_structure.md` section 4. Read
`model_profile`, `execution_topology`, `activated_lanes`, `delegation_policy`, `convergence_profile` and
`role_assignments` (when present) before execution; a malformed or unknown value stops the workbook. If a required
heading is missing, patch the workbook before execution and record the evidence.

## Steps

One flow for every mode; the table lists what changes by mode (`spec_work_mode.md` section 3 holds the Direct and Governed rules; the Standalone column is its whole rule).

1. Run the Setup-State Guard, record the readiness disposition, and apply the Context Routing Hook.
2. Record the scope block.
3. Resolve active artifacts for the target: if some exist, ask continue or switch; if none, ask whether to use an
   existing artifact (one the requestor names) or create one.
4. Run the placement check and register the selected or created artifact, with its `repo` field.
5. For a new workbook, runbook or spine, run the Execution Topology and Delegation Gate before writing its body. For
   any workbook selected or created, run the Workbook Preflight Gate.
6. Execute the scoped tasks under the authority guard.
7. Complete per the Pre-Completion Validation Order.

| Step | Direct (`ai_ops`) | Governed (external repo) | Standalone |
| --- | --- | --- | --- |
| Target | `ai_ops` | `work_repos`; add a new repo there and create its sandbox if missing | the repo root and provided context docs; ask before reading beyond them |
| Artifacts | ai_ops state entries | state entries for the target repo | small scope directly; propose a workbook or runbook for larger scope, in the repo's own conventions |
| Validation | ai_ops validators | `customizations.validation_policy.governed_mode` in `.ai_ops/local/config.yaml` | the repo's own checks |

## Pre-Completion Validation Order

Before reporting completion in workbook lanes:

1. Finish scoped deliverables and complete the workbook verification checklist.
2. Run required validators, lint and tests for touched scope. For narrow-lane workbooks, use the scoped `git
   status`/`git diff --stat` discovery pattern in `policy_git_workflow_conventions.md` "Scoped Discovery for
   Narrow-Lane Work" to confirm touched-file scope before validation.
3. Record command evidence with environment context.
4. Run the selfcheck loop (max 3 iterations) from `AGENTS.md`; review loops (tiers, caps, budget, who closes) follow
   `crosscheck.md` "Loop Control".

If checks fail, keep the workbook active, fix, and rerun.

## Outputs

- Current work context summary and next actions.
- Clarifying questions when target/scope is ambiguous.
- Handoff to other command lanes when requested action is out-of-lane.

## Resources

- `00_Admin/specs/spec_work_mode.md`
- `00_Admin/specs/spec_workbook_structure.md`
- `00_Admin/specs/spec_cross_surface_coordination.md`
- `00_Admin/guides/ai_operations/guide_work_programs.md`
- `00_Admin/guides/authoring/guide_workbooks.md`
- `00_Admin/guides/authoring/guide_runbooks.md`

## Lane

Default lane path: Coordinator -> Executor -> Reviewer (activate other lanes only when task shape requires them).

## Risks and Limits

- Broad scope can cause drift; confirm boundaries before execution.
- Do not execute code or modify files without explicit user intent.
- Do not perform canonical edits outside authority guard requirements.
- Do not assume ai_ops structure in standalone repos.
- Do not assume command folders exist; if missing, read `.ai_ops/workflows/work.md` directly.
