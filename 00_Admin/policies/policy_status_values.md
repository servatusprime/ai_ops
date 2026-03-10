---
title: Status Values Policy
version: 0.2.0
updated: 2026-02-12
status: active
license: Apache-2.0
---
<!-- markdownlint-disable MD025 -->

# Status Values Policy

## Purpose

Define the canonical status vocabulary for documents and metadata.

## Status Definitions

- `planned`: referenced but not started; file may not exist.
- `stub`: file exists with minimal content; needs expansion.
- `active`: implemented and in use; reasonably complete.
- `completed`: finished work; retained for reference.
- `deprecated`: superseded or being phased out; avoid new dependencies.

## Normalization Rules

- `draft`, `wip`, `in_progress` => `stub`.
- `beta` => `stub` unless explicitly designated `active`.
- `draft` MUST NOT be used in new work. Normalize it to `stub`.
- No other status values are allowed in new work.

## Allowed Transitions

- `planned` -> `stub` -> `active` -> `completed`.
- Use `deprecated` only when an artifact is superseded or explicitly phased out.
- Backwards transitions require explicit rationale in the owning artifact.

## Disposition Procedure for Deprecated Artifacts

When an artifact transitions to `deprecated`:

1. **Move** the file to `99_Trash/` (with an optional subdirectory for context).
2. Alternatively, **replace in-place** with a minimal stub containing only:
   - Front matter with `status: deprecated`
   - A pointer to the replacement artifact
3. **Do not** leave fully functional deprecated code in its original location
   with warning banners. In-place deprecation stubs must be inert (no working
   logic).
4. Update any references (README, manifest, registry) to remove or redirect
   the deprecated entry.

`99_Trash/` items are subject to ~30-day auto-purge per repository structure
policy. See `guide_repository_structure.md` for folder semantics.

## Quality Rule for Active

- A document MUST NOT be labeled `active` unless its structure conforms to its template (spec, prompt, matrix, plan,
  policy, guide, etc.).
