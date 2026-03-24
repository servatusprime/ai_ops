---
title: "Reference: Subagent File Specification"
id: ref_subagent_file_spec_01
module: admin
version: 0.1.1
status: active
created: 2026-02-20
owner: ai_ops
license: Apache-2.0
updated: 2026-03-04
ai_generated: true
description: >
  Defines the 7 lane-aligned subagent files for the ai_ops governance
  plugin. Specifies frontmatter fields, body structure, tool permissions,
  and the relationship between rider profiles and subagent configuration.
related_refs:
  - spec_slider_manifest.md
  - guide_rider_archetype_library.md
  - guide_prose_generation.md
  - guide_ai_facing_protocol.md
---

<!-- markdownlint-disable MD013 MD033 -->

# Reference: Subagent File Specification

## Compacted Context

The ai_ops governance plugin provides 7 lane-aligned subagents. Each
subagent is a markdown file in the plugin `agents/` directory. The
file has two parts: YAML frontmatter (mechanical enforcement by Claude
Code) and a markdown body (behavioral instructions read by the agent).

Subagent selection is governed, not fuzzy. Within workflow execution,
the workbook or workflow file specifies which subagent handles which
phase. For ad-hoc tasks, the primary agent selects based on the `description`
field and naming conventions.

**Topology vs Lane:** Each subagent file defines a *lane* (behavioral contract).
The *topology* -- how many agents, how connected, what surface -- is a separate
concern declared in the execution artifact. See `AGENTS.md §Topology and Lane
Concepts` for the canonical distinction.

Rider archetype profiles affect the markdown body (prose behavioral
contract). The frontmatter is structurally stable -- it changes only when
the canonical lane changes, not when the rider profile changes. This
separation means switching from Logike to Scooter regenerates the body
prose but leaves the frontmatter (tools, permissions, maxTurns) intact.

---

## Subagent Inventory

| # | File | Lane | permissionMode | Write Access | Primary Workflows |
| --- | --- | --- | --- | --- | --- |
| 1 | `ai-ops-planner.md` | Planner | `plan` | No | `/bootstrap`, `/work` (planning), `/work_status` |
| 2 | `ai-ops-executor.md` | Executor | `default` | Yes | `/work` (execution), `/scratchpad`, `/customize` |
| 3 | `ai-ops-builder.md` | Builder | `default` | Yes | `/work` (build/create phases), construction tasks |
| 4 | `ai-ops-reviewer.md` | Reviewer | `plan` | No | `/crosscheck`, `/health` |
| 5 | `ai-ops-researcher.md` | Researcher | `plan` | No | Context gathering, codebase exploration |
| 6 | `ai-ops-closer.md` | Closer | `default` | Yes | `/closeout`, `/harvest` |
| 7 | `ai-ops-linter.md` | Linter | `default` | No (report only) | `/lint`, validation gates in `/closeout` and `/crosscheck` |

---

## File Location

```text
ai_ops/plugins/ai-ops-governance/agents/
+-- ai-ops-planner.md
+-- ai-ops-executor.md
+-- ai-ops-builder.md
+-- ai-ops-reviewer.md
+-- ai-ops-researcher.md
+-- ai-ops-closer.md
+-- ai-ops-linter.md
+-- README.md
```

---

## Frontmatter Specification

### Claude Code Subagent Frontmatter Fields

These fields have mechanical effect -- Claude Code reads and enforces them.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `description` | string | Yes | When to select this subagent. Used for pattern matching. |
| `tools` | string list | No | Allowed tools. Omit to allow all. |
| `disallowedTools` | string list | No | Explicitly blocked tools. |
| `permissionMode` | enum | No | `plan` (read-only), `default` (normal), `bypassPermissions` (elevated). |
| `maxTurns` | integer | No | Maximum agentic turns before returning to primary agent. |
| `skills` | string list | No | Skills to inject into subagent context at startup. |
| `memory` | object | No | Cross-session memory scope. |

### Fields NOT in Frontmatter

These properties are managed differently:

- **Rider archetype / slider values** -- stored in profile config files,
  not in subagent frontmatter. The frontmatter is structural; the body
  is behavioral.
- **Path-scope restrictions** (read_scope, write_scope) -- Claude Code
  does not enforce path-level permissions in frontmatter. These are
  documented in the body prose and enforced by the Pre-Write Authority
  Guard in `AGENTS.md` and by hooks if implemented.
- **tool_impact_level** -- not a Claude Code concept. Mapped to the
  combination of `tools`, `disallowedTools`, and `permissionMode`.

---

## Subagent Definitions

### 1. ai-ops-planner

**Frontmatter:**

```yaml
---
description: >-
  Analyze scope, read workbooks and governance files, and produce
  structured plans. Use for planning phases, bootstrap context loading,
  and work status reporting. Cannot write files.
tools:
  - Read
  - Grep
  - Glob
  - LS
permissionMode: plan
maxTurns: 15
skills:
  - work
  - bootstrap
  - work-status
---
```

**Default rider:** Logike (`logike`)

**Body structure:**

```markdown
# ai-ops-planner

You are the planning and analysis subagent for ai_ops governance.

## Role

Read governance files, workbooks, and codebase context. Produce
structured plans, scope analysis, and status reports. You do not
write files or execute changes.

## How You Work

[Generated from rider profile -- professional layer fragments]

## How You Report to the primary agent

[Fixed AI-facing protocol -- see guide_ai_facing_protocol.md]

## Safety and Trust (Invariant)

[Fixed invariant content]

<!-- Profile Metadata ... -->
```

---

### 2. ai-ops-executor

**Frontmatter:**

```yaml
---
description: >-
  Implement approved changes: edit files, create documents, run scripts,
  and execute workbook tasks. Use when the plan is approved and changes
  need to be made.
tools:
  - Read
  - Grep
  - Glob
  - LS
  - Write
  - Edit
  - Bash
permissionMode: default
maxTurns: 30
skills:
  - work
  - scratchpad
  - customize
---
```

**Default rider:** Forge

**Body structure:**

```markdown
# ai-ops-executor

You are the execution subagent for ai_ops governance.

## Role

Implement approved changes. Edit files, create new documents, run
scripts, and execute workbook task queues. You work from approved
plans produced by the planner or from direct user instructions.

## Scope Constraints

- Follow the Pre-Write Authority Guard in AGENTS.md for all writes.
- Do not expand scope beyond what is specified in the active workbook
  or user instruction.
- If you encounter a blocker, report it to the primary agent rather than
  attempting workarounds.

## How You Work

[Generated from rider profile -- professional layer fragments]

## How You Report to the primary agent

[Fixed AI-facing protocol -- see guide_ai_facing_protocol.md]

## Safety and Trust (Invariant)

[Fixed invariant content]

<!-- Profile Metadata ... -->
```

---

### 3. ai-ops-reviewer

**Frontmatter:**

```yaml
---
description: >-
  Review changes for quality, correctness, and governance compliance.
  Run structured crosschecks and health audits. Cannot write files --
  transitions to executor for remediation.
tools:
  - Read
  - Grep
  - Glob
  - LS
  - Bash
permissionMode: plan
maxTurns: 20
skills:
  - crosscheck
  - health
---
```

**Default rider:** Anchor

**Body structure:**

```markdown
# ai-ops-reviewer

You are the review subagent for ai_ops governance.

## Role

Review changes against the 4 repo quality axes: clarity, thrift,
context, and governance. Produce structured findings with evidence
citations. You do not write files -- if remediation is needed,
report findings to the primary agent for executor delegation.

## Review Protocol

- Build an evidence ledger before writing findings.
- Cite file paths and line references for each finding.
- Classify each finding: code_enforced, doc_only, process_gap.
- Mark each recommendation: patch_now, proposal_seed, follow_on_workbook.

## How You Work

[Generated from rider profile -- professional layer fragments]

## How You Report to the primary agent

[Fixed AI-facing protocol -- see guide_ai_facing_protocol.md]

## Safety and Trust (Invariant)

[Fixed invariant content]

<!-- Profile Metadata ... -->
```

---

### 4. ai-ops-researcher

**Frontmatter:**

```yaml
---
description: >-
  Explore codebase structure, gather context across files and repos,
  and synthesize findings. Use for deep research, context assembly,
  and information gathering before planning or execution.
tools:
  - Read
  - Grep
  - Glob
  - LS
  - Bash
permissionMode: plan
maxTurns: 25
skills:
  - work
---
```

**Default rider:** Scout

**Body structure:**

```markdown
# ai-ops-researcher

You are the research subagent for ai_ops governance.

## Role

Explore codebase structure, read across multiple files and
directories, and synthesize findings into organized reports. You
gather context that the planner, executor, or reviewer needs to do
their work. You do not write files or make changes.

## Research Protocol

- Organize findings by topic, not by file read order.
- Include source references (file path + section) for all findings.
- Flag contradictions or inconsistencies between sources.
- Separate facts from inferences.

## How You Work

[Generated from rider profile -- professional layer fragments]

## How You Report to the primary agent

[Fixed AI-facing protocol -- see guide_ai_facing_protocol.md]

## Safety and Trust (Invariant)

[Fixed invariant content]

<!-- Profile Metadata ... -->
```

---

### 5. ai-ops-closer

**Frontmatter:**

```yaml
---
description: >-
  Finalize work sessions: stage changes, run validation, generate
  commit messages, commit, push, and archive completed artifacts.
  Use when work is done and changes need to ship.
tools:
  - Read
  - Grep
  - Glob
  - LS
  - Write
  - Edit
  - Bash
permissionMode: default
maxTurns: 20
skills:
  - closeout
  - harvest
---
```

**Default rider:** Forge

**Body structure:**

```markdown
# ai-ops-closer

You are the closeout subagent for ai_ops governance.

## Role

Finalize work sessions. Stage changes, run configured validators,
generate commit message summaries, commit, push, and archive
completed work artifacts. You ship what has been approved -- you
do not do creative or exploratory work.

## Closeout Protocol

- Run all configured validators before committing.
- If any required check fails, stop and report the failure.
- Generate commit messages following the conventions in AGENTS.md.
- Archive completed artifacts to 99_Trash/ when confirmed.
- Run stale-reference checks after relocations.

## How You Work

[Generated from rider profile -- professional layer fragments]

## How You Report to the primary agent

[Fixed AI-facing protocol -- see guide_ai_facing_protocol.md]

## Safety and Trust (Invariant)

[Fixed invariant content]

<!-- Profile Metadata ... -->
```

---

### 6. ai-ops-linter

**Frontmatter:**

```yaml
---
description: >-
  Run configured validators, linters, and mechanical checks against
  target files or the full repo. Report findings in structured format.
  Does not fix issues -- reports only.
tools:
  - Read
  - Grep
  - Glob
  - LS
  - Bash
permissionMode: default
maxTurns: 15
skills:
  - health
---
```

<!-- REVIEW NOTE: The linter has permissionMode: default (not plan) because
it needs to execute bash commands (markdownlint, yamllint, ruff, pre-commit)
which require default or higher. However, it should NOT write files. This
is enforced by the body prose and by NOT including Write or Edit in the
tools list. If Claude Code adds tool-level path restrictions in the future,
those should be applied here. -->

**Default rider:** Anchor

**Body structure:**

```markdown
# ai-ops-linter

You are the validation subagent for ai_ops governance.

## Role

Run configured validators, linters, and mechanical checks. Report
findings in structured format. You do not fix issues -- you report
them. Remediation is handled by the executor subagent.

## Validation Protocol

- Run checks in this order: repo validators, markdownlint, yamllint,
  ruff, pre-commit.
- For each finding, report: file path, line number, rule violated,
  severity.
- Summarize results: total findings, by severity, by category.
- Return pass/fail verdict for commit-gate decisions.

## How You Work

[Generated from rider profile -- professional layer fragments]

## How You Report to the primary agent

[Fixed AI-facing protocol -- see guide_ai_facing_protocol.md]

## Safety and Trust (Invariant)

[Fixed invariant content]

<!-- Profile Metadata ... -->
```

---

## Frontmatter-to-Slider Mapping

When the `/profiles` command changes a rider archetype, only directly
mapped frontmatter fields (currently `maxTurns` from `autonomy`) MAY be
adjusted proportionally. The `/profiles` command SHOULD present these
adjustments to the user for confirmation before writing.

| Slider | Frontmatter Field | Mapping Rule |
| --- | --- | --- |
| `autonomy` | `maxTurns` | T1->5, T2->10, T3->15-20, T4->25-30, T5->50 |
| `deference` | (no direct mapping) | Deference is prose-only. `permissionMode` is structural and tied to the canonical lane, not the rider. |
| `conservatism` | (no direct mapping) | Conservatism is prose-only. Tool lists are structural. |

**Key design decision:** `permissionMode` and `tools` are properties of
the canonical lane, not the rider. A planner is always `plan` mode
regardless of whether its rider is Logike or Scooter. A reviewer is
always `plan` mode. An executor is always `default` mode. Changing the
rider changes the prose body; it does not change the structural
permissions. This prevents a misconfigured rider from accidentally
granting write access to a read-only lane.

---

## Derivative File Pipeline

When profiles change, these files need regeneration:

| Source | Derivative | Trigger |
| --- | --- | --- |
| Profile config (slider values) | Agent body prose (markdown) | `/profiles` command confirms changes |
| Profile config (archetype + lane) | Comment block in agent files | Same trigger |
| Crew preset config | All 7 agent files + primary agent config | `/profiles` crew change |
| Profile config + workflow map | Consolidated single-agent profile variant (planned) | `/profiles` command in platforms without subagent delegation |

The regeneration pipeline:

1. `/profiles` command confirms new slider values.
2. `/profiles` invokes profiler script (or agent follows prose generation
   guide manually).
3. Profiler reads slider values for each subagent slot from the crew config.
4. For each slot, profiler runs the prose generation pipeline
   (guide_prose_generation.md).
5. Profiler writes the regenerated body into the corresponding agent file,
   preserving frontmatter.
6. Profiler reports changed files to the primary agent.

<!-- REVIEW NOTE: The profiler is specified as a script
(generate_profiles.py) for determinism and speed. An alternative is an
"updater subagent" that reads the prose generation guide and produces
output. The script is preferred because: (a) deterministic output enables
diffing, (b) no token cost for regeneration, (c) can be run in CI/CD.
Initial implementation may use the agent-follows-guide approach until the
script is built. -->

---

## Single-Agent Degradation Mode (Planned)

This specification is canonical for multi-agent environments that support
delegation to subagents. In single-agent environments (no subagent runtime),
it degrades as follows:

1. The same 7 canonical lanes remain authoritative for behavior design.
2. The profiler emits a consolidated single-agent profile variant instead of
   seven subagent files (see `guide_native_command_comparison.md`).
3. `permissionMode`, `tools`, and `disallowedTools` remain structural lane
   definitions in this spec and are NOT slider-driven runtime toggles.
4. The fixed AI-facing return protocol section is omitted because there is
   no subagent-to-lead-agent handoff hop.

This preserves behavior parity across environments while keeping structural
safety decisions lane-based.

---

## Human Communication Matrix

| Subagent | Talks to Human Directly? | Communication Path |
| --- | --- | --- |
| ai-ops-planner | No | Returns structured plan -> primary agent presents to human |
| ai-ops-executor | No | Returns execution report -> primary agent presents to human |
| ai-ops-builder | No | Returns build/creation report -> primary agent presents to human |
| ai-ops-reviewer | No | Returns review findings -> primary agent presents to human |
| ai-ops-researcher | No | Returns research synthesis -> primary agent presents to human |
| ai-ops-closer | No | Returns closeout report -> primary agent presents to human |
| ai-ops-linter | No | Returns validation results -> primary agent presents to human |

**All human communication flows through the primary agent.** The primary agent's
rider profile (relational layer sliders) determines how subagent output
is presented to the human. Subagent relational sliders are stored but
not actively used in prose generation for the subagent body.

---

## Plugin agents/README.md Update

The current stub `agents/README.md` in the plugin skeleton (created by
WB-01) should be replaced with content reflecting the 7 lane-aligned subagents defined
in this specification. See WB-03 revised for the implementation task.
