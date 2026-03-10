---
title: Guide: Work Proposals
version: 0.2.0
status: active
license: Apache-2.0
last_updated: 2026-02-26
owner: ai_ops
related:
- 00_Admin/guides/ai_operations/guide_ai_ops_vocabulary.md
- 00_Admin/guides/ai_operations/guide_workflows.md
- 00_Admin/guides/authoring/guide_workbooks.md
- 01_Resources/templates/workflows/work_proposal_template.md
---

# Guide: Work Proposals

## Purpose and scope

A **Work Proposal** is a governance-only artifact used to document scope, rationale, and approval needs for Level 4
changes. Work Proposals are not executed.

This guide defines the required structure and placement for Work Proposals.

## When required

Create a Work Proposal when:

- The change affects governance artifacts (policies/specs/architecture).
- The decision requires human approval before execution.

## Required sections

Each Work Proposal MUST include:

- Purpose and background
- Scope (in/out)
- Affected files (explicit list)
- Proposed changes (concise list)
- Rationale and alternatives
- Approval status and decision log
- Approver and approval date

## Approval Record

Approval details MUST be recorded in the proposal using these fields:

- Approver name
- Approval date (YYYY-MM-DD)
- Approval status (approved/rejected/needs-revision)
- Scope summary (1-2 sentences)
- Execution workbook reference (path or ID, if known)

Example approval record (inline section):

```markdown
## Approval status and decision log

- Approver: requestor
- Approval date: 2026-01-15
- Status: approved
- Scope summary: Update AI Ops governance guides and registries.
- Execution workbook: 90_Sandbox/ai_workbooks/wb_example/wb_example_execute_01.md
```

## Location and naming

Work Proposals live alongside their parent container:

- Workbundle: `90_Sandbox/ai_workbooks/wb_<workbook_id>_<YYYY-MM-DD>/`
- Workprogram: `<program_folder>/`

Naming pattern:

`work_proposal_<topic>_<nn>.md`

## Status and lifecycle

- Use `status: stub` while pending approval.
- Work Proposals are transient; move to `99_Trash/` with the workbundle/program after execution.

## Relationship to execution workbooks

Work Proposal -> Execution Workbook

- The proposal defines scope and rationale.
- The execution workbook performs the approved edits.
- Execution workbooks MUST reference the approved proposal.
- Do not execute a proposal directly.

Approval details MUST be recorded in both the Work Proposal and the execution workbook.

## Proposal-Truth Synchronization

Execution workbooks MUST stay synchronized with their governing proposal:

<!-- markdownlint-disable MD013 -->
| Check | When | Action if mismatch |
| --- | --- | --- |
| Proposal status | Before execution starts | If `stub` or `rejected`, STOP. |
| Proposal status | During execution | If revoked/revised, STOP and re-sync. |
| Scope match | Before execution | If workbook scope exceeds proposal, request scope update. |
| Approval record | After execution | Both artifacts MUST record identical approval details. |
<!-- markdownlint-enable MD013 -->

**Rules:**

<!-- markdownlint-disable MD013 -->

1. **Proposal is source of truth.** Workbook claims of approval are invalid without matching proposal
   record.
2. **No execution without explicit approval.** A workbook may proceed only when the proposal has an
   explicit approval record (see "Approval record" section). Check `approval_status: approved` in the
   proposal, not `status` (which remains canonical: stub/active/deprecated).
3. **Scope drift requires re-approval.** If workbook discovers out-of-scope changes are needed, pause
   and update the proposal before continuing.
4. **Synchronization check at start and end.** Re-read proposal approval record before first edit and
   before reporting completion.

<!-- markdownlint-enable MD013 -->

This prevents orphaned approvals and scope creep during execution.

## Minimal scaffold

```markdown
---
title: Work Proposal: <Topic>
id: work_proposal_<topic>_<nn>
status: stub
version: 0.1.0
created: YYYY-MM-DD
last_updated: 2026-01-15
owner: ai_ops
---

H1: Work Proposal: <Topic>

## Purpose and background

## Scope

## Affected files

## Proposed changes

## Rationale and alternatives

## Approval status and decision log
```

## References

- `00_Admin/guides/authoring/guide_workbooks.md`
- `00_Admin/guides/ai_operations/guide_ai_ops_vocabulary.md`
- `01_Resources/templates/workflows/work_proposal_template.md`
