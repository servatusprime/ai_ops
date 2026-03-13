---
title: Agents Start Here
version: 3.5.0
status: active
license: Apache-2.0
last_updated: 2026-03-12
owner: ai_ops
description: Bootstrap and authority contract for AI agents operating in ai_ops.
related:
  - CONTRIBUTING.md
  - 00_Admin/guides/ai_operations/guide_workflows.md
---

<!-- markdownlint-disable MD013 MD025 -->

# Agents: Start Here

## Quick Path (Read This First)

**On first turn:** Read this file. This is the canonical bootstrap entry point.
Read `CONTRIBUTING.md` on demand for contributor policy, maintainer workflow,
or unresolved authority ambiguity.

**Mode check:** Determine whether you are operating ai_ops directly (ai_ops repo
is your target) or governing an external repo (ai_ops is your ops stack; the
target is a separate work repo). This is your most important first classification.
See Mode Detection section for the full decision table.

**Do not** scan the filesystem or infer repo purpose before completing bootstrap.

---

## Authority Quick Reference

| Level | Scope | Action |
| ----- | ----------------------------- | ------------------------------------------ |
| 0 | Read, analyze, report | Always allowed |
| 1 | Single atomic edit | Pre-authorized if in scope |
| 2 | 2-5 related changes | Confirm first |
| 3 | 6+ changes or multi-layer | Create workbook, wait for approval |
| 4 | Policies, specs, architecture | Document rationale, require human approval |

Full authority execution contract is consolidated in this document.

**Key principle:** Authority is explicit, not assumed. If uncertain, ask.

**Safe default:** If you are unsure of authority, treat it as Level 3 and ask.

### Authority Detail

Use these details when classifying non-obvious requests:

- **Level 0**: read, analyze, report only (including review reports in active
  workbundle or sandbox).
- **Level 1**: one atomic edit in explicit scope, plus obvious hygiene fixes
  (links, lint, terminology, repo structure map update).
- **Level 2**: 2-5 related edits in one scope (including simple renames and
  linked reference updates); confirm first with the requestor.
- **Level 3**: 6+ edits, multi-layer change, or multi-step resumable lane;
  includes structural reorganization and analysis that yields prioritized
  action lists; create workbook and wait for approval.
- **Level 4**: policy/spec/architecture touching scope; require explicit human
  approval with rationale before execution.

### Path-Based Authority Guard (Pre-Write)

Before any file write, classify the target path against this guard:

| Path Pattern | Minimum Authority | Required Behavior |
| --- | --- | --- |
| `00_Admin/{policies,specs}/**`, `AGENTS.md`, `CONTRIBUTING.md` | Level 4 | Stop; require explicit human approval. |
| `.ai_ops/workflows/**` | Level 4 | Stop; require explicit approval evidence before edits. |
| `00_Admin/configs/**` | Level 4 | Stop; require explicit human approval. |
| `00_Admin/guides/**` | Level 3 | Use approved workbook scope; do not direct-edit outside scope. |
| `90_Sandbox/**` | Level 1-2 | Allowed when in-scope and request-aligned. |
| `.ai_ops/local/**` | Level 1 | Machine-local work state; update freely when directed by /work or /closeout. Never commit. |

If a path does not match, default to higher governance and ask.

## Agent Decision Tree

```text
START: Work identified

Is this reading/analysis only?
 YES -> Proceed (Level 0)
 NO  ->

Is this single atomic edit in pre-authorized path?
 YES -> Proceed, document (Level 1)
 NO  ->

Is this 2-5 related changes, same scope?
 YES -> Confirm first (Level 2)
 NO  ->

Is this 6+ changes OR multi-layer?
 YES -> Create workbook (Level 3)
 NO  ->

Does this affect policies/specs/architecture?
 YES -> Document rationale, wait (Level 4)
```

## First-Turn Guardrails

- Do not scan the filesystem before reading this file.
- Do not infer repo purpose from directory names.
- Only perform wide scans when explicitly requested.
- If you started scanning before bootstrap, stop, note the violation, and restart.
- Mid-session rebootstrap: re-read this file (Quick Path only).
- Treat questions as questions: answer first. Do not execute edits unless the
  user explicitly asks for action.
- A question about what should change is not authorization to change it.

---

## Red Flags Requiring Workbook

If a response implies multi-phase execution, broad remediation, or workbook-
sized scope, stop and apply this Red Flags gate.

Terminology guardrail: use **work proposal** (not "implementation plan") for Level 4 governance changes.

Common red flags:

- "Here are commands/scripts to run..."
- "I can implement these fixes quickly..."
- "Phase 1 / Phase 2 / Phase 3..."
- "I found N issues, here is a broad fix list..." (especially N > 5)
- "Analysis suggests a prioritized remediation list..."
- Changes span 3+ directories or can fail partway and require resumption
- You expect a status checkpoint question ("what is the status?") before finish

---

## Self-Check Before Acting

Before proposing actions, verify:

- [ ] I identified the authority level (0-4).
- [ ] I followed the decision tree.
- [ ] If Level 3+, I am proposing workbook execution, not direct edits.
- [ ] If Level 4, I documented rationale and am waiting for explicit approval.
- [ ] I am not presenting multi-step implementation as ad-hoc "quick wins".
- [ ] I am not prescribing command sequences for workbook-sized work.

## Approval Scope Rule

When a Work Proposal, Workbook, or Phase is approved, that approval authorizes
all actions within approved scope. If scope changes, stop and ask.

Workbook creation approval does not authorize workbook execution. Treat these
as separate gates.

## Pre-Authorized Actions

Agents may perform without extra confirmation when scope permits:

- read anywhere
- write in `90_Sandbox/**`
- update `<git_root>/repo_structure.txt`
- edit files explicitly in approved workbook/workbundle scope
- update `.ai_ops/local/work_state.yaml` when directed by /work, /closeout, or approved workbook scope
- auto-fix YAML, links, lint, and terminology drift

If uncertain, ask before writing.

Pre-authorized logs:

- Update `00_Admin/logs/log_workbook_run.md` and workbook/workbundle logs when
  required by active execution artifacts.

## Commit/Push Gate

Before commit/push for Level 3+ work:

1. Provide change summary (files touched, key edits, validation results).
2. Obtain explicit requestor approval.
3. Record approval in `00_Admin/logs/log_workbook_run.md`.

Level 2 changes should also use this gate when scope is non-trivial or the
requestor asks for explicit review before commit/push.

## Request Clarification Gate

If a request is vague, ask for:

- desired outcome and deliverable
- scope boundaries (in/out)
- target artifact type
- constraints
- success criteria

If scope expands during execution, stop and reclassify authority.

---

## Mode Detection

| Target | Mode | Logic |
| --------------- | -------------- | ------------------------------------------------------------------------- |
| ai_ops itself | **Direct** | `AGENTS.md` is in the root of the repo you are directly operating. |
| External repo | **Governed** | ai_ops is an external ops stack; workspace topology names a target repo. |
| No ai_ops found | **Standalone** | No `AGENTS.md` with ai_ops structure can be resolved. |

**Rule:** Determine target repo root first, then resolve mode from workspace
topology (see Workspace Topology section below).

Fallback if manifest is missing/conflicting:

1. Prefer `ai_ops` governance files when available.
2. Follow `AGENTS.md` as minimum bootstrap baseline; load `CONTRIBUTING.md`
   when contributor policy details are required.
3. Pause and ask if mode/scope is still ambiguous.

Minimum governed-mode verification snippet:

- confirm target repo root and active artifact path
- confirm validator/lint command path for target repo
- confirm sandbox destination and no cross-repo write drift

---

## Level 0-2 Early Exit

If you are recentering mid-session or doing Level 0-2 work:

1. Re-read this file (Quick Path section).
2. Read `.ai_ops/local/work_state.yaml` for active work context (`work_context.active_artifacts`).
   Absence = no active work; not an error. If different than expected, notify requestor.
3. If authority remains Level 0-2 and no workbook red flags are triggered, stop here and proceed.

**Early Exit Marker (Level 0-2):** You may stop at this section for Level 0-2
execution. Continue to "Bootstrap Sequence (Full)" only for Level 3+ work.

Full bootstrap (reading policies, specs, guides) is only required for Level 3+ work.

**Active Artifacts Authority:** `.ai_ops/local/work_state.yaml` is the single source of truth for
`active_artifacts`. This file is machine-local and gitignored; absence means no active work.
Governed repos do not mirror this section. See `work_context.updated_at` timestamp for freshness.

---

## Axes At A Glance

ai_ops uses two axis groups. Keep both visible while choosing artifacts and reporting status.

- Organizing axes: `Intent -> Commitment -> Execution -> Verification` (+ Meta governance)
- Quality axes: `Clarity`, `Thrift`, `Context`, `Governance`

Canonical definition:
`00_Admin/guides/ai_operations/guide_ai_operations_stack.md`

### Organizing Axes

ai_ops work flows through five organizing axes: Intent, Commitment, Execution,
Verification, and Meta. The four reference-flow axes run left to right; Meta is
cross-cutting governance above the flow. All artifacts map to exactly one primary axis.

| Axis | Purpose | Primary Artifacts | Reference |
| --- | --- | --- | --- |
| Intent | Describe desired outcomes and strategies | Workflows | Workflows define what should happen |
| Commitment | Freeze approved scope for execution | Workbooks, Execution Spines, Workprograms | Locked plan with specific parameters |
| Execution | Define how work is carried out | Runbooks, Pipelines, Tools, Modules | Reusable implementations |
| Verification | Define correctness and safety gates | Contracts, Validators, Logs | Binary pass/fail checks and audit trails |
| Meta | Explain and govern the system | Policies, Guides, Specs, Vocabulary, Catalogs | Cross-cutting rules and reference data |

### ai_ops Standard Artifact Inventory

Use this table to classify an artifact before writing or classifying a path.

| Artifact | Primary Axis | Durability | Scope Tier |
| --- | --- | --- | --- |
| Workflow | Intent | persistent | program |
| Work Proposal | Intent | run-scoped | program |
| Workprogram | Commitment | run-scoped | program |
| Workbundle | Commitment | run-scoped | bundle |
| Workbook | Commitment | run-scoped | book |
| Execution Spine | Commitment | run-scoped | bundle |
| Runprogram | Execution | persistent | program |
| Runbundle | Execution | persistent | bundle |
| Runbook | Execution | persistent | book |
| Pipeline | Execution | persistent | book |
| Module | Execution | persistent | support |
| Tool / Script | Execution | persistent | support |
| Contract | Verification | persistent | support |
| Validator | Verification | persistent | support |
| Log | Verification | run-scoped | support |
| Compacted Context | Meta | run-scoped | support |
| Scratchpad | Meta | run-scoped | support |
| Bundle README | Meta | persistent | support |
| README.md | Meta | persistent | support |
| AGENTS.md | Meta | persistent | support |
| HUMANS.md | Meta | persistent | support |
| CONTRIBUTING.md | Meta | persistent | support |
| Guide | Meta | persistent | support |
| Spec | Meta | persistent | support |
| Policy | Meta | persistent | support |
| Template | Meta | persistent | support |
| Catalog | Meta | persistent | support |

**Durability:** `run-scoped` = ephemeral per-execution artifact; `persistent` = standing reference artifact.

**Key principles:**

- Mixed responsibility is prohibited. Each artifact serves exactly one primary axis.
- Reference direction flows left to right: Intent -> Commitment -> Execution -> Verification.
- Meta may inform any axis. Authority increases downstream.

### Quality Axes

Every artifact and operation is evaluated against four quality axes.

| Axis | Purpose | Interpretation | Scope | Quick-Scan Check |
| --- | --- | --- | --- | --- |
| **Clarity** | Cold-start readability | No inference required; inputs/steps/outputs explicit | Local | Can a new reader follow without external context? |
| **Thrift** | Efficient required outcome | Minimum cost including execution burden, read hops, retracing | Local + Global | Is each element necessary? Are there avoidable bounces? |
| **Context** | Reliable resumption/handoff | Work restarts from files; handoff state explicit | Global (task chain) | Can a different agent resume from artifacts alone? |
| **Governance** | Authority and gate discipline | Authority boundaries explicit, traced, and enforced | Global (scope crossing) | Are decision gates in the right place? Is authority clear? |

### Level 3+ Work

Complete the full Bootstrap Sequence below before executing.

---

## Bootstrap Sequence (Full)

Complete this sequence for Level 3+ work or first-time repo onboarding.

### Minimum Viable Bootstrap (Role-Based)

For narrow roles, use minimum bootstrap instead of full sequence:

| Role | Use case | Minimum reading |
| ------------------- | ------------------- | ------------------------------------------------ |
| Crosscheck reviewer | Review only | This file -> `peer_review_template.md` |
| Validator | Validate + report | This file -> `rb_repo_validator_01.md` |
| Recentering agent | Refocus mid-session | This file (Quick Path only) |

If authority is unclear after minimum bootstrap, read `CONTRIBUTING.md` and
pause to ask before acting.

If work reclassifies to Level 3+ mid-session, resume at Step 1 below before continuing.

### Step 1: Read Entry Points

- Read this file (`AGENTS.md`) first.
- Read `CONTRIBUTING.md` only when contributor policy, maintainer workflow, or
  authority ambiguity requires it.
- For external repos or if the user requests a runbook, use
  `00_Admin/runbooks/rb_bootstrap.md` and avoid duplicate reads.
- Machine-specific overrides (modality, work_repos) live in
  `.ai_ops/local/config.yaml` (gitignored; absence is normal for a fresh clone).

### Step 2: Apply Authority Rules

Read and apply this document's authority controls:

- Authority Quick Reference
- Agent Decision Tree
- Selfcheck Loop (Completion Gate)

### Step 3: Follow Required Reading (Level 3+ Only)

1. **Global rules:** `00_Admin/policies/README.md` -> `00_Admin/specs/README.md`
2. **Domain knowledge:** `00_Admin/guides/README.md` (consult by task; avoid bulk reads)
3. **Task-specific:** Active workbook context, module docs

### Step 4: Bootstrap Verification (Level 3+ Only)

Before executing Level 3+ work, confirm:

- [ ] I understand authority levels 0-4
- [ ] I know canonical vocabulary (workbook vs workbundle vs workprogram)
- [ ] I can navigate the decision tree
- [ ] I understand 90_Sandbox (experimental) vs 00_Admin (canonical)

---

## Workflow Source Contracts

Workflow source contracts live in `.ai_ops/workflows/`. Each command has one
workflow file.

| Command | Default role | Purpose |
| --------------- | ------------------------ | ------------------------------------------ |
| /work | Coordinator -> Executor | Establish work context, execute tasks |
| /work_status | Coordinator | Summarize active work and blockers |
| /work_savepoint | Executor | Commit + push savepoint, then end session |
| /harvest | Coordinator -> Executor | Harvest/prune artifacts |
| /crosscheck | Validator | Review and report only |
| /health | Validator | Report-only repo health check |
| /closeout | Executor | Finalize and archive work |
| /lint | Validator | Run configured validators and linters |
| /bootstrap | Coordinator | Orientation and readiness |
| /scratchpad | Executor | Create session notes |
| /customize | Coordinator -> Executor | Configure preferences |
| /profiles | Coordinator -> Executor | Manage rider/crew profile contracts |

If command folders are not installed for your tool, read `.ai_ops/workflows/<command>.md` directly.

---

## Role Reference

Role sequence flows left to right. Coordinator repeats at each cycle boundary.
Builder is invoked as needed -- not every run requires a dedicated Builder step.

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "darkMode": true,
    "background": "#111111",
    "primaryColor": "#0d0b09",
    "primaryTextColor": "#FFD85A",
    "primaryBorderColor": "#FF9F00",
    "lineColor": "#FF9F00",
    "textColor": "#FFD85A",
    "mainBkg": "#0d0b09",
    "clusterBkg": "#12110f",
    "clusterBorder": "#8A4F00",
    "titleColor": "#FFE680",
    "edgeLabelBackground": "#0d0b09"
  },
  "themeCSS": ".edgeLabel rect, .labelBkg { fill: #0d0b09 !important; } .edgeLabel text, .edgeLabel span { fill: #FFD85A !important; color: #FFD85A !important; }"
}}%%

flowchart LR
  CO[Coordinator]
  EX[Executor]
  BL[Builder]
  VA[Validator]
  CO2[Coordinator]

  CO --> EX --> BL --> VA --> CO2
  CO2 -. next cycle .-> EX

  classDef node fill:#0d0b09,stroke:#FF9F00,color:#FFD85A,stroke-width:2px

  class CO,EX,BL,VA,CO2 node

  linkStyle 0,1,2,3 stroke:#FF9F00,stroke-width:2px
  linkStyle 4 stroke:#FF9F00,stroke-width:2px,stroke-dasharray:6 4
```

| Role | When Active | Primary Duties | Default Model Level | Notes |
| --- | --- | --- | --- | --- |
| Coordinator | Start, between phases, at end | Plan scope, select workflows, manage handoffs, approve gates | Level 2 | Level 3 for L4 or architectural decisions |
| Executor | Per work step | Execute current step, maintain logs, flag blockers | Level 1 or 2 | Primary execution lane. Level 1 for bounded tasks; Level 2 when judgment required |
| Builder | When tooling needed | Write tools, implement automation, update configs | Level 2 | Spawned as needed; may be skipped in execution-only runs |
| Validator | After each phase | Review outputs against contracts, issue pass/fail verdict | Level 2 | Level 3 for Elevated Crosscheck |

**Agent topology:**

- **Single agent:** one agent cycles through all roles in sequence. This is the default mode. The agent you interact with directly is the *primary agent*; it holds all four roles internally.
- **Multi-agent:** Coordinator (primary agent) spawns dedicated *subagents*, each pre-assigned a role. Subagent definitions live in `plugins/ai-ops-governance/agents/` -- six generated files (`ai-ops-planner.md`, `ai-ops-executor.md`, `ai-ops-reviewer.md`, `ai-ops-researcher.md`, `ai-ops-closer.md`, `ai-ops-linter.md`). These files are generated by `/profiles` + `regenerate_profiles.py`; do not hand-edit them.
- **Profiles and topology:** `/profiles` configures your *primary agent's* behavioral posture. Subagent behavior is governed by their definition files and the `role_assignments` frontmatter in the active workbook. Lead-agent profile payloads are written to `02_Modules/01_agent_profiles/generated/lead_agent_profile_context.md`.

---

## AI Model Level Reference

Model level refers to LLM reasoning depth -- not authority level (0-4).
Use this table to select an AI model level for each role assignment.

| Level | Depth | Typical Tasks | Recommended Role |
| --- | --- | --- | --- |
| 1 | Low | Bounded extraction, formatting, simple edits | Executor (bounded execution), Builder (routine tasks) |
| 2 | Medium | Scoped implementation, multi-step work | Executor (judgment needed), Builder, Validator (standard), Coordinator (standard) |
| 3 | High | Architecture, governance, precedent-setting | Coordinator (L4 decisions), Validator (Elevated Crosscheck) |

**Notes:**

- Default to Level 2 when unsure. Upgrade to Level 3 only for architectural decisions or Elevated Crosscheck.
- Level 1 is appropriate only for fully bounded, deterministic tasks with no judgment required.
- Model level is set per role in the workbook `role_assignments` frontmatter field.

---

## Agent Profiles

**Primary agent profiles** configure how your primary agent approaches work -- the
agent you interact with directly. `/profiles` sets the active named preset. Without
a named profile, the primary agent runs in default out-of-box posture.

**Subagent profiles** are different. Each subagent's definition file
(`plugins/ai-ops-governance/agents/<name>.md`) sets its role, permission mode,
and parameter defaults. The active workbook's `role_assignments` frontmatter field
maps roles to model levels for the current run. Rider personality is less visible
to you when applied to subagents -- behavioral differences primarily surface through
the primary agent you interact with.

**Do not hand-edit** files in `plugins/ai-ops-governance/agents/`. These are
generated. Use `/profiles` to modify profile source data, then regenerate.

Each profile assigns a rider archetype and sets behavioral parameters (0-100 scale):

### Profile Catalog

| Profile | Rider | Autonomy | Conservatism | Initiative | Deference | Permission Mode | Max Turns |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ai-ops-planner | logike | 55 | 75 | 30 | 60 | plan | 20 |
| ai-ops-executor | forge | 75 | 45 | 45 | 45 | default | 30 |
| ai-ops-reviewer | anchor | 25 | 90 | 20 | 80 | plan | 10 |
| ai-ops-researcher | scout | 70 | 60 | 70 | 55 | plan | 30 |
| ai-ops-closer | forge | 75 | 80 | 20 | 45 | default | 30 |
| ai-ops-linter | anchor | 70 | 90 | 20 | 80 | default | 30 |

### Parameter Glossary

| Parameter | High (near 100) | Low (near 0) |
| --- | --- | --- |
| Autonomy | Acts without waiting for confirmation | Asks before acting |
| Conservatism | Sticks strictly to stated scope | Open to expanding scope |
| Initiative | Proactively surfaces gaps and follow-on items | Executes only what is asked |
| Deference | Follows prior instructions closely | Applies more independent judgment |

### Riders (Behavioral Archetypes)

| Rider | Characteristic |
| --- | --- |
| logike | Methodical, structured -- planning and scoping focus |
| forge | Action-oriented -- execution, build, and delivery focus |
| anchor | Conservative, thorough -- review, gate, and correctness focus |
| scout | Curious, exploratory -- research and discovery focus |

### Profile to Role Mapping

| Profile | Typical Role Assignment | Notes |
| --- | --- | --- |
| ai-ops-planner | Coordinator | Planning and scoping focus |
| ai-ops-executor | Executor, Builder | Primary execution lane |
| ai-ops-reviewer | Validator | Structured review and crosscheck |
| ai-ops-researcher | Coordinator (research phase) | Discovery-oriented coordinator |
| ai-ops-closer | Executor | Specialized for closeout workflow (/closeout) |
| ai-ops-linter | Validator | Specialized for lint/validation automation (/lint) |

---

## Context Management

Compacted Context is the single shared run state for all participants. It lives as a repo
artifact -- in the workbundle README or workbook body -- not in any agent's memory. Every
participant reads from and writes to the same artifact, ensuring full transparency,
enabling cold-start resumption and post-execution review without requiring chat history.

### Shared Access

```mermaid
%%{init: {'theme':'base','themeVariables': {
  'darkMode': true,
  'background': '#111111',
  'primaryColor': '#0d0b09',
  'primaryTextColor': '#FFD85A',
  'primaryBorderColor': '#FF9F00',
  'lineColor': '#FF9F00',
  'textColor': '#FFD85A',
  'mainBkg': '#0d0b09',
  'clusterBkg': '#12110f',
  'clusterBorder': '#8A4F00',
  'titleColor': '#FFE680',
  'edgeLabelBackground':'#12110f'
}, 'themeCSS': '.edgeLabel rect, .labelBkg { fill: #12110f !important; } .edgeLabel text, .edgeLabel span { fill: #FFD85A !important; color: #FFD85A !important; }'}}%%
flowchart TB
  subgraph actors ["Participants"]
    direction LR
    CO[Coordinator]
    EX[Executor]
    BL[Builder]
    VA[Validator]
    HR[Human Reviewer]
  end

  subgraph state ["Shared State"]
    direction TB
    CC[Compacted Context]
  end

  subgraph outcomes ["Outcomes"]
    direction LR
    RS[Cold-Start Resume]
    PER[Post-Execution Review]
  end

  CO -- "reads and writes" --> CC
  EX -- "reads and writes" --> CC
  BL -- "reads and writes" --> CC
  VA -- "reads and writes" --> CC
  HR -. "reads" .-> CC

  CC --> RS
  CC --> PER

  classDef tier fill:#12110f,stroke:#8A4F00,color:#FFE680,stroke-width:2.2px
  classDef node fill:#0d0b09,stroke:#FF9F00,color:#FFD85A,stroke-width:2px
  classDef core fill:#1b1308,stroke:#FFB347,color:#FFE680,stroke-width:2.4px

  class actors,state,outcomes tier
  class CO,EX,BL,VA,HR,RS,PER node
  class CC core

  linkStyle default stroke:#FF9F00,stroke-width:2px,color:#FFD85A
  linkStyle 4 stroke:#FF9F00,stroke-width:2px,color:#FFD85A,stroke-dasharray:6 4
```

### Storage Locations

| Level | Location | Notes |
| --- | --- | --- |
| Book level | Workbook body (standalone run) | Use when no bundle coordinates the run |
| Bundle level | Workbundle README.md | Shared across all books in the bundle |
| Local only | .ai_ops/local/work_state.yaml (gitignored) | Machine-local; never committed; not a shared artifact |

### Update Cadence

Update compacted context at every:

1. Role handoff (Coordinator to Executor, Executor to Validator, etc.)
2. Phase completion (end of each workbook phase)
3. Scope change or new dependency discovered
4. Validation result (pass/fail finding requiring action)

---

## Response Thrift

Keep outputs efficient without sacrificing correctness:

- Be concise by default; expand when complex or requested
- Prefer pointers to canonical docs over recreating content
- Optimize for clarity and actionability
- Do not increase internal cycle burden in touched docs without explicit
  justification and landing-zone mapping

## Thriftiness Pass

If `customizations.review_preferences.thrift_pass` is enabled in
`.ai_ops/local/config.yaml`:

- `local`: limit to files touched in current execution
- `meta`: broad refactors; log in workbundle scratchpad before proposing a
  dedicated workbook

## Selfcheck Loop (Completion Gate)

Before reporting "done" on any workbook or multi-step task, run a selfcheck loop:

```text
LOOP until (clean OR blocked OR iterations >= 3):
  1. Re-read all tasks from beginning
  2. For each task, verify: completed? outputs exist? no regressions?
  3. Run thrift/streamlining pass on touched docs:
     - no unnecessary duplication
     - no dead references
     - no avoidable cross-document hop increases
  4. If gaps found -> fix and increment iteration
  5. If blocked -> record blocker and exit loop
  6. If clean -> exit loop
END LOOP
```

**Exit conditions:**

- **Clean:** All tasks verified, no gaps. Report completion.
- **Blocked:** Issue cannot be resolved without user input. Report blocker.
- **Max iterations (3):** Persistent issues remain. Report partial completion with remaining gaps.

**Never report "done" after a single pass.** The first pass often misses edge cases.

---

## Workspace Topology

Machine-readable workspace defaults. Per-machine overrides (modality, work_repos)
live in `.ai_ops/local/config.yaml` (gitignored; absent on fresh clone = no override).

```yaml
workspace:
  workspace_root: ".."          # parent of ai_ops/ in your workspace
  ops_stack_root: "ai_ops"      # path to this ai_ops clone
  setup_mode: direct            # direct | governed | standalone
  work_repos: []                # populated per machine via /ai_ops_setup
  resource_repos: []
  directory_overrides:
    sandbox_dir_name: 90_Sandbox
    trash_dir_name: 99_Trash
```

**Fallback rule:** When no `.ai_ops/local/config.yaml` is present, use the
defaults above. Agents MUST NOT halt on missing local config.

---

## Folder Structure

| Folder | Purpose |
| --------------- | ------------------------------------------------------- |
| `00_Admin/` | Governance, policies, guides, specs, runbooks, logs |
| `01_Resources/` | Shared templates, prompts, and reference data |
| `02_Modules/` | Reusable capabilities (code, docs, tests) |
| `90_Sandbox/` | Temporary workbundles and experiments (manually purged) |
| `99_Trash/` | Staged deletions and deprecated files (manually purged) |

Detailed structure: [guide_repository_structure.md](00_Admin/guides/architecture/guide_repository_structure.md)

## Quick References

- Guides: [00_Admin/guides/README.md](00_Admin/guides/README.md)
- Policies: [00_Admin/policies/README.md](00_Admin/policies/README.md)
- Vocabulary: [guide_ai_ops_vocabulary.md](00_Admin/guides/ai_operations/guide_ai_ops_vocabulary.md)
- Structure: `<git_root>/repo_structure.txt` (use when task needs navigation)

---

## Canonical References

- Terminology: `00_Admin/guides/ai_operations/guide_ai_ops_vocabulary.md`
- Contributor policy: `CONTRIBUTING.md`
- Workflows: `00_Admin/guides/ai_operations/guide_workflows.md`
- Bootstrap algorithm: `00_Admin/guides/architecture/guide_bootstrap_algorithm.md`
