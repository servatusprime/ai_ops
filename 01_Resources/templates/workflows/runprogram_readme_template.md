---
title: Runprogram README Template
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
description: Template for runprogram README files.
---

# Runprogram: <runprogram_title>

## Purpose

Briefly describe why this runprogram exists and what it coordinates.

## Scope

- **Target**: <repo or module>
- **Focus areas**: <bullets>

## Runbundles

| Runbundle ID | Resolved Canonical Home | Constraint | Profile | Status |
| --- | --- | --- | --- | --- |
| `rnb_<bundle_id>` | `<repo-relative-path>` | `<version_constraint>` | `<parameter_profile>` | `<status>` |

The colocated consumer manifest owns this runprogram's outgoing `consumes`
edges. This table is a human projection and MUST match the manifest. A
runbundle may be consumed by multiple runprograms without being copied.

## Execution Strategy

| Artifact | Mode | Model Tier | Isolation | Actor | Notes |
| --- | --- | --- | --- | --- | --- |
| `rnb_<bundle_01>` | subagent | low | none | Executor | bounded, repeatable |
| `rnb_<bundle_02>` | subagent | medium | worktree | Executor | writes to shared surface |
| `Manual step` | operator | n/a | n/a | requestor | human-only gate |

**Modes:** `direct` (current session), `subagent` (spawned agent), `operator` (human action)

**Model tiers:** portable `low`, `medium`, or `high` capability levels

**Isolation:** `none`, `worktree` (isolated git worktree), `venv`, `container`

**Actor:** `executor`, `requestor`, `approver`, `external_operator`

## Execution Lane Contract

Canonical lanes during execution:

- `Coordinator`: runprogram sequencing and gate ownership.
- `Executor`: runbundle/runbook task execution.
- `Builder`: tooling/config implementation lanes when present.
- `Reviewer`: review and crosscheck verdict ownership.
- `Linter`: mechanical validation/report-only gate ownership.

## Sequence Naming Contract

Use numbered runbook names for fixed-order execution across runbundles in this
program:

- ordered books: `rb_NN_<name>.md` (for example `rb_01_preflight.md`)
- unordered books: `rb_<name>.md` (no sequence prefix)

Rule:

- If `execution_graph.yaml` or `runprogram_pipeline_<nn>.md` encodes strict
  order, apply `rb_NN_` naming for affected books.
- If order is informal or parallel-safe, numbering is optional.

Batch-sequenced parallel guidance:

- For staged execution with parallel batches, define explicit batch gates in
  `execution_graph.yaml` or `runprogram_pipeline_<nn>.md`.
- Runbooks may run in parallel within a batch only when `execution_mode` and
  lock declarations allow it.
- Rule: batch `NN+1` cannot start until all required runbooks in batch `NN`
  satisfy completion gates.

## Staged Reconciliation and Identity Preservation (Conditional)

Complete this section when the runprogram reconciles, blends, or composes inputs
across **ordered stages** (for example: normalize -> reconcile source A ->
reconcile source B against the A-derived result). Omit it for programs whose
runbundles are independent and orderless.

- **Distinct identities persist across stages.** Each source and each stage
  output is a separately identifiable artifact end to end. A stage MUST NOT
  collapse two distinct sources into one identity, and a later stage's output
  MUST NOT overwrite the identity of an input it consumed.
- **Explicit stage order and boundaries.** State the stage sequence and the
  boundary/relationship assumptions between stages (inputs may coincide,
  overlap, or differ; do not assume they coincide). Encode strict order in
  `execution_graph.yaml` or the pipeline artifact and apply `rb_NN_` naming.
- **Per-stage acceptance disposition.** Each stage output carries a disposition:
  `candidate` -> `validated` (passed the stage's QA/residual checks) ->
  `accepted` (approved for downstream consumption). Downstream stages consume
  only `accepted` artifacts unless a stage explicitly declares otherwise.
- **Provenance retained.** Blended or composite outputs record which sources and
  which stage produced them, so a consumer can trace any cell/feature back to
  its origin and exclusion rules.

Stage table starter:

| Stage | Inputs (identities) | Output (identity) | Acceptance gate | Disposition |
| --- | --- | --- | --- | --- |
| `NN` | `<source_a>`, `<source_b>` | `<stage_output>` | `<QA/residual gate>` | `candidate/validated/accepted` |

## Authority Source

- Membership authority: colocated `manifest.yaml` (the run-family discovery name;
  do not use a `runprogram_manifest.yaml` variant)
- Control-flow authority: colocated `execution_graph.yaml` (routing, gates,
  bounded loops, escalation; see `spec_execution_control_graph.md`). Runprograms
  use the control graph, not a work-family execution spine.
- Queue mirror (optional): `runprogram_pipeline_<nn>.md`
- Conflict rule: the control graph governs control flow; the pipeline is a synced
  queue mirror.

## CSCC Preflight

- [ ] Consumer manifest IDs, constraints, profiles, and resolved homes are valid.
- [ ] Runprogram README/`execution_graph.yaml`/pipeline references are valid.
- [ ] Runbundle inventory reflects current execution scope.
- [ ] Compacted context source is known (runprogram or runbundle README).
- [ ] Gate owners/approval mode are explicit.
- [ ] Validation command paths are known.

## Status

- [ ] Runprogram created
- [ ] Active runbundles in progress
- [ ] All runbundles complete
- [ ] Closeout complete

## Maintenance

- Update this README when adding/removing runbundles.
- Update the `updated` date whenever contents change.

## Axis Mapping

- Primary axis: `execution`
- Quality axes: `clarity`, `thrift`, `context`, `governance`

## References

- `<path/to/runbook_or_guide>`
- `execution_graph.yaml` (colocated control surface; see `spec_execution_control_graph.md`)
- `runprogram_pipeline_<nn>.md` (optional)
