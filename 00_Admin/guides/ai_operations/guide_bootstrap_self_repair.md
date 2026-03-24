---
title: Guide: Bootstrap Self-Repair Protocol
version: 0.2.1
status: stub
license: Apache-2.0
created: 2026-01-24
last_updated: 2026-03-24
owner: ai_ops
ai_agent_applicability: conditional
related:
  - ../../runbooks/rb_bootstrap.md
  - ./guide_workflows.md
  - ../architecture/guide_bootstrap_algorithm.md
---

# Guide: Bootstrap Self-Repair Protocol

## Purpose

Define automatic recovery behavior when bootstrap sequence fails or encounters corrupted artifacts.

## AI Agent Applicability

- Applicability: Conditional
- Explicit triggers: user requests repair or safe-mode recovery
- Implicit triggers: bootstrap failure detected (missing/unreadable AGENTS.md, corrupted session files)

## Session Storage

This repo uses a directory-based session layout:

- `.aiops_session/session.yaml` - current session state (schema applies here)
- `.aiops_session/locks.yaml` - agent locks
- `.aiops_session/transcripts/` - session transcripts
- `.aiops_session/context_exports/` - context exports

## Failure Detection

### Bootstrap Failure Signals

Agent detects bootstrap failure when:

- **AGENTS.md missing**: Bootstrap entry point not found
- **AGENTS.md unreadable**: Permission errors, encoding issues
- **Authority rules missing**: No authority model in AGENTS.md
- **Session file corrupted**: .aiops_session/*.yaml unreadable
- **Required file unreadable**: Permission errors, encoding issues on other bootstrap files

### Detection Timing

Check for failures:

- **First turn**: Before any other file operations
- **On file read error**: When reading bootstrap sequence files
- **On validation failure**: When checking AGENTS.md parse or structure

## Safe-Mode Behavior

When bootstrap failure detected, agent enters safe-mode:

### Safe-Mode Constraints

- **Read-only operations**: No writes, edits, or deletions
- **Minimal file access**: Only read files explicitly requested by user
- **No autonomous actions**: Wait for user guidance
- **Report failure clearly**: Show what failed and why

### Safe-Mode Message Template

```text
[SAFE-MODE] Bootstrap failed: [specific_reason]

Detected issue:
- [Description of what failed]
- [Path attempted if applicable]

Safe-mode constraints active:
- Read-only operations only
- No autonomous file modifications
- Awaiting user guidance for recovery

Recovery options:
1. Provide bootstrap files manually
2. Point to alternate manifest location
3. Check file permissions and retry

Current capability: Can answer questions, read specific files on request
```

## Guided Recovery Workflows

Operational step-by-step recovery workflows for Missing AGENTS.md, Corrupted Session File,
and Permission Errors are in `00_Admin/runbooks/rb_bootstrap.md` §Bootstrap Failure Recovery.

## Automatic Repair Operations

### Auto-Repair Criteria

Agent may automatically repair (Level 0-1 actions only):

- Remove corrupted session files (non-critical state)
- Use alternate manifest locations (if found)
- Create missing .aiops_session/ directory
- Use fallback bootstrap sequence (AGENTS.md -> README.md)

### Never Auto-Repair

Agent MUST NOT automatically:

- Delete or recreate AGENTS.md
- Change authority rules
- Initialize new repo structure
- Install missing dependencies

## Self-Repair Command

### /work --repair

**Note**: This command is not yet implemented. Workflow file does not exist.

When implemented, `/work --repair` would attempt:

1. **Diagnosis phase**:
   - Check AGENTS.md (exists? readable? contains authority model?)
   - Check .aiops_session/ (writable? corrupted files?)
   - Check required directories (00_Admin, 01_Resources, 02_Modules, etc.)

2. **Repair phase** (only Level 0-1 actions):
   - Remove corrupted session files
   - Create missing .aiops_session/ directory
   - Report any Level 2+ issues for user decision

3. **Verification phase**:
   - Attempt normal bootstrap sequence
   - Report success or remaining blockers

4. **Output**:
   - List of issues found
   - List of issues auto-repaired
   - List of issues requiring user action

## Bootstrap Fallback Sequence

If primary bootstrap fails, try fallback sequence:

1. **Primary**: AGENTS.md -> authority rules -> CONTRIBUTING.md
2. **Fallback 1**: README.md -> .ai_ops/ directory scan
3. **Fallback 2**: Safe-mode (read-only, await guidance)

Agent logs which sequence succeeded.

## Recovery Testing

### Test Scenarios

Bootstrap self-repair should handle:

- AGENTS.md missing
- AGENTS.md unreadable (permission denied)
- .aiops_session/locks.yaml corrupted
- Permission denied on required files
- Wrong working directory (not repo root)

### Expected Behavior

For each scenario, verify:

- Failure detected on first turn
- Safe-mode activated
- Clear error message shown
- Recovery options provided
- No data loss from auto-repair attempts

## Anti-Patterns

**Don't**:

- Silently ignore bootstrap failures
- Auto-repair critical files (AGENTS.md)
- Proceed with partial bootstrap (unsafe state)
- Guess at missing configuration

**Do**:

- Detect failures immediately
- Enter safe-mode on critical failures
- Report clearly what failed and why
- Offer guided recovery options
- Log all repair attempts

## Implementation Notes

- Safe-mode flag: Store in agent state, check before all file operations
- Failure logging: Append to .aiops_session/bootstrap_failures.log
- Backup naming: `[original].[status].YYYYMMDD_HHMMSS` format
- Recovery attempts: Limit to 3 automatic attempts, then require user input

## References

- [rb_bootstrap.md](../../runbooks/rb_bootstrap.md) - Standard bootstrap sequence
- [guide_workflows.md](./guide_workflows.md) - Workflow patterns and error handling
- [op_validate_config.py](../../scripts/op_validate_config.py) - Config validation helper
