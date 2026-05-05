---
title: Spec - Workbundle Placement Suggestion
id: spec_workbundle_placement_suggestion
module: admin
version: 0.1.0
status: active
license: Apache-2.0
created: 2026-02-24
updated: 2026-05-05
owner: ai_ops
owners: ["ai_ops"]
ai_generated: true
spec_archetype: governance_spec
description: Canonical contract for deterministic workbundle candidate suggestion during /work intake.
---

# Spec - Workbundle Placement Suggestion

## Purpose

Reduce placement ambiguity during `/work` by producing candidate workbundle
matches from request text and known bundle metadata.

## Inputs

- request text (one or more sentences)
- optional target repo
- indexed workbundle metadata (`README` purpose/scope lines)

## Outputs

- ordered candidate list with scores `[0.0, 1.0]`
- recommendation:
  - `match_existing`
  - `create_new`
  - `manual_confirm`

## Scoring Contract (MVP)

`score = weighted_keyword_overlap + intent_bonus - mismatch_penalty`

- weighted keyword overlap:
  - exact token match in title/purpose: `+0.30`
  - domain token match in scope: `+0.20`
  - execution-mode fit (process vs feature): `+0.10`
- intent bonus:
  - explicit lane words (`crosscheck`, `health`, `closeout`, `profiles`): `+0.10`
- mismatch penalty:
  - explicit out-of-scope conflict: `-0.30`

Thresholds:

- `>= 0.70`: strong match
- `0.45 - 0.69`: suggest with confirmation
- `< 0.45`: propose new workbundle

## Deterministic Behavior

- always return top 3 candidates when available
- include one-line rationale for each candidate
- never auto-create a workbook without explicit confirmation

## Placement Decision Echo Contract

`/work` relevance-gate records should include:

- `requested_scope_echo`
- `candidate_workbundle_echo`
- `relevance_result` (`match|mismatch|uncertain`)
- `placement_decision_echo`

## Failure Modes

- no indexed bundles -> return `create_new`
- sparse metadata -> return `manual_confirm`
- multi-topic request -> return grouped candidates by intent token

## Change Log

- 0.1.0 (2026-05-05): Metadata normalized to declare spec_archetype.
  Existing version history remains in Git history and prior frontmatter dates.
