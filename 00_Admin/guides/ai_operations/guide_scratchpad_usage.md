---
title: Guide: Scratchpad Usage
version: 0.2.0
status: active
license: Apache-2.0
last_updated: 2026-02-03
owner: ai_ops
related:
- ./guide_ai_ops_vocabulary.md
- ./guide_workflows.md
- ../../guides/authoring/guide_workbooks.md
---

<!-- markdownlint-disable-next-line MD025 MD041 -->

# Guide: Scratchpad Usage

## Purpose

Defines when and how to use scratchpads as temporary companion artifacts during workbook execution. Covers
creation, lifecycle rules, pruning, and promotion of scratchpad content into canonical repo artifacts.

This guide defines when and how to use scratchpads as companion artifacts during workbook execution.

## 1) Definition

A **Scratchpad** is an append-only companion note file stored inside a workbundle. It captures observations, friction
points, and decisions that emerge during execution but do not belong in the workbook itself.

Scratchpads are:

- Transient (archived with the workbundle)
- Append-only during execution (new entries are added, old entries are not deleted)
- Agent-specific (one per agent per session, when useful)
- Lightweight (minimal structure, no governance overhead)

## 2) When to Use

Use a scratchpad when:

- **Tangential Ideas**: Random thoughts, "rabbit holes," or ideas unrelated to the current task (prevent focus loss).
- **Task Buffer**: New tasks identified mid-flight that don't fit the current workbook scope.
- **Friction Logs**: Ambiguity or errors encountered during execution.
- **Mid-Session Context**: Notes for a future agent (or yourself) if the session breaks.
- **Drafting**: Rough work, scratch analysis, or text buffers before finalizing.

## 3) Decision: Scratchpad vs. Workbook

| Item Type                  | Place it in...                                              |
| :------------------------- | :---------------------------------------------------------- |
| **In-Scope Task**          | **Active Workbook** (Execution Notes)                       |
| **Random Idea / Tangent**  | **Scratchpad**                                              |
| **New, Large Scope**       | **New Workbook** (create or propose in scratchpad)          |
| **Deferred / Future Work** | **Scratchpad** (then Harvest to Registry)                   |
| **Governance Decision**    | **Scratchpad** (draft) -> `00_Admin/decisions/` (final)     |

## 3) Naming and Location

- **Naming**: `_scratchpad_<agent_name>_<date>.md` (leading underscore sorts it before workbooks)
- **Location**: Inside the active workbundle folder
- **Example**: `90_Sandbox/ai_workbooks/wb_example_01_2026-01-24/_scratchpad_claude_2026-01-24.md`

Multiple agents MAY have separate scratchpads in the same workbundle.

## 4) Required Structure

Use the template at `01_Resources/templates/workflows/scratchpad_template.md`. Minimum sections:

1. YAML front matter (with `lifecycle: transient`)
2. Purpose (one line)
3. Notes (append-only, dated entries)
4. References (related artifacts)
5. Optional future-work section (only when requestor asks to capture potential future items)

## 4.1) Optional Future Work Matrix (Request-Driven, Not Mandatory)

If the requestor asks to capture potential future tasks/work items in the scratchpad:

- Add a dedicated section named `Potential Future Work (Optional)`.
- Place a compact matrix at the top of that section before freeform notes.
- Use this matrix as triage input; promote keepers to future registry or a workbook later.

Recommended matrix columns:

- `candidate`
- `domain/category`
- `benefit` (`H/M/L`)
- `effort` (`XS-XL`)
- `readiness` (`ready/partial/blocked/deferred`)
- `activation_trigger`

## 5) Lifecycle

1. **Created** when the agent identifies friction or observations during execution.
2. **Appended** throughout the session as new observations arise.
3. **Migrated/Pruned** at closeout (pre-commit): move actionable items into workbooks or the future work registry, then
   prune scratchpad entries that have been migrated.
   If optional future-work matrix was used, promote selected entries and remove migrated rows from scratchpad.
4. **Archived** with the workbundle only if material remains that is still needed for context.
5. **Promoted** (rare): If content warrants canonical status, extract to appropriate location (guide, decision record,
   or policy proposal) via workbook.

### 5.1) Promotion Workflow Standard (Scratchpad -> Workbook -> Registry)

Use these checkpoints to keep scratchpads lean and synchronized:

1. **Capture**: log observation with date, impacted paths, and why it matters.
2. **Classify**:
   - in-scope now -> active workbook
   - out-of-scope future -> future work registry candidate
   - governance decision -> decision record candidate
3. **Promote**: move actionable items into workbook tasks or registry entries.
4. **Prune**: remove migrated items from the scratchpad in closeout.
5. **Verify sync**:
   - workbook checklists reflect promoted items
   - registry contains only intentional future handoffs
   - scratchpad keeps only unmigrated items

## 6) Relationship to Other Artifacts

| Artifact                 | Purpose                           | When to Use Instead              |
| ------------------------ | --------------------------------- | -------------------------------- |
| Workbook Execution Notes | Task-level progress and results   | Routine task outcomes            |
| Peer Review              | Structured independent review     | Formal quality assessment        |
| Decision Record          | Governance decisions              | Cross-cutting repo decisions     |
| Compacted Context        | Handoff payload                   | Agent-to-agent transitions       |
| Scratchpad               | Observations and friction capture | Everything else during execution |

## 7) Best Practices

- Keep entries short (3-5 bullets per entry).
- Date each entry heading.
- Include context for why the observation matters.
- Do not duplicate information already in the workbook.
- Reference specific file paths and line numbers when citing friction.
