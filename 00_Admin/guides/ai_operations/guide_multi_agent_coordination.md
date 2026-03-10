---
title: Guide: Multi-Agent Coordination
version: 0.1.1
status: stub
license: Apache-2.0
created: 2026-01-24
last_updated: 2026-03-04
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

In ai_ops multi-agent runs, agents are assigned canonical functional roles -- Coordinator, Executor, Builder,
Validator -- per the **Crew Model**. See `00_Admin/guides/architecture/guide_design_and_philosophy.md`
Sec.The Crew Model. The lock and conflict rules in this guide apply regardless of which role an agent holds.

## AI Agent Applicability

- Applicability: Conditional
- Explicit triggers: user requests parallel execution or multi-agent coordination
- Implicit triggers: more than one active agent or overlapping shared files

## Lock Mechanisms

### File-Level Locks

When a workbook specifies `execution_mode: parallel_with_locks` and `lock_scope: file`:

- Agent MUST acquire lock on file before editing
- Lock includes file path and agent identifier
- Lock TTL (Time To Live): 30 minutes default
- Lock refresh: Every 10 minutes if work continues
- Lock release: Immediately after file write completes

### Lock Storage

Locks stored in: `.aiops_session/locks.yaml`

Session state is stored in `.aiops_session/session.yaml` (schema applies to this file).

Format:

```yaml
locks:
  - file: 00_Admin/guides/example.md
    agent_id: claude_session_abc123
    acquired: 2026-01-24T10:30:00Z
    ttl_expires: 2026-01-24T11:00:00Z
    workbook: wb_example_01
```

### Lock Acquisition

Lock acquisition steps:

1. Check if a valid lock exists for the file.
2. If the same agent holds it, refresh the lock.
3. If another agent holds it, stop and report conflict.
4. If no valid lock exists, create one with TTL.

## Conflict Handling

### Scenario 1: Lock Acquisition Failure

**Situation**: Agent A tries to edit file locked by Agent B

**Behavior**:

1. Agent A detects lock held by Agent B
2. Agent A logs conflict to `00_Admin/logs/log_workbook_run.md`
3. Agent A suggests to user:
   - Wait for lock release (check TTL expiry time)
   - Contact Agent B's operator to coordinate
   - Override lock if Agent B session terminated (requires human approval)

### Scenario 2: Lock Expiry During Work

**Situation**: Agent A's lock expires while still working

**Behavior**:

1. Agent A attempts to refresh lock every 10 minutes
2. If refresh fails (another agent acquired), Agent A:
   - Stops editing
   - Logs conflict
   - Reports to user: "Lock lost during work, changes not saved"
   - Suggests manual merge or retry

### Scenario 3: Simultaneous Lock Requests

**Situation**: Agent A and Agent B request same file lock simultaneously

**Behavior**:

- First lock write wins (filesystem atomic write)
- Loser detects lock exists, backs off
- Exponential backoff: 1s, 2s, 4s, then report conflict

## Coordination Patterns

### Pattern 1: Shared Files Declaration

Workbook declares files that may conflict:

```yaml
shared_files:
  - 00_Admin/configs/validator/validator_config.yaml
  - 00_Admin/guides/authoring/guide_workbooks.md
lock_scope: file
```

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

## Lock Cleanup

### Manual Cleanup

If lock file corrupted or stale locks present:

```bash
cat .aiops_session/locks.yaml
```

To remove a specific lock entry, edit `.aiops_session/locks.yaml` with human approval.

Emergency-only full lock reset command (requires human approval):

```bash
rm .aiops_session/locks.yaml
```

### Automatic Cleanup

On session start, agent checks for expired locks:

- If lock TTL expired > 1 hour, automatically remove
- If lock TTL expired < 1 hour, warn user before removing

## Conflict Resolution Workflow

1. **Detect**: Agent detects lock conflict or merge conflict
2. **Log**: Record conflict in `00_Admin/logs/log_workbook_run.md`
3. **Notify**: Report to user with context (which file, which agents, what work)
4. **Options**:
   - Wait: User decides to wait for lock release
   - Coordinate: User contacts other agent's operator
   - Override: User approves lock override (Level 4 decision)
   - Abort: User aborts current agent's work

## Safe Defaults

- Default lock TTL: 30 minutes (prevents indefinite locks)
- Default lock refresh interval: 10 minutes
- Default conflict behavior: Stop and report (never auto-merge)
- Default coordination mode: Pessimistic locking (acquire before edit)

## Future Enhancements

- Optimistic locking (edit first, merge on conflict)
- Agent-to-agent messaging (direct coordination without human mediation)

## References

- [guide_workflows.md](./guide_workflows.md) - Parallel execution patterns
- [guide_workbooks.md](../authoring/guide_workbooks.md) - Execution modes and dependencies
