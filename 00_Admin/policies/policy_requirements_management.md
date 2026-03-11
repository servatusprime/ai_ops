---
title: Requirements Management Policy
version: 0.1.0
updated: 2025-12-02
status: active
license: Apache-2.0
---
<!-- markdownlint-disable MD025 -->

# Requirements Management Policy

## Purpose

Define how requirement IDs (REQs) are created, ordered, and traced.

## REQ ID Format

- `REQ_<module_code>_<numeric_id>`
- `<module_code>` = module folder name (e.g., `gis_workflow`, `analysis_engine`, `financial_modeling`).
- `<numeric_id>` = zero-padded integer (0001, 0002, ...).

## Ordering & Stability

- Assign IDs monotonically in document order: first requirement -> `_0001`, second -> `_0002`, etc.
- Preserve REQ order during refactors; do not renumber existing REQs except during a deliberate major reset.
- If a requirement is removed, its ID is retired and MUST NOT be reused.
- New requirements are appended at the end of the sequence.

## Requirements Matrices

- Matrices must use the exact same REQ IDs as the corresponding spec.
- Include columns at minimum: REQ ID, Description, Source Doc, Status.
- Matrix status values MUST be one of: planned, stub, active, completed, deprecated.
- The matrix is the traceability companion to the spec, not a separate source of IDs.
