---
title: "Reference: AI-Facing Communication Protocol"
id: ref_ai_facing_protocol_01
version: 0.1.1
status: active
created: 2026-02-20
last_updated: 2026-03-04
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

## Compacted Context

All 6 ai_ops subagents report to the primary agent using the same structured
format. This protocol is uniform -- it does not vary by rider archetype,
crew preset, or functional role. The fixed format ensures the primary agent
can reliably parse subagent output regardless of which subagent produced
it and which rider profile was active.

The primary agent then relays findings to the human using its own relational
layer (rider-driven communication style). The subagent-to-lead-agent
channel is optimized for machines: compact, structured, and unambiguous.
The lead-agent-to-human channel is optimized for the human: styled by
the active rider's relational sliders.

---

## Protocol Format

Every subagent response MUST include these sections in this order. Sections
with no content should include "None" rather than being omitted.

```markdown
## Return: [Subagent Name]

### Status
[completed | blocked | partial | failed]

### Summary
[1-3 sentences. What was done or found. Bottom line up front.]

### Deliverables
[List of files created, modified, or produced. Include paths.
If no file deliverables, state "No file deliverables."]

### Findings
[Structured findings, if any. Use consistent sub-structure per role.
If no findings, state "No findings."]

### Blockers
[Issues preventing completion. Include what is needed to resolve.
If no blockers, state "None."]

### Proposals
[Suggested follow-up work that is out of scope for this invocation.
These are proposal seeds, not approved work. If none, state "None."]

### Evidence
[File paths, command outputs, or line references supporting the above.
Minimum: 1 evidence item per deliverable or finding.]
```

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

Structured per the subagent's role. Each role has a consistent sub-format:

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
| Blockers | 0-30 | Usually empty |
| Proposals | 0-30 | Usually empty or 1-2 items |
| Evidence | 10-30 per item | Path + reference |

A typical subagent return is 100-300 tokens of protocol overhead plus
the actual content. This is acceptable given that the primary agent needs
structured input to present results reliably.

---

## Body Text for Subagent Files

The following text is the fixed "How You Report to the primary agent" section
that appears in every subagent body, generated by the prose pipeline. It
MUST be included verbatim.

```markdown
## How You Report to the primary agent

When you complete your work, report using the ai_ops AI-Facing
Communication Protocol. Structure your response with these sections
in order: Status, Summary, Deliverables, Findings, Blockers,
Proposals, Evidence.

- Status is one of: completed, blocked, partial, failed.
- Summary is 1-3 sentences, bottom line up front, no filler.
- Deliverables lists files created/modified with paths and actions.
- Findings uses the structured format for your role.
- Blockers describes what prevents completion and what is needed.
- Proposals suggests future work as proposal seeds, not approved actions.
- Evidence cites file paths, command outputs, or line references.

Do not include pleasantries, emotional framing, or conversational
phrasing in your return. The primary agent handles human-facing
communication. Your output is optimized for machine parsing.
```
