---
title: Guide: Authority Decision Tree
version: 0.1.0
status: active
license: Apache-2.0
last_updated: 2026-02-28
owner: ai_ops
related:
  - ../../../CONTRIBUTING.md
  - ../../../AGENTS.md
  - 00_Admin/guides/ai_operations/guide_bootstrap_verification_checklist.md
alignment_note: "This guide supplements and expands upon the authority decision tree in CONTRIBUTING.md with detailed
  examples, edge cases, and action patterns. It does not replace the canonical policy in CONTRIBUTING.md, but provides
  operational guidance for applying those rules. If divergence occurs, CONTRIBUTING.md takes precedence."
---

# Guide: Authority Decision Tree

## Purpose

This decision tree helps agents quickly determine the correct authority level for a task and understand the appropriate
action pattern.

## How to Use This Tree

1. Start at the top with your task description
2. Answer each decision point (yes/no)
3. Follow the path to your authority level
4. Execute the corresponding action pattern

## Decision Tree

```text
START: I have a task to complete
|
+-> Does this task involve READING ONLY (no writes)?
|   +-> YES -> LEVEL 0: Read, analyze, report
|       Action: Proceed without restriction
|       +-> DONE
|
+-> NO (task involves writes) -> Continue below
    |
    +-> Does this task affect governance artifacts?
    |   (Policies in 00_Admin/policies/, Specs in 00_Admin/specs/,
    |    Architecture guides in 00_Admin/guides/architecture/)
    |   |
    |   +-> YES -> LEVEL 4: Governance changes
    |       Action: Create Work Proposal, document rationale, wait for human approval
    |       +-> DONE
    |
    +-> NO (not governance) -> Continue below
        |
        +-> How many file operations are involved?
        |
        +-> 1 file, atomic change (single focused edit)
        |   +-> Is the file in a pre-authorized path?
        |       (Module docs, sandbox artifacts, logs)
        |       |
        |       +-> YES -> LEVEL 1: Single atomic edit
        |       |   Action: Make edit, validate, commit
        |       |   +-> DONE
        |       |
        |       +-> NO -> LEVEL 2: Confirm first
        |           Action: Describe change, wait for confirmation, proceed
        |           +-> DONE
        |
        +-> 2-5 files, related changes (small batch)
        |   +-> LEVEL 2: Small batch
        |       Action: Describe changes, wait for confirmation, proceed
        |       +-> DONE
        |
        +-> 6+ files, OR affects 3+ directories, OR multi-layer
            +-> LEVEL 3: Workbook required
                Action: Create workbook, wait for approval, execute workbook
                +-> DONE
```

## Detailed Decision Points

### Decision Point 1: Read-Only?

**Question**: Does this task involve writing or modifying any files?

- **YES (read-only)**: Level 0 - No restrictions
- **NO (involves writes)**: Continue to next decision point

**Examples:**

- Level 0: "Analyze the GIS workflow and report findings"
- Level 0: "Search for all uses of the `calculateTotal` function"
- Not Level 0: "Fix the typo in README.md" (involves write)

### Decision Point 2: Governance Artifacts?

**Question**: Does this task affect policies, specs, or architecture documents in 00_Admin/?

**Governance artifacts include:**

- `00_Admin/policies/*.md` - Hard rules (MUST/MUST NOT)
- `00_Admin/specs/*.md` - Technical requirements
- `00_Admin/guides/architecture/*.md` - Structural guidance
- `CONTRIBUTING.md`, `AGENTS.md`, `HUMANS.md` - Entry point documents

**YES (governance)**: Level 4 - Work Proposal required, human approval mandatory

**NO (not governance)**: Continue to next decision point

**Examples:**

- Level 4: "Update the authority levels policy"
- Level 4: "Add a new spec for module interfaces"
- Level 4: "Restructure the repository architecture guide"
- Not Level 4: "Update a module's documentation" (module-specific, not governance)

### Decision Point 3: How Many Files?

**Question**: How many file operations (create, update, delete) are involved?

**1 file, atomic change:**

- Single focused edit to one file
- Examples: Fix typo, update single config value, add one function

**2-5 files, related changes:**

- Small batch of related edits
- Examples: Update imports across a few files, rename function in 3 places

**6+ files OR 3+ directories OR multi-layer:**

- Large scope requiring coordination
- Examples: Refactor module structure, update all templates, cross-cutting change

### Decision Point 4: Pre-Authorized Path?

**Question**: Is the single file edit in a pre-authorized location?

**Pre-authorized paths:**

- `02_Modules/<module>/docs/` - Module documentation
- `90_Sandbox/` - Experimental artifacts
- `00_Admin/logs/` - Execution logs (when part of approved work)
- Single file in a module you're actively working on (context-dependent)

**YES (pre-authorized)**: Level 1 - Proceed with edit

**NO (not pre-authorized)**: Level 2 - Confirm first

## Action Patterns by Level

### Level 0: Read, Analyze, Report

**Pattern:**

1. Read files as needed
2. Analyze and synthesize findings
3. Report results to user
4. No workbook required

**Example:**

> User: "What's the current state of the GIS workflow module?"
> Agent: Reads module files, reports status

### Level 1: Single Atomic Edit

**Pattern:**

1. Identify the single file and specific edit
2. Make the edit
3. Run validation (markdownlint, yamllint, etc.)
4. Commit with clear message
5. Report completion

**Example:**

> User: "Fix the typo in a module README"
> Agent: Edits file, validates, commits, reports done

### Level 2: Confirm First

**Pattern:**

1. Describe the proposed changes clearly
2. Wait for user confirmation
3. Make the edits
4. Run validation
5. Commit with clear message
6. Report completion

**Example:**

> User: "Update the version numbers in these 3 config files"
> Agent: "I'll update versions in: file1.yaml, file2.yaml, file3.yaml. Proceed?"
> User: "Yes"
> Agent: Makes edits, validates, commits, reports done

### Level 3: Workbook Required

**Pattern:**

1. Create workbook in 90_Sandbox/ai_workbooks/
2. Document scope, tasks, outputs clearly
3. Wait for workbook approval
4. Execute workbook steps
5. Run Self-Review Smoke Pass
6. Run validation
7. Commit changes
8. Log execution in 00_Admin/logs/log_workbook_run.md
9. Report completion

**Example:**

> User: "Refactor the GIS workflow module to use the new interface pattern"
> Agent: Creates wb_gis_refactor_01.md with full plan
> User: Approves workbook
> Agent: Executes plan, validates, commits, logs, reports done

### Level 4: Work Proposal + Human Approval

**Pattern:**

1. Create Work Proposal document (work_proposal_<topic>_01.md)
2. Document:
   - Purpose and background
   - Scope (in/out)
   - Rationale and alternatives considered
   - Affected files (explicit list)
   - Proposed changes (concise)
3. Set status: stub (pending approval)
4. Wait for human approval
5. Create execution workbook referencing approved proposal
6. Execute workbook (Level 3 pattern)
7. Log decision in 00_Admin/decisions/ if repo-level

**Example:**

> User: "Update the authority levels policy to add Level 5"
> Agent: Creates work_proposal_authority_level_5_01.md with rationale
> User: Reviews and approves
> Agent: Creates wb_update_authority_policy_01.md
> Agent: Executes workbook, logs decision, reports done

## Common Misclassifications

These tasks are often misclassified. Use these as reference:

| Task Description | Seems Like | Actually Is | Reason |
| --- | --- | --- | --- |
| "Quick wins in 8 modules" | Level 2 | Level 3 | 6+ files = workbook |
| "Update CONTRIBUTING.md" | Level 1-2 | Level 4 | Governance artifact |
| "Add example to module docs" | Level 2 | Level 1 | Single file, pre-authorized |
| "Refactor 5 related files" | Level 2 | Level 3 | Borderline - create workbook for clarity |
| "Update AGENTS.md workspace topology" | Level 2 | Level 4 | Root governance file |

## Edge Cases

### Borderline Cases

**Recommendation**: Default to workbook (Level 3) for:

- Clarity: Workbook documents intent and scope
- Auditability: Clear execution record
- Rollback: Easier to revert if issues arise

**Exception**: If all 5 files are simple config updates in the same directory and user explicitly confirms, Level 2 may
be acceptable.

### Sandbox vs Canonical Confusion

**Rule**: Authority level is based on the **intent** of the work, not the current location.

- If creating sandbox artifacts for experimentation: Level 1-2
- If creating sandbox artifacts that will be promoted to canonical: Level 3 (workbook shows promotion path)
- If modifying canonical governance: Always Level 4

### Log and Validation Steps

**Rule**: Logging and validation steps are **pre-authorized** once a workbook is approved.

- Don't re-confirm: "Can I run markdownlint?" (pre-authorized)
- Don't re-confirm: "Can I log this in log_workbook_run.md?" (pre-authorized)
- Do confirm: Adding a new validation tool or logging location not in approved workbook

## Enforcement

This decision tree is **normative** - agents must follow it. Violations indicate bootstrap failure or governance drift.

**If you're unsure**: Default to the higher authority level (more restrictive). It's better to confirm unnecessarily
than to overstep authority.

## References

- Full authority descriptions: `CONTRIBUTING.md` section "Agent Action Authority Levels"
- Pre-authorization rules: `CONTRIBUTING.md` section "Agent Handshake and Pre-Authorization"
- Workbook requirements: `00_Admin/guides/authoring/guide_workbooks.md`
- Work Proposal requirements: `00_Admin/guides/ai_operations/guide_work_proposals.md`
