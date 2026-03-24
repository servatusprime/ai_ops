---
title: Guide: Naming Architecture (ai_ops)
version: 0.3.1
status: active
license: Apache-2.0
last_updated: 2026-03-24
owner: ai_ops
related:
  - ../../policies/policy_naming_conventions.md
  - ./guide_naming_conventions.md
---

# Guide: Naming Architecture

**Scope:** Semantic naming model for ai_ops. This guide defines what names mean and where naming decisions live. It
does not redefine file/folder syntax rules.

## 1) Purpose

Use this guide to keep naming intent consistent across modules, projects, and artifacts:

- **Naming architecture** = semantic layers (platform, capability, artifact, output)
- **Naming conventions** = concrete syntax/prefix rules

Canonical syntax rules remain in `00_Admin/guides/architecture/guide_naming_conventions.md`.

## 2) Canonical Definitions

- **Module:** Reusable capability package used across many tasks/repos.
- **Project:** Bounded implementation effort with a specific outcome, timeline, and deliverables.

Use these definitions consistently in guides, specs, and metadata.

## 3) Naming Layers

1. **Platform layer**
   - Repo/system identity names (for example, repo title, tool family name).
2. **Capability layer**
   - Module names and stable IDs (`module_id`) used in metadata and orchestration.
3. **Artifact layer**
   - Document/script/spec/runbook/workflow names.
4. **Output layer**
   - Generated reports/exports/build artifacts.

Rule: each layer should remain swappable without forcing broad refactors in other layers.

## 4) Tokenized References

When cross-repo reuse is expected, prefer neutral tokens over hard-coded repo or domain names.

Example token set:

```yaml
tokens:
  WORK_REPO: "<work_repo>"
  MODULE_ID: "<module_id>"
  ARTIFACT_SCOPE: "<scope>"
```

Use tokens in templates/examples; resolve to concrete values during implementation.

## 5) Usage Rules

- Keep domain/business branding out of ai_ops canonical docs.
- Keep module IDs stable once published.
- Prefer neutral examples in ai_ops; domain-specific examples belong in target/work repos.
- If a name change is needed, update metadata and pointers in one controlled change set.

### 5.1 Display Name vs Filesystem Name (Governance Rule)

- Display/product names are mutable labels.
- Filesystem/module paths are stable identifiers by default.
- `module_id` is the canonical cross-artifact token.

Hard rename gate for path-level renames:

1. Dedicated migration workbook approved.
2. Reference inventory and update plan completed.
3. Validation plan includes metadata/tests/path references.
4. Migration executed as one controlled change set.

## 6) Relationship to Other Guides

- **Naming syntax/prefixes/date formats:**
  `00_Admin/guides/architecture/guide_naming_conventions.md`
- **Where artifacts belong:**
  `00_Admin/guides/architecture/guide_file_placement.md`
- **Top-level repository layout and folder roles:**
  `00_Admin/guides/architecture/guide_repository_structure.md`

## 7) Change Control

When updating naming architecture:

1. Update this guide first (semantic intent).
2. Update naming conventions only if syntax rules change.
3. Update metadata/templates that depend on changed terms.
4. Record rationale in decision docs when change affects multiple modules/repos.

## 8) Changelog

- **0.2.0 - 2026-02-02:** Rewritten as repo-agnostic semantic guide; removed malformed duplicate front matter and
  domain-specific naming catalog.
