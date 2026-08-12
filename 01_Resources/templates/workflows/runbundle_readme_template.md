---
title: Runbundle README Template
version: 0.3.0
status: active
license: Apache-2.0
created: 2026-02-01
updated: 2026-07-16
owner: ai_ops
related:
  - 00_Admin/guides/ai_operations/guide_workflows.md
  - 00_Admin/guides/ai_operations/guide_ai_ops_vocabulary.md
  - 00_Admin/specs/spec_run_family_composition.md
description: Template for runbundle README files.
---

# Runbundle: <runbundle_title>

## Purpose

Briefly describe why this runbundle exists and what it executes.

## Scope

- **Target**: <repo or module>
- **Focus areas**: <bullets>

## Contents

| Runbook ID | Resolved Canonical Home | Constraint | Profile | Purpose |
| --- | --- | --- | --- | --- |
| `rb_<runbook_id>` | `<repo-relative-path>` | `<version_constraint>` | `<parameter_profile>` | Primary runbook |

Companion files:

| File | Purpose |
| --- | --- |
| `rnb_<bundle_name>_<nn>.md` | Local queue artifact (optional) |
| `_scratchpad_<agent>_<YYYY-MM-DD>.md` | Notes (optional) |

The consumer manifest owns outgoing `consumes` edges. This table is a human
projection. A runbook may be consumed by multiple runbundles without copying.

## Intake / Admission Contract (Conditional)

Complete this section when the runbundle is an **intake or admission provider**:
it accepts heterogeneous or variable inputs (consultant packages, vendor
exports, mixed formats) and normalizes them for downstream consumers. Omit it
for runbundles whose inputs are fixed and homogeneous.

An intake provider MUST make admission explicit and lossless in the audit sense:
every received item resolves to exactly one disposition and **nothing
disappears silently**.

- **Source immutability and provenance snapshot.** Preserve originals unmodified.
  Record an inventory that preserves original names, relative paths, sizes,
  content hashes, and timestamps where available, plus package relationships
  (xrefs, sidecars, dependencies). Freeze and hash the received package before
  any conversion.
- **Format / capability matrix.** For each anticipated input class, declare how
  it is read, what capability or tool it requires, and whether that capability
  is verified. Unsupported or partially supported formats are named, not
  skipped.
- **Admission disposition (per item).** Every inventoried item receives one
  disposition:

  | Disposition | Meaning |
  | --- | --- |
  | `admitted` | Read and normalized as authoritative for its role. |
  | `conversion_required` | Usable only after a pinned, receipted conversion. |
  | `reference_only` | Retained as context/evidence; never authoritative geometry or data. |
  | `quarantine` | Held for review (ambiguous currency, backups, unexplained conflicts). |
  | `unsupported` | No admission path yet; a future adapter is required. |
  | `blocked` | A dependency or gate prevents admission until resolved. |

- **Admission receipt.** The run MUST emit a receipt stating what was read, what
  was converted, what was retained only as evidence, what was quarantined, and
  what remains blocked. The receipt is run evidence and stays separate from the
  reusable definition (see `spec_run_family_composition.md`). Its canonical shape
  is `00_Admin/configs/validator/schema_run_family_intake_receipt.yaml`, enforced
  by `validate_run_family_graph.py --intake-receipt <path>`, which rejects a
  receipt with an item missing a disposition, missing provenance, or an
  admitted/converted item with no admission evidence.

Format-capability matrix starter:

| Input class | Read path / capability | Capability verified | Default disposition |
| --- | --- | --- | --- |
| `<class>` | `<tool_or_parser>` | `yes/no/conditional` | `<disposition>` |

## Execution Strategy

| Artifact | Mode | Model Tier | Isolation | Actor | Notes |
| --- | --- | --- | --- | --- | --- |
| `rb_<runbook_id>` | subagent | low | none | Executor | bounded, repeatable |
| `Manual step` | operator | n/a | n/a | requestor | human-only gate |

**Modes:** `direct` (current session), `subagent` (spawned agent), `operator` (human action)

**Model tiers:** portable `low`, `medium`, or `high` capability levels

**Isolation:** `none`, `worktree` (isolated git worktree), `venv`, `container`

**Actor:** `executor`, `requestor`, `approver`, `external_operator`

## Execution Lane Contract

Canonical lanes during execution:

- `Coordinator`: sequence and gate ownership.
- `Executor`: runbook execution.
- `Builder`: tooling/config implementation when required by runbook scope.
- `Reviewer`: judgment-heavy review and crosscheck findings.
- `Linter`: mechanical validation findings and report-only checks.

## Sequence Naming Contract

Use numbered runbook names when execution order is fixed and coordinated
inside this runbundle:

- ordered books: `rb_NN_<name>.md` (for example `rb_01_preflight.md`)
- unordered books: `rb_<name>.md` (no sequence prefix)

Rule:

- If this README or `rnb_<bundle_name>_<nn>.md` defines strict order, apply
  `rb_NN_` naming.
- If order is informal, do not force numbering.

Batch-sequenced parallel guidance:

- If runbooks execute in parallel batches with strict stage ordering, keep
  `rb_NN_` numbering aligned to batch sequence.
- Use batch sections in local queue artifacts to show which runbooks can run
  concurrently in each stage.
- Rule: all required runbooks in batch `NN` must complete before starting
  batch `NN+1`.

## Authority Source

- Membership authority: colocated `manifest.yaml` (the run-family discovery name;
  do not use a `runbundle_manifest.yaml` variant)
- Optional control authority: the consuming runprogram's `execution_graph.yaml`
  (or this runbundle's own `execution_graph.yaml` when it branches). Runbundles
  do not use a work-family execution spine.
- Local queue artifact: `rnb_<bundle_name>_<nn>.md`
- Conflict rule: the control graph governs control flow; directory ancestry
  never grants authority.

## CSCC Preflight

- [ ] Consumer manifest IDs, constraints, profiles, and resolved homes are valid.
- [ ] Runbook path and companion artifacts are valid.
- [ ] Parent program references are valid (if present).
- [ ] Compacted context source is known (runbundle README or runbook body if standalone).
- [ ] Local gates/approvals are explicit before execution.
- [ ] Validation command paths are known.

## Status

- [ ] Runbundle created
- [ ] Execution in progress
- [ ] Execution complete
- [ ] Closeout complete

## Maintenance

- Update this README when new artifacts are added.
- Update the `updated` date whenever contents change.

## Axis Mapping

- Primary axis: `execution`
- Quality axes: `clarity`, `thrift`, `context`, `governance`

## References

- `<path/to/runbook_or_guide>`
- `rnb_<bundle_name>_<nn>.md` (optional pipeline artifact)
