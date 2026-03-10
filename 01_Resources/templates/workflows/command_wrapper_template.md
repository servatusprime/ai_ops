---
title: Command Wrapper Template
version: 0.1.0
description: Template for ai_ops slash command wrappers.
status: active
license: Apache-2.0
owner: ai_ops
---

# /command_name

## Purpose

State what the command does and why it exists.

## Inputs and Preconditions

- Required inputs (if any).
- Preconditions that must be true before running.

## Steps

### Inside Repo (Maintainer)

1. Step one.
2. Step two.

### External Repo (User)

1. Step one.
2. Step two.

## Loop Checkpoints (Required for Non-Trivial Commands)

Use these decision gates when a command has meaningful discovery, write
operations, or validation:

1. **Checkpoint A (After Inputs)**: verify inputs/preconditions, then decide
   proceed or pause.
2. **Checkpoint B (After Discovery)**: confirm targets/scope, then decide
   proceed or refine.
3. **Checkpoint C (Before Write)**: confirm output paths/change set, then decide
   execute or stop.
4. **Checkpoint D (After Write)**: validate outputs with evidence, then decide
   done or fix.

## Outputs

- What the command produces (reports, files, summaries).
- Where outputs are written.

## Resources

- Required runbooks, templates, or guides.
- Any config files the command reads or writes.

## Roles

Default role(s) the agent should assume.

## Risks and Limits

- Key risks, tradeoffs, or limitations.

## Related Commands

- `/command_a`
- `/command_b`

## See Also

- `path/to/related/doc.md`
