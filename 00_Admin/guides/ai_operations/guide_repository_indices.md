---
title: Guide: Repository Indices
version: 0.1.0
status: active
license: Apache-2.0
last_updated: 2026-01-31
owner: ai_ops
related:
- ../../specs/spec_repository_indices.md
---

# Guide: Repository Indices

This guide explains how canonical and derived indices are used and maintained.

## 1) Canonical vs derived indices

- Canonical indices are the source of truth.
- Derived indices are regenerated views and must not override canonical records.

## 2) When to regenerate derived indices

Regenerate derived indices when:

- Canonical index entries change
- A structural change introduces new modules or registries
- A validator reports index drift

## 3) Validation expectations

Use the repository validator (or relevant runbooks) to confirm index consistency after regeneration.

## 4) Governance pointers

Enforceable requirements live in `spec_repository_indices.md`.
