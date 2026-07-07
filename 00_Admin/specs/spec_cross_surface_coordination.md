---
title: Cross-Surface Coordination Spec
id: spec_cross_surface_coordination
module: admin
status: active
license: Apache-2.0
version: 0.1.0
created: 2026-07-07
updated: 2026-07-07
owner: ai_ops
ai_generated: true
spec_archetype: governance_spec
related:
  - .ai_ops/workflows/work.md
  - .ai_ops/workflows/crosscheck.md
  - .ai_ops/workflows/closeout.md
  - 01_Resources/templates/workflows/peer_review_template.md
---

<!-- markdownlint-disable MD013 MD025 -->
# Cross-Surface Coordination Spec

## Purpose

Define portable coordination rules for AI-first execution when work moves across
agents, runtimes, shells, validators, or source-control surfaces.

This spec promotes stable dogfood lessons into canonical ai_ops behavior without
promoting any sandbox-only Conductor topology.

## Scope

This spec applies to ai_ops and governed-repo work when:

- a task is resumed after prior partial execution,
- more than one agent or runtime surface participates,
- a review or closeout depends on source-control state,
- a validator, fetch, or runtime check is surface-bound, or
- canonical promotion or completion claims are written to mirror surfaces.

## Normative Rules

### 1. Authoritative-Read Discipline

When surfaces disagree, agents MUST verify suspected file-state defects against
the authoritative file or runtime surface before recording a blocking finding.
A shell, mount, cache, or portable-tool failure is evidence to reconcile; it is
not by itself proof that the repository artifact is defective.

### 2. Changed-Files Containment

Returning execution surfaces MUST disclose every changed file they touched, or
explicitly state that no other files were touched.

Bottom-up and hybrid reviews MUST perform an unscoped changed-files sweep when
source control is available, reconcile the result against authorized scope, and
treat unexplained out-of-scope paths as blocking until attributed.

### 3. Closeout Scope Manifest

Before staging or completion closeout, agents MUST classify changed paths into:

- `include`: in-scope files to ship,
- `related_scope_requires_confirmation`: adjacent fixes that need explicit
  operator confirmation before shipping with the active scope, and
- `exclude`: unrelated dirty paths that must not be staged.

Unrelated dirty paths block unscoped closeout. They do not block a scoped
savepoint when they are excluded and named.

### 4. Completion-Claim Parity

Completion claims MUST match the level actually closed: task, workbook,
milestone, workbundle, workprogram, or program. A milestone closeout MUST NOT
claim program completion unless a program-closeout lane ran.

Any completion claim written to one mirror surface MUST be synchronized to the
required mirror set in the same pass, or the open mirror debt MUST be recorded
as pending.

### 5. Promotion-Record Parity

Canonical promotion writes MUST include the promotion record and required mirror
updates in the same execution leg when practical. If the promoting surface
cannot complete the record or mirrors, it MUST mark `record_pending` or
`mirrors_pending` with owner, affected paths, and next retry surface.

### 6. Resume-Delta Freshness

Before changing state during resumed or multi-surface execution, agents MUST
compare prior claims to live evidence, record the delta, and repair stale
wording before advancing completion or promotion claims.

### 7. Surface-Bound Validation Evidence

When a required fetch, runtime check, or canonical validator cannot run on the
current surface, agents MUST record:

- the canonical command or endpoint,
- the failed/current surface,
- the owning retry surface,
- any portable substitute run and its rule/config divergence, and
- whether canonical re-validation is owed.

Portable substitute findings are not governed findings unless they match the
canonical validation contract or are separately verified on the owning surface.

## Canonical Surface Map

| Rule | Primary Surface | Enforcement Surface |
| --- | --- | --- |
| Authoritative-read discipline | `.ai_ops/workflows/crosscheck.md` | review evidence ledger + finding gate |
| Changed-files containment | `.ai_ops/workflows/crosscheck.md`; peer review template | unscoped sweep + declaration reconciliation |
| Closeout scope manifest | `.ai_ops/workflows/closeout.md` | closeout scope manifest before staging |
| Completion-claim parity | `.ai_ops/workflows/closeout.md` | closeout mirror-sync gate |
| Promotion-record parity | `.ai_ops/workflows/closeout.md` | promotion manifest + mirror debt markers |
| Resume-delta freshness | `.ai_ops/workflows/work.md` | resume contract and pre-write state check |
| Surface-bound validation evidence | `.ai_ops/workflows/crosscheck.md`; peer review template | unresolved external evidence field |

## CSCC Requirements

For cold-start, capacity-constrained agents, the active workbook, review file,
or closeout summary MUST preserve enough structured evidence to resume without
chat history:

- current scope and gated boundaries,
- changed-files declaration and reconciliation status,
- prior-claim versus live-evidence delta,
- unresolved external evidence with owning retry surface,
- completion or promotion mirror debt, if any.

## Change Log

- 0.1.0 (2026-07-07): Initial canonical spec promoted from conductor dogfood
  rules P-1, P-2, P-3, P-4, P-5, P-7, and P-11.
