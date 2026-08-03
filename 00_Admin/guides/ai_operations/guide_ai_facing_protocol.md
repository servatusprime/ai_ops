---
title: "Reference: AI-Facing Communication Protocol"
id: ref_ai_facing_protocol_01
version: 0.1.1
status: active
created: 2026-02-20
last_updated: 2026-07-22
owner: ai_ops
license: Apache-2.0
description: >
  Uniform return format for all subagents when reporting to the primary agent.
  This protocol is invariant across rider profiles. It defines the
  structured output format that enables the primary agent to parse, relay,
  and present subagent results to the human.
related_refs:
  - 00_Admin/specs/spec_subagent_file.md
  - 02_Modules/01_agent_profiles/guide_prose_generation.md
---

<!-- markdownlint-disable MD013 -->

# Reference: AI-Facing Communication Protocol

## Purpose

Defines the uniform return format all subagents must use when reporting results to the primary agent.
This protocol is invariant across rider profiles and enables structured parsing and relay of subagent output.

## Compacted Context

All 7 ai_ops subagents report to the primary agent using the same structured
format. This protocol is uniform -- it does not vary by rider archetype,
crew preset, or canonical lane. The fixed format ensures the primary agent
can reliably parse subagent output regardless of which subagent produced
it and which rider profile was active.

The primary agent then relays findings to the human using its own relational
layer (rider-driven communication style). The subagent-to-lead-agent
channel is optimized for machines: compact, structured, and unambiguous.
The lead-agent-to-human channel is optimized for the human: styled by
the active rider's relational sliders.

---

## Protocol Format

A subagent return carries a **task-specific minimum**, not a fixed section set.
Include exactly what the task produced; omit what does not apply. Do not emit
empty placeholder sections -- an omitted section and a section reading "None"
carry the same information, and the placeholder costs tokens on every return.

Required in every return:

- **Disposition** -- one of `completed | blocked | partial | failed`.
- **Result** -- what was done or found, and the changed paths if the task wrote
  anything. Bottom line up front.
- **Evidence** -- required whenever the return makes a claim. Evidence must be
  capable of observing the claim it supports (`file:line`, command + key
  output). A claim without evidence is not acceptable.

Include only when applicable:

- **Blocker / next action** -- what prevents completion and what would resolve
  it. Omit entirely when nothing is blocked.
- **Proposals** -- out-of-scope follow-up seeds. Omit entirely when there are
  none.

Minimal example -- a read-only research return with no blockers:

```markdown
## Return: Researcher

Disposition: completed

Result: `lock_scope` has no runtime consumer; the coordination guide claims an
enforcement mechanism that does not exist.

Evidence:
- `guide_multi_agent_coordination.md:47` declares `.aiops_session/locks.yaml`
- repo-wide grep for that path returns 0 consumers
```

The maximal shape below remains available when a task genuinely produces every
part; it is an upper bound, not a required form.

---

## Section Specifications

### Status

One of four values. The primary agent uses this to determine next action.

| Value | Meaning | primary agent Action |
| --- | --- | --- |
| `completed` | Task finished successfully. All deliverables produced. | Present results to human. |
| `blocked` | Cannot proceed. Blocker requires human or primary agent input. | Present blocker to human for resolution. |
| `partial` | Some deliverables produced. Remaining work identified. | Present partial results and ask human how to proceed. |
| `failed` | Task could not be completed. Error or constraint violation. | Present failure reason to human. |

### Summary

A brief bottom-line statement. Written for the primary agent, not the human.
The primary agent will rephrase this using its relational layer when
presenting to the human.

Good: "Created 3 workbook files. Frontmatter validates. Body content
follows template. Markdownlint clean."

Bad: "I've completed the task you asked me to do! Everything looks great
and I'm happy to report that all three files were successfully created."

The summary is machine-optimized: no pleasantries, no filler, no emotional
framing. The primary agent adds those as appropriate for its rider profile.

### Deliverables

A flat list of concrete outputs. Each entry includes:

- File path (relative to repo root)
- Action taken (created, modified, deleted, moved)
- Brief content note (what the file contains or what changed)

```markdown
- `90_Sandbox/ai_workbooks/wb_example/wb_example_01.md` -- created -- workbook with 5-phase execution queue
- `00_Admin/configs/context_routing.yaml` -- modified -- added crosscheck route entry
```

### Findings

Structured per the subagent's lane. Each lane has a consistent sub-format:

**Reviewer findings:**

```markdown
- **[severity: high | medium | low]** [file:line] -- [description]
  - Classification: [code_enforced | doc_only | process_gap]
  - Disposition: [patch_now | proposal_seed | follow_on_workbook]
```

**Researcher findings:**

```markdown
- **[topic]** -- [summary of finding]
  - Source: [file path + section or URL]
  - Confidence: [high | medium | low]
  - Contradicts: [other source, if any]
```

**Linter findings:**

```markdown
- **[rule_id]** [file:line] -- [message]
  - Severity: [error | warning | info]
  - Fixable: [yes | no]
```

**Planner findings:**

```markdown
- **[phase/step]** -- [description of planned action]
  - Authority: [level 0-4]
  - Estimated scope: [files touched, complexity]
```

**Executor findings:**
Executors typically produce deliverables rather than findings. When an
executor reports findings, use the generic format:

```markdown
- **[topic]** -- [observation]
  - File: [path]
  - Action needed: [description or "none"]
```

**Closer findings:**

```markdown
- **[validation_step]** -- [pass | fail | skip]
  - Detail: [description if fail]
  - Blocker: [yes | no]
```

### Blockers

Each blocker includes what is needed to resolve it and who can resolve it.

```markdown
- [Description of blocker]
  - Needs: [specific action or information needed]
  - Resolver: [human | lead_agent | specific_subagent]
```

### Proposals

Proposal seeds for future work. These are NOT approved actions. The lead
agent presents them to the human as suggestions.

```markdown
- [Description of proposed work]
  - Rationale: [why this would be valuable]
  - Scope: [estimated effort]
  - Priority: [suggestion only -- human decides]
```

### Evidence

Traceability artifacts. At minimum, one evidence item per deliverable or
significant finding.

```markdown
- File: `path/to/file.md` -- section "## Execution Steps" -- confirms task queue structure
- Command: `markdownlint ai_ops/plugins/**/*.md` -- exit code 0, no warnings
- Diff: `path/to/file.md` lines 15-22 -- frontmatter upgraded to new schema
```

---

## Single-Agent Mode Exception (Planned)

This protocol is for subagent-to-lead-agent communication in multi-agent
mode. In single-agent mode (no subagent delegation), this section is
omitted because the acting agent communicates directly with the human.

Single-agent implementations should still preserve the same reporting
discipline (status, deliverables, findings, blockers, proposals, evidence)
but do not need the fixed "How You Report to the primary agent" prose block.

See `guide_native_command_comparison.md` for the single-agent architecture.

---

## Protocol Invariance

This protocol does NOT change when:

- A different rider archetype is applied to the subagent
- A different crew preset is selected
- The subagent is invoked from a different workflow
- The primary agent's rider profile changes

The protocol DOES change when:

- The ai_ops governance model adds new structural output requirements
  (version bump to this document)
- A new subagent role is added that requires a novel findings format
  (add a new role-specific sub-format above)

---

## Token Efficiency Notes

The protocol is designed for minimal token overhead in the subagent's
return. Approximate token costs:

| Section | Typical Tokens | Notes |
| --- | --- | --- |
| Status | 1-2 | Single word |
| Summary | 20-50 | 1-3 sentences |
| Deliverables | 10-30 per item | Path + action + note |
| Findings | 20-50 per item | Structured per role |
| Blockers | 0-30 | Omit when nothing is blocked |
| Proposals | 0-30 | Omit when there are none |
| Evidence | 10-30 per item | Path + reference |

Under the former fixed seven-section form, a typical return carried 100-300
tokens of protocol overhead, including placeholder sections for the two rows
above that are usually empty. The task-specific minimum removes that floor:
overhead scales with what the task actually produced. Structure is retained
where it earns its cost -- disposition, changed paths, and evidence -- because
the lead agent needs those to integrate results reliably.

---

## Body Text for Subagent Files

The "How You Report to the Lead Agent" section in every subagent body is
**generated**, not hand-written. `00_Admin/scripts/regenerate_profiles.py` is
the source of truth for its exact wording; it emits a short report contract
plus any per-role additions from `spec.report_contract`. Do not hand-edit
generated agent files, and do not treat the text below as a verbatim mandate --
if the two ever disagree, the generator wins and this guide is the defect.

The generated contract is equivalent to the task-specific minimum above:

```markdown
## How You Report to the Lead Agent

- Return a structured summary with outcomes, evidence, and blockers.
- Include concrete file paths and line references for findings.
- Distinguish observed facts from inferred recommendations.
```

Do not include pleasantries, emotional framing, or conversational phrasing in a
return. The lead agent handles human-facing communication; subagent output is
optimized for machine reading.
