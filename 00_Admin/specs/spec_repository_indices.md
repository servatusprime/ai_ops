---
title: Repository Indices Spec
id: spec_repository_indices
module: admin
status: stub
license: Apache-2.0
version: 0.1.0
created: 2026-01-15
updated: 2026-05-05
owner: ai_ops
ai_generated: true
spec_archetype: governance_spec
---

<!-- markdownlint-disable-next-line MD025 -->
# Repository Indices Spec

## 1. Purpose

Define the canonical index hierarchy so AI agents know which inventory is authoritative and how derived indices
are maintained.

## 1.1 Scope

Applies to repository index files that declare canonical or derived inventories for agents,
modules, AI core domain views, and workbook inventories.

## 2. Canonical Index

When the optional `01_Agents/` pattern is used, the canonical index for
executable agents and modules is:

- `01_Agents/metadata/agent_registry.yaml`

If `01_Agents/` is not present, use module metadata in
`02_Modules/01_agent_profiles/metadata/module.yaml` as the authoritative source
for agent profile configuration. In that case, there is no separate agent
registry file to regenerate.

## 3. Derived Indices

Derived indices include (when `01_Agents/` is used):

- `../<work_repo>/01_Agents/metadata/module_graph.yaml` (dependency graph)
- `../<work_repo>/01_Resources/<domain_core>/<domain_core>_index.yaml` (AI core domain view)
- `../<work_repo>/01_Resources/<domain_core>/ai_workbook_index.yaml` (workbook inventory view)

Derived indices MUST NOT override canonical records.

## 4. Update Protocol

1. Update the canonical index first.
2. Regenerate derived indices from the canonical source.
3. Validate references in guides and specs after regeneration.

## 5. Validation

Validators SHOULD confirm:

- canonical index exists and is readable,
- derived indices are in sync with canonical records,
- references to indices in guides point to the correct hierarchy.

## 6. Related References

- Guide: `00_Admin/guides/ai_operations/guide_repository_indices.md`

## Change Log

- 0.1.0 (2026-05-05): Metadata normalized to declare spec_archetype.
  Existing version history remains in Git history and prior frontmatter dates.
