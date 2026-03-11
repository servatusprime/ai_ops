---
title: Requirements Traceability Matrix Template
version: 0.1.0
status: active
updated: 2026-02-24
owner: ai_ops
license: Apache-2.0
---

# Requirements Traceability Matrix

This file tracks the relationship between **requirements (REQ IDs)**, **code implementation**, and **tests**.  
Every normative requirement (`REQ-<SPEC>-<SECTION>-<NNN>`) from the specifications should appear here.

## AI-First Guidance

- Keep rows concise and machine-readable.
- Prefer explicit file/function paths over narrative notes.

---

## Usage Guidelines

- Each requirement ID MUST appear in exactly one row.
- `Code Pointer` should reference the module/function/file where implemented.
- `Test Case` should reference the automated test name/path (or manual test doc).
- `Status` values: `draft`, `in-progress`, `passing`, `failing`, `deprecated`.

---

## Matrix

<!-- markdownlint-disable MD013 -->
| REQ ID | Spec Reference | Code Pointer | Test Case | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| REQ-API-3.1-001 | [API Spec Sec.3.1](../specs/API_SPEC.md#31-auth) | /src/auth/jwt.py:validate_token() | tests/test_auth.py::test_jwt | passing | - |
| REQ-API-3.1-002 | [API Spec Sec.3.1](../specs/API_SPEC.md#31-auth) | /src/auth/expiry.py:TTL | tests/test_auth.py::test_ttl | failing | Token expiry >60min |
| REQ-DATA-2.2-005 | [Data Model Sec.2.2](../specs/DATA_MODEL.md#22-types) | /src/models/data_types.py:DateField | tests/test_data.py::test_date | in-progress | - |
<!-- markdownlint-enable MD013 -->

---

## Change Log

- 2025-09-30: Template created.
