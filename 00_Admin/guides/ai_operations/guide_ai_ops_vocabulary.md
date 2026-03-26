---
title: Guide: AI Ops Vocabulary
version: 1.0.5
status: active
license: Apache-2.0
last_updated: 2026-03-13
owner: ai_ops
related:
- ./guide_ai_operations_stack.md
- ./guide_contracts.md
- ./guide_workflows.md
promoted_from: 90_Sandbox/AI_Operations_Drafts/guide_ai_ops_vocabulary.md
---

# Guide: AI Ops Vocabulary

## Purpose

Defines the canonical vocabulary used across the AI Operations Stack. Normative — all agents and authors
must use these terms consistently to avoid ambiguity in governance artifacts and execution records.

This document defines the **canonical vocabulary** used across the AI Operations Stack. It is **normative**.

<!-- markdownlint-disable MD013 -->

## Goals

- Reduce ambiguity for AI agents and humans
- Standardize modality (must/should/may)
- Standardize constraint language (hard vs soft)
- Provide accepted aliases and explicit non-equivalences ("NOT this")

## 1) Modality (Normative Strength)

Use these words with the meanings below. Do not mix.

| Term | Meaning | Allowed In | Notes |
| --- | --- | --- | --- |
| **MUST** | Hard requirement; non-compliance is failure | Policy, Spec, Contract, Workbook | Equivalent to "shall" in standards writing |
| **MUST NOT** | Prohibited; non-compliance is failure | Policy, Spec, Contract, Workbook | Use for safety boundaries |
| **SHOULD** | Strong default; deviation requires explicit rationale | Policy, Runbook, Workflow | If you deviate, document why |
| **SHOULD NOT** | Strong discouragement; deviation requires explicit rationale | Policy, Runbook, Workflow | |
| **MAY** | Optional; allowed but not required | Any | |
| **RECOMMENDED** | Same as SHOULD, but less strict in tone | Guides only | Avoid in Contracts (prefer SHOULD) |
| **OPTIONAL** | Same as MAY | Guides only | Avoid mixing with MAY |

### NOT this

- Do NOT use **"try to"**, **"best effort"**, or **"ideally"** in Contracts or Specs.
- Do NOT use **"required"** without also mapping to MUST or SHOULD.

## 2) Constraints, Preferences, and Checks

These terms are distinct and must not be used interchangeably.

| Term | Definition | Primary Axis | Where It Lives | Enforced By |
| --- | --- | --- | --- | --- |
| **Constraint** | Hard safety or scope boundary | Verification | Contract / Workbook | Validators + agent behavior |
| **Preference** | Soft default; optimize for it but may deviate | Meta/Execution | Policy / Runbook | Agents (with rationale) |
| **Assumption** | Belief treated as true for a run | Commitment | Workbook | Human review + checks |
| **Commitment** | Locked parameter or scope for a run | Commitment | Workbook | Human governance |
| **Check** | Assertion verifying success or compliance | Verification | Contract | Validator + agent |
| **Test** | Concrete procedure to evaluate checks | Verification | Validator / Runbook | Validator + agent |
| **Precondition** | Must be true before execution begins | Verification/Execution | Contract / Runbook | Validator + agent |
| **Required State** | Target conditions required by the Contract | Verification | Contract | Validator + agent |

### NOT this (Constraints)

- A **Preference** is NOT a Constraint.
- A **Check** is NOT a Test (a check is the claim; a test is the method).
- An **Assumption** is NOT a Commitment (assumptions explain; commitments lock).

## 3) Artifact Vocabulary (AI Operations Stack)

Canonical terms, accepted aliases, and explicit exclusions.

| Canonical Term | Primary Axis | Lifecycle Tier | Accepted Aliases | NOT This |
| --- | --- | --- | --- | --- |
| **Policy** | Meta | Governance | Guideline, Standard | Guide (explanatory) |
| **Guide** | Meta | Reference | How-to, Overview | Policy (normative) |
| **Spec** | Meta | Governance | Specification, Schema | Guide (narrative) |
| **Work Proposal** | Meta | Governance | Proposal | Workbook |
| **Vocabulary / Glossary** | Meta | Reference | Terminology | Spec (schema) |
| **Catalog** | Meta | Reference | Registry, Index | Manifest (exhaustive) |
| **Manifest** | Meta | Reference | Inventory (exhaustive) | Catalog (curated) |
| **aiops manifest (`aiops.yaml`) [retired]** | Meta | Reference | Bootstrap manifest [retired; superseded by `AGENTS.md`] | Catalog (curated) |
| **Workflow** | Intent | Reference | Recipe, Agent Workflow | Runbook (execution-focused) |
| **Runbook** | Execution | Reference | SOP, Playbook | Workbook (committed run) |
| **Workbook** | Commitment | Commitment | Workbook | Runbook (reusable) |
| **Workbundle** | Commitment | Ephemeral | Workbook workbundle, workbundle folder | Workbook (the artifact itself) |
| **Workprogram** | Commitment | Commitment | Program, Work pipeline | Workbook (single-run) |
| **Execution Spine** | Commitment | Commitment | Program spine | Workbook (single-run plan) |
| **Runbundle** | Execution | Reference | Run workbundle | Workbook |
| **Runprogram** | Execution | Reference | Run pipeline | Workbook |
| **Pipeline** | Execution | Reference | DAG (if purely ordered) | Workflow (intent-level) |
| **Tool** | Execution | Reference | Script, CLI, Model | Contract (guarantee) |
| **Validator** | Verification | Reference | Linter, Checker | Tool (work executor) |
| **Logs** | Verification | Ephemeral | Audit log, Run log | Workbook (plan) |
| **Scratchpad** | Meta | Ephemeral | Scratch notes, Companion notes | Workbook (plan) |
| **Compacted Context** | Meta | Ephemeral | Handoff payload, Shared run state | Chat transcript |
| **Session Artifact** | Meta | Ephemeral | Scratch, Session File | Canonical doc |
| **Module** | Execution | Reference | Capability group (description only) | Domain (strict boundary) |
| **Parallel Execution** | Execution | Reference | Concurrent execution | Sequential-only execution |

Workbundle is the **transient folder container** under `90_Sandbox/ai_workbooks/` that groups a workbook with its
companion artifacts. A **Workbook** is the single `.md` execution artifact.

Workprogram coordinates multiple Workbooks/Workbundles and is not a workbook. Treat program artifacts as
pipeline-level orchestration files. Work Proposal is governance-only and
precedes execution workbooks. Runbundle serves the same grouping function for runbooks that Workbundles serve for
workbooks, but they are not interchangeable (different artifact types and locations).

Terminology stability rule: avoid churn between workpacket/workbundle naming. Use **workbundle** as canonical and keep
legacy aliases only in this glossary.

### Term Normalization Rule

When editing files, normalize legacy spaced or underscored variants to the single-token forms:

- `work packet`, `work_packet` -> `workbundle`
- `work program`, `work_program` -> `workprogram`
- `run bundle`, `run_bundle` -> `runbundle`
- `run program`, `run_program` -> `runprogram`

Program/book/bundle nuance:

- `*program` = pipeline-level orchestration artifact (coordinates `*bundle` and `*book` artifacts).
- `*bundle` = grouping container folder for a run/work execution scope.
- `*book` = primary executable markdown artifact for a scoped run/work commitment.

Scratchpads are append-only companion notes stored inside workbundles. They capture observations, friction points,
and decisions during execution. Use `_scratchpad_<agent>_<date>.md` naming. They are transient and archived with
the workbundle unless explicitly promoted.

Scratchpads are Meta artifacts: they preserve working notes, ideas, and local
context, but they do not prove correctness.

Compacted Context is a shared run-state artifact stored in a workbook body or
bundle/program README. It captures transparent history, intent, goals, current
state, outcomes, blockers, and next steps for agents and humans. Its primary
axis is Meta because it provides shared context infrastructure rather than
execution logic or verification proof.

Session Artifacts are temporary by default. Store them inside the active workbundle, keep them out of canonical
paths, and delete or archive them when the workbundle closes unless explicitly promoted.

Status values are defined in `00_Admin/policies/policy_status_values.md`. Use `planned`, `stub`, `active`, `completed`,
`deprecated` only. `draft` is not allowed.

### Spec vs Contract (Clarification)

**Spec** = descriptive requirements document (may or may not be enforced). **Contract** = versioned spec WITH
machine-enforced validation (binary pass/fail).

One-liner: "Contracts are specs with machine-enforced checks."

### Policy vs Contract (Comparison)

| Aspect | Policy | Contract |
| --- | --- | --- |
| **Definition** | Human-facing governance rules about HOW we work | Machine-enforceable agreements about WHAT must be true |
| **Enforcement** | Human judgment, code review | Automated validation, runtime checks |
| **Violations** | Require context and interpretation | Binary pass/fail |
| **Scope** | Process, conventions, standards | Data schemas, interfaces, invariants |
| **Typical Location** | `00_Admin/policies/` | `../<work_repo>/01_Resources/<domain_core>/contracts/`, `02_Modules/<module>/docs/contracts/` |

### Lifecycle Tiers (Summary)

- **Governance**: policies, specs, contracts; slow-changing system rules
- **Reference**: guides, templates, catalogs; stable but evolving
- **Commitment**: workbooks/execution spines; frozen for a run
- **Ephemeral**: logs, audit traces, scratch artifacts

## 4) Identity, IDs, and Referencing

| Term | Meaning | Rule |
| --- | --- | --- |
| **ID** | Stable identifier for an artifact (Contract, Pipeline, etc.) | MUST be unique within its namespace |
| **Path** | Repo-relative file location | Prefer relative paths |
| **Reference** | A pointer to an artifact via ID or path | Prefer ID where available |

### Referencing rules

- Runbooks and Workbooks SHOULD reference **Pipelines** and **Contracts** by **ID** when available.
- Runbooks and Workbooks SHOULD NOT reference **Tools** directly unless the Pipeline is intentionally omitted.

## 5) Agent Lane Vocabulary

Use canonical execution **lanes** as the upstream orchestration schema.

**Lane:** behavioral contract for a type of work -- what the agent is doing,
what permissions it holds, what model level it uses, and when to stop.

**Topology:** structural arrangement of execution -- how many agents, how they
are connected, what surface controls them. A topology uses lanes; `activated_lanes`
in a workbook declares which lanes are in scope, not which topology is used.

Any model or human may assume any lane.

| Lane | Responsibility | Outputs |
| --- | --- | --- |
| **Coordinator** | Selects workflows, plans runs, manages handoffs | Workbook drafts, compacted context |
| **Planner** | Converts approved scope into executable sequencing | Ordered execution plans, phase contracts |
| **Researcher** | Gathers evidence and reconciles context | Findings, inventories, contradiction checks |
| **Executor** | Executes the current step | Outputs + logs |
| **Builder** | Writes/edits tools and configs | Tool changes + diffs |
| **Reviewer** | Evaluates outputs against scope, governance, and correctness | Findings + evidence |
| **Linter** | Runs validators/linters without fixing files | Mechanical pass/fail + evidence |
| **Closer** | Finalizes completion and closeout state | Closeout summary + gate status |

**Rider:** a named behavioral archetype (logike / forge / anchor / scout) that shapes how
the agent approaches work -- caution, initiative, and judgment style. Riders are
**operator-selected** via `/profiles` and apply to the primary agent. They are
**lane-agnostic**: the same rider works regardless of which lane is active. Riders do not
assign to specific lanes and are not per-lane defaults. Without a selected profile, the
primary agent runs in default out-of-box posture.

**Profile:** a named behavioral contract that packages a rider archetype + professional
parameter sliders (autonomy, conservatism, initiative, deference) + technical config
(permission mode, max turns). Profiles are generated from source data. A profile may be
associated with a *typical* canonical lane in a crew config, but the rider inside it
remains lane-agnostic.

**Relational sliders** (Communication Depth, Tone Warmth, Formality, Directness) are a
separate category that applies to the **primary agent / Coordinator profile only** --
subagents return structured output and do not communicate directly with humans.

**Compatibility note:** The `executor` value used in workbook frontmatter
`ai_role` fields maps to the primary delivery identity of the session agent.
Canonical lane participation belongs in `activated_lanes`. The `role_assignments`
field broad-role keys are **deprecated**; use `activated_lanes` and `model_profile`
(level-based) instead. See `AGENTS.md §AI Model Level Reference`.

### Crew Model

The **Crew Model** is the umbrella term for how ai_ops configures and coordinates agents:
canonical lanes + behavioral archetypes (riders) + named profiles + model tier assignments.
Applies to both single-agent mode (virtual lane switching) and multi-agent mode
(primary agent orchestrating dedicated subagents). See
`00_Admin/guides/architecture/guide_design_and_philosophy.md` Sec.The Crew Model.

**model_level_map:** Operators may declare a model-ID-to-level binding in
`.ai_ops/local/config.yaml` under `customizations.model_capabilities.model_level_map`
(populated via `/customize`). This resolves workbook `model_profile` level references
to concrete model IDs at runtime.

### Agent Topology Terms

| Term | Meaning | Notes |
| --- | --- | --- |
| **Primary agent** | The agent the human interacts with directly in session. | Canonical term for current docs. |
| **Subagent** | A delegated agent spawned by the primary agent for a scoped role/task. | Used in multi-agent mode only. |
| **Lead agent** | Legacy alias for **primary agent**. | Keep for backward compatibility in older docs; prefer `primary agent` in new edits. |

### Compacted Context

At every handoff, the active agent MUST provide **Compacted Context**: minimal, structured context required for the next
step.

## Legacy Terminology

| Legacy Term | Canonical Term | Status |
| --- | --- | --- |
| `ai_work_packets/` | `ai_workbooks/` | Directory renamed |
| `wp_*` | `wb_*` | Prefix renamed |
| `work_bundle` | `workbundle` | Deprecated alias |

## 6) Repository and Industry Alignment

Repository and industry analogies are provided for context only and live in Appendix A.

## 7) Change and Promotion Vocabulary

| Term | Meaning | Rule |
| --- | --- | --- |
| **Adopted Tool** | Vetted tool approved for reuse | MUST NOT be overwritten casually |
| **Temporary Tool** | One-off implementation for a run | MUST be isolated and explicitly named |
| **Promotion** | Process of moving temporary -> adopted | Requires explicit governance review |

## 8) Forbidden Terms (Pointer)

Avoid ambiguous terms that imply human-only actions unless a human is explicitly required. See
`00_Admin/guides/authoring/guide_ai_assistants.md` and VS017 in
`00_Admin/configs/validator/validator_config.yaml` for the current list.

This vocabulary is the system's language contract.

## 9) Operational Vocabulary (Slash Commands)

Terms used in `.ai_ops/workflows/*.md` slash command definitions.

| Term | Definition | Used In |
| --- | --- | --- |
| **CSCC** | Cold-start, capacity-constrained. Describes an execution context where the agent starts with no prior session state and must operate within bounded context (token budget, limited reads). CSCC lanes must be self-contained: all required context must be readable from the artifact itself without relying on session memory. | All workflows |
| **Turbo Authorization** | Pre-authorized commit/push without interactive pause. Applies when the user has already approved the work scope. See `rb_commit_push_streamlining_01.md`. | `/closeout` |
| **Thrift Pass** | A review to remove unnecessary content, tighten wording, and confirm each element belongs in the artifact. Reduces bloat and improves clarity. | `/crosscheck`, `/health` |
| **ai_ops_session** | The period between `/work` (or `/bootstrap`) and `/work_savepoint` when repo rules actively apply. During a session, the agent follows ai_ops governance. Ending a session (via `/work_savepoint`) suspends active tracking. | `/work_savepoint` |

## 10) Mode Vocabulary

Operating modes determined by target repo relationship to ai_ops.

| Mode | Definition | Trigger |
| --- | --- | --- |
| **Direct** | Working on ai_ops itself. Workbooks stored in ai_ops's `90_Sandbox/ai_workbooks/`. Full governance applies. | Target is ai_ops repo |
| **Governed** | Working on external repo via ai_ops governance. Workbooks stored in external repo's sandbox. ai_ops authority levels, workflows, and templates apply. Git operations happen in target repo. | Target is external repo listed in `AGENTS.md` workspace topology `work_repos` |
| **Standalone** | Working in repo with no ai_ops connection. Agent adapts to that repo's conventions. No ai_ops governance assumed. | No `AGENTS.md` with ai_ops structure reachable |

Mode is determined by **target repo**, not by whether a bootstrap marker exists. Once set during `/work`, mode persists
until `/work_savepoint` ends the session.

## Appendix A: Repository and Industry Alignment

### Repository-Specific Vocabulary

| Term | Meaning | Source |
| --- | --- | --- |
| Phase | Stage in a domain capability roadmap (for example foundation phase, implementation phase, verification phase) | Domain capability index/work program |
| Engine | Named domain logic component or service boundary within that roadmap | Domain specs and module contracts |
| Module metadata | `module.yaml` describing module ID/deps | `02_Modules/*/metadata/module.yaml` |
| Operation / Tool | Executable following `op_*` or script pattern | `02_Modules/*/operations/` or `00_Admin/scripts/` |
| Compacted Context | Shared run-state and handoff payload (YAML) pointing to artifacts | This guide + `guide_ai_operations_stack.md` |
| Reference Pack | Pointer YAML to large supporting materials | `packs/pack_*.yaml` stubs |

### Industry Alignment (Informative)

| Our Term | Rough External Analogy | Notes |
| --- | --- | --- |
| Module | Anthropic MCP Skill | Ours is capability grouping with metadata |
| Tool | MCP tool / API endpoint | Executable behind contracts/pipelines |
| Contract | API schema / interface contract | Behavioral guarantees |
| Agent | GPT "assistant" / MCP server actor | Canonical lanes, non-anthropomorphic |
| Workbook | Single-run plan | External "runbook" in some orgs |

<!-- markdownlint-enable MD013 -->
