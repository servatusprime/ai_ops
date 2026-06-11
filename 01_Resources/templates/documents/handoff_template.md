---
title: Handoff Artifact Template
version: 0.2.0
status: stub
license: Apache-2.0
created: 2026-03-25
updated: 2026-06-11
owner: ai_ops
lifecycle: transient
description: >
  Minimal template for a Handoff Artifact. Fill in required fields;
  delete optional fields if not needed. Route to 99_Trash/ after the
  destination lane acknowledges receipt and begins execution.
---

<!-- markdownlint-disable-next-line MD025 -->
# Handoff: `<source_artifact_id>` → `<destination_lane>`

<!-- File naming: handoff_<source_id>_<YYYY-MM-DD>.md -->
<!-- Place at workbundle root alongside workbook and README. -->

## Required Fields

```yaml
handoff:
  source_artifact: <workbook_id or workbundle_id>
  destination_lane: <Coordinator | Executor | Builder | Reviewer | Closer>
  status_summary: >-
    One sentence: what was completed and what state it is in.
  carry_forward:
    constraints:
      - <authority limits, L4 gates, scope boundaries, etc.>
    blocking_issues:
      - <anything unresolved that the next lane must address>
  open_items:
    - <deferred tasks or pending decisions>
  next_step:
    goal: >-
      One sentence: what the next lane needs to accomplish.
    entry_point: <path/to/workbook.md or "Phase N of <workbook_id>">
```

## Optional Fields

```yaml
  validation_commands:
    - python 00_Admin/scripts/validate_repo_rules.py
  references:
    - path/to/relevant/artifact.md
    - path/to/spec.md
  notes: >-
    Any additional context that does not fit above.
```

## Governed-Repo Proposal Seed (Conditional)

Use this block when a governed repo discovers an ai_ops improvement. Do not
edit ai_ops canon or backlog from the unrelated governed-repo lane.

```yaml
proposal_seed:
  generic_source_class: <governed_repo_audit|execution_friction|closeout_review>
  owner: <role or team>
  problem: <self-contained problem statement>
  recommendation: <proposed ai_ops improvement>
  target_surfaces:
    - <generic ai_ops artifact class or repo-relative path>
  activation_trigger: <condition that justifies ai_ops sandbox intake>
  authority_boundary: >-
    This handoff is evidence only and does not authorize canonical ai_ops edits.
  acknowledgement_state: <pending|received|intake_authorized>
```

Activation requires both a satisfied trigger and requestor authorization to
land the seed in an ai_ops sandbox workbundle.

## Usage Notes

- This is a **Meta / transient** artifact. It is not a replacement for the
  workbook — it is a thin summary layer that prevents the next agent from
  needing to re-read all state surfaces.
- Required fields are mandatory. Do not omit `status_summary`, `carry_forward`,
  or `next_step`.
- After the destination lane acknowledges and begins execution, move this file
  to `99_Trash/`.
- See `00_Admin/guides/authoring/guide_workbooks.md §12.1` for the full pattern
  definition.
