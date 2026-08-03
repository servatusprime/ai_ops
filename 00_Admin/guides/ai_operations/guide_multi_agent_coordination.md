---
title: Guide: Multi-Agent Coordination
version: 0.2.0
status: active
license: Apache-2.0
created: 2026-01-24
last_updated: 2026-07-22
owner: ai_ops
ai_agent_applicability: conditional
related:
  - ./guide_workflows.md
  - ../authoring/guide_workbooks.md
---

# Guide: Multi-Agent Coordination

## Purpose

Define coordination rules for multiple agents working concurrently on the same repository, preventing conflicts while
enabling parallel execution.

In ai_ops multi-agent runs, agents are assigned canonical lanes -- Coordinator, Planner, Executor, Builder,
Reviewer, Researcher, Closer, Linter -- per the **Crew Model**. See
`00_Admin/guides/architecture/guide_design_and_philosophy.md` Sec.The Crew Model. The write-coordination rules
in this guide apply regardless of which lane an agent holds.

## AI Agent Applicability

- Applicability: Conditional
- Explicit triggers: user requests parallel execution or multi-agent coordination
- Implicit triggers: more than one active agent or overlapping shared files

## Write Coordination Model

ai_ops has **no runtime lock service**. There is no daemon, no lock file
consumer, and no process that can prevent a second agent from writing a file.
Any rule that depends on acquiring, refreshing, or expiring a lock is therefore
unenforceable, and unenforceable rules are not governance.

Coordination is achieved structurally instead, by making conflicts impossible
rather than detecting them after the fact.

### Rule 1: Disjoint Write Targets by Default

Assign every concurrent lane a write target that no other lane touches. This is
the primary and preferred mechanism. Identify all output paths at the start of
execution planning, before any lane is dispatched.

### Rule 2: Named Merge Owner When Overlap Is Unavoidable

If two lanes genuinely must write the same path:

1. Name **one** merge owner -- a single lane that owns the final content.
2. Sequence the writes explicitly: one lane writes, then hands off.
3. Record the merge owner in the execution artifact before dispatch, not after
   a conflict appears.

Do not rely on filesystem atomic writes to prevent corruption; enforce
sequencing at the workflow level.

### Rule 3: Delegated Writes Declare Their Target

Every delegated write declares a single `write_target` path in its task brief.
A delegated lane may not write outside its declared target.

Hash or promotion evidence is required **only** when the runtime actually
isolates the child write root -- for example `isolation: worktree`, where the
child writes to a separate checkout and its output must be verified before
promotion. When agents share one authoritative checkout, requiring hash
promotion adds ceremony without adding safety, and is not required.

### Conflict Handling

Because conflicts are prevented structurally, there is no lock-conflict
protocol. If two agents are found writing the same path, that is a planning
defect: stop, record it in the execution artifact, assign a merge owner, and
re-sequence. Never auto-merge.

## Coordination Patterns

### Pattern 1: Overlapping Write Target with a Merge Owner

Workbook declares a path more than one lane must write, and names the single
lane that owns the merge:

```yaml
shared_files:
  - 00_Admin/guides/authoring/guide_workbooks.md
merge_owner: Executor   # one named lane owns final content
write_sequence:
  - Executor            # writes first
  - Reviewer            # then hands off
```

`lock_scope` is retained as compatibility-only frontmatter metadata. It records
intent and does not permit, coordinate, or enforce concurrent writes.

### Pattern 2: No-Conflict Execution

Workbook declares no shared files:

```yaml
execution_mode: parallel_safe
shared_files: []
lock_scope: none
```

Agents can run concurrently without coordination overhead.

### Pattern 3: Sequential Dependency

Workbook declares dependency on another workbook:

```yaml
depends_on:
  - wb_example_01
  - wb_example_02
```

Agent MUST verify dependencies complete before starting.

## Sequential Execution Guard

Mutating stages that write to the same output path MUST be sequential. Parallel
subagent lanes MUST NOT be assigned the same output path.

Rules:

- Identify all output paths at the start of parallel execution planning.
- If two tasks write the same output file, assign them to the same lane in sequence.
- If parallel assignment is unavoidable, add an explicit merge gate: one lane writes,
  then hands off to the other.
- Do not rely on filesystem atomic writes to prevent corruption — enforce sequencing
  at the workflow level.

Declare this constraint in the `do_not_delegate_when` block of the
`execution_topology_contract` in workbooks with parallel lanes.

Reference: `fw_20260319_04` governance seed.

## Safe Defaults

- Default coordination mode: disjoint write targets.
- Default conflict behavior: stop and report; never auto-merge.
- Default merge ownership: unset. If two lanes need one path, naming an owner is
  a required planning step, not a runtime fallback.

## References

- [guide_workflows.md](./guide_workflows.md) - Parallel execution patterns
- [guide_workbooks.md](../authoring/guide_workbooks.md) - Execution modes and dependencies
