---
title: "Guide: ai_ops"
version: 2.3.5
status: active
license: Apache-2.0
last_updated: 2026-03-13
owner: ai_ops
related:
  - ./guide_ai_ops_vocabulary.md
  - ./guide_contracts.md
  - ./guide_workflows.md
---

# Guide: ai_ops

This guide defines **ai_ops**, the AI-first governance layer. It is **normative**. If any document
conflicts with this guide, this guide prevails.

## Purpose

ai_ops provides a formal structure for AI-first work planning, execution, and verification:

- Enable reliable multi-agent execution
- Reduce ambiguity and context burden
- Make governance enforceable by machines

## Cornerstones: The Axes

ai_ops is built on two sets of axes that serve as organizing principles for all work.

### Primary Organizing Axes (Artifact Classification)

All work artifacts MUST map to exactly one primary axis:

| Axis | Purpose | Reference |
| ---- | ------- | --------- |
| **Intent** | Describe desired outcomes | Workflows |
| **Commitment** | Freeze approved scope for a run | Workbooks, Execution Spines |
| **Execution** | Define how work is carried out | Runbooks, Pipelines, Tools |
| **Verification** | Define correctness and safety | Contracts, Validators, Logs |
| **Meta** | Explain, govern, or carry shared context | Policies, Guides, Specs, Compacted Context |

Cross-references are allowed. Mixed responsibility is not.

**Reference direction:** Intent -> Commitment -> Execution -> Verification. Meta may inform any layer.

### Quality Axes (Review Dimensions)

Every artifact and operation is evaluated against four quality axes:

| Axis | Purpose | Interpretation | Scope |
| ---- | ------- | -------------- | ----- |
| **Clarity** | Cold-start readability | No inference required; inputs/steps/outputs explicit. | Local |
| **Thrift** | Efficient required outcome | See canonical thrift interpretation below (normative). | Local + Global |
| **Context** | Reliable resumption/handoff | Work restarts from files; handoff state explicit. | Global |
| **Governance** | Authority and gate discipline | Authority boundaries explicit, traced, and enforced. | Global |

Thrift interpretation:

> Thrift is not minimalism. Thrift is efficiency -- the minimum cost to achieve
> the required outcome.
>
> In ai_ops, cost includes not just artifact size, but also execution burden:
> avoidable read hops, retracing, and other internal cycle burden that slow
> cold-start execution or review.

For quantitative cost governance levers (token budgets, model routing preferences,
alert thresholds), see `00_Admin/specs/spec_cost_governance.md`. The Thrift axis is
the qualitative goal; that spec defines the optional machine-readable contract agents
use to self-govern their cost footprint.

**Local vs Global:**

- **Local:** Apply to individual artifacts (each file, each section)
- **Global:** Apply across the entire task chain (bootstrap -> work -> closeout)

**Quality Axes Checklist (Pre-Completion):**

Before reporting work complete, verify:

- [ ] **Clarity Pass:** A low-context reader can follow inputs, steps, and outputs without inference
- [ ] **Thrift Pass:** No bloat introduced; each element belongs in this artifact
- [ ] **Context Check:** Compacted context updated; handoff is clear
- [ ] **Governance Check:** Authority level respected; scope not exceeded

### Internal Cycle Burden (Diagnostic Signal)

Internal cycle burden is the avoidable cost introduced when an agent must
retrace steps across multiple artifacts to complete one lane.

- Applies primarily to `Thrift` and `Context` axes.
- Increases when contracts are duplicated, split without routing, or moved
  without explicit landing-zone pointers.
- Pass condition: required reads are explicit, minimal, and ordered; no
  unnecessary back-and-forth hops are needed for cold-start execution.

## Boundary Reinforcement

Use this reinforcement when designing or patching governance artifacts:

- **Governance upstream:** Cross-artifact governance rules belong in upstream
  guides/specs/policies.
- **Context downstream:** Execution-profile specifics belong in templates and
  active workbook/runbook artifacts.
- **Thrift includes cycle burden:** If an agent must bounce repeatedly across
  documents to execute one lane, thrift is failing.

Design test:

1. If the rule is stable and cross-artifact, move it up.
2. If the rule is lane-specific and execution-local, move it down.

Operational enforcement surface:

- Runtime execution contract and selfcheck loop: `AGENTS.md`
- Workflow-level behavior and handoffs: `00_Admin/guides/ai_operations/guide_workflows.md`
- Crosscheck structure and streamlining checks: `.ai_ops/workflows/crosscheck.md`

---

## Canonical Artifact Types

For the comprehensive artifact vocabulary including lifecycle tiers, accepted aliases, and
exclusions, see `guide_ai_ops_vocabulary.md` Section 3.

**Summary by axis:**

| Axis | Key Artifacts |
| ---- | ------------- |
| Meta | Policy, Guide, Spec, Work Proposal, Compacted Context, Scratchpad, Vocabulary, Catalog, Manifest |
| Intent | Workflow |
| Commitment | Workbook, Execution Spine, Workprogram |
| Execution | Runbook, Runbundle, Runprogram, Pipeline, Module, Tool |
| Verification | Contract, Validator, Logs |

Compacted Context and Scratchpad are Meta artifacts because they provide
cross-cutting shared context and working notes rather than execution logic or
verification proof.

---

## Immutability Rules

- **Workbooks** are immutable after approval
- **Execution Spines** are append-only or versioned
- **Logs** never enact changes
- **Contracts** change only via governance review

---

## Agents

Agents operate via **canonical lanes** as the execution schema. The primary
orchestration model is lane-based. The complete configuration of lanes +
behavioral archetypes (riders) + profiles + model tiers is the **Crew Model**
-- see `00_Admin/guides/architecture/guide_design_and_philosophy.md`
Sec.The Crew Model for the full conceptual overview.

For the complete lane vocabulary, see `guide_ai_ops_vocabulary.md` Section 5.

**Summary:**

| Lane | Responsibility |
| ---- | -------------- |
| Coordinator | Selects workflows, plans runs, manages handoffs |
| Planner | Converts approved scope into executable sequencing |
| Researcher | Gathers evidence, reconciles context, and surfaces gaps |
| Executor | Executes the current step |
| Builder | Writes or modifies tools/configs |
| Reviewer | Evaluates outputs for correctness, governance fit, and adequacy |
| Linter | Runs mechanical validation and reports tool-backed findings |
| Closer | Finalizes completion, closeout, and handoff readiness |

### Agent Delegation Patterns

When a workbook involves multiple lanes, each significant lane transition is a natural
boundary for spawning a sub-agent. Use this heuristic to decide:

| Condition | Pattern | Example |
| --- | --- | --- |
| Lanes can run in parallel | Parallel sub-agents | Multiple Executor agents for independent tasks |
| Lane needs a different model tier | Separate sub-agent with `model` override | Reviewer spawned at high tier for crosscheck |
| Lane is a clean handoff with distinct outputs | Separate sub-agent (context isolation) | Builder sub-agent for tool edits |
| Task is short, sequential, shared state | Inline in current session | Simple config edits within an executor run |

**Common sequencing pattern:**
Coordinator (main session) -> spawn Executor sub-agents -> results returned ->
Coordinator runs Linter/Reviewer checks (optionally higher tier) -> findings
return to the lead lane.

**Model tier selection:** A Coordinator running at medium tier MAY spawn a Reviewer
at high tier. Use `model_profile` and `activated_lanes` in workbook frontmatter to
declare the overall tier and active lane set. The `model` parameter on the Agent
tool controls the actual model used when spawning. (`role_assignments` broad-role
keys are deprecated -- see `AGENTS.md` AI Model Level Reference.)

**model_level_map:** Operators may bind concrete model IDs to ai_ops reasoning
levels (1–4) in `.ai_ops/local/config.yaml` under
`customizations.model_capabilities.model_level_map` (populated via `/customize`).
This binding resolves workbook `model_profile` level references at runtime.

**Enhanced Crosscheck Mode:** A pattern where the executor spawns a higher-tier
sub-agent specifically for the crosscheck phase, enabling a more capable model to
review the work. Enable by setting a higher review tier in workbook frontmatter
and using the high-tier runtime model when spawning the review agent.

**Relational sliders** (Communication Depth, Tone Warmth, Formality, Directness)
apply to the **primary agent / Coordinator profile only** -- subagents return
structured output to the primary agent and do not communicate directly with
humans.

### Topology vs Lane

A **lane** defines the *behavioral contract for a type of work* -- what the agent
is doing, what permissions it holds, what model level it uses, and when to stop.

A **topology** defines the *structural arrangement of execution* -- how many agents,
how they are connected, what surface controls them.

The governing rule: **a topology uses lanes; a lane is not a topology.** All 8 lanes
can run inside a single-agent topology. Those same lanes can be distributed across
agents in a multi-agent topology. `activated_lanes` in a workbook declares which
lanes are in scope -- it does not determine the topology.

For the canonical topology table and topology/lane concepts, see `AGENTS.md`
section `### Topology and Lane Concepts`.

**Director topology (design note, not yet implemented):** A Director pattern
allows one primary session to spawn Coordinator subagents per project for
concurrent work streams. See `AGENTS.md §Topology and Lane Concepts`.

### Lane Extensibility

New lanes MAY be added if responsibilities are non-overlapping. If the repo
uses the optional `01_Agents/` pattern, register them in
`01_Agents/metadata/agent_registry.yaml`. Otherwise, document role capabilities
and handoff rules alongside the owning module metadata under
`02_Modules/`.

### Operational Behavior Location

To keep stack governance upstream and runtime context downstream:

- Role assignment and role transition behavior: `00_Admin/guides/ai_operations/guide_workflows.md`
- Agent runtime contract (bootstrap, authority quick path, selfcheck loop): `AGENTS.md`
- Agent runtime behavior and authority contract: `AGENTS.md`
- Execution drift-recovery reliability controls:
  `00_Admin/specs/spec_execution_orchestration.md`

---

## Context Handoff (Compacted Context)

Context handoff = making work resumable from repository artifacts, not chat history.

Compacted Context is a Meta artifact: shared context infrastructure used during
handoff, execution, and review.

### Principles

- Repository is authoritative; conversations are optional UI.
- Every workflow must be restartable from files (inputs/outputs/state clear).
- Reference documents by path; do not inline large materials.

Workprograms SHOULD reference their workbooks/workbundles by path or ID and include an Execution
Spine. Runprograms SHOULD reference their runbooks by path or ID and include an Execution Spine.

**Compacted Context placement:**

- Standalone workbooks/runbooks: include compacted context inside the artifact.
- Workbundles/runbundles/workprograms: place compacted context in the README.
- If a workbundle README already contains compacted context, omit duplicate from the workbook body.

### Compacted Context Structure (Handoff Payload)

```yaml
compacted_context:
  from_role: <role>
  to_role: <role>
  proposal_id: <work_proposal_id>   # required for Level 4
  completed_step:
    summary: <one-sentence>
    workbook: <wb_id>
    outputs:
      - <path>
  next_step:
    goal: <one-sentence>
    workbook: <wb_id>
    inputs: []
  carry_forward:
    constraints: []
    blocking_issues: []
  validation_commands:
    - <command>                     # required for Level 4
  status_checksum: <checksum>       # required for Level 4
  approval_record:
    path: <path>                    # required for Level 4
    date: YYYY-MM-DD
  references:
    workbook_path: <path>
    execution_spine: <path>    # if used
    specs: []                  # file paths
    contracts: []              # file paths
```

**Minimum required fields (all handoffs):**

- `from_role`, `to_role`
- `completed_step.summary`
- `completed_step.outputs` (path list; may be empty)
- `next_step.goal`
- `next_step.workbook`

**Update cadence triggers:**

- Each role handoff
- Major checkpoint completion
- Scope change or new dependency
- Validation result (pass/fail)

For Level 4 handoffs, `proposal_id`, `validation_commands`, `status_checksum`, and `approval_record`
are required. Compacted Context is a pointer/summary; full context lives in files.

### Compaction Quality Heuristics

Use these heuristics to keep compacted context useful for cold-start and handoff:

- Prefer natural breakpoints:
  - end of workbook phase,
  - end of workbook/runbook execution,
  - approval or decision gate,
  - recovery point after a blocking issue.
- Preserve only decision-bearing information:
  - what changed,
  - current state,
  - blockers,
  - immediate next action.
- Exclude low-value detail:
  - exploratory dead ends,
  - routine pass-only validations,
  - long command transcripts,
  - repeated implementation detail without decision impact.

Compact context should be deterministic enough that a new agent can resume without
reconstructing chat history.

---

## Execution Orchestration

Execution mechanics (lifecycle, triggers, state tracking) are defined in:

- `00_Admin/specs/spec_execution_orchestration.md`

---

## Relationship to Domain Capability Frameworks

ai_ops defines **how work is governed and executed**. Domain frameworks define
**what capability is being built** (for example phase/engine roadmaps, domain
spec tracks, or product capability ladders).

- **ai_ops artifacts:** workflows, workbooks, runbooks, spines, contracts, validators.
- **Domain artifacts:** capability specs, engine/module specs, domain contracts.

Recommended mapping pattern:

- domain capability definition -> `Intent`/`Meta`
- approved execution packet -> `Commitment`
- implementation and run automation -> `Execution`
- acceptance criteria and checks -> `Verification`

Keep domain semantics in domain artifacts; keep execution governance in ai_ops
artifacts.

---

## Appendix A: Reference Packs (Optional)

When materials are too large, link packs instead of inlining:

```yaml
reference_packs:
  executor_pack: packs/pack_executor_next.yaml
  human_pack: packs/pack_human_review.yaml
```

Packs are pointer YAML files listing specs/contracts/outputs/configs or human-facing summaries.

## Appendix B: Non-Goals

- Anthropomorphic agent design
- Encoding strategy inside contracts
- Embedding logic inside pipelines
