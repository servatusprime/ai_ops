---
title: Repository Indices Spec
id: spec_repository_indices
module: admin
status: active
license: Apache-2.0
version: 0.3.0
created: 2026-01-15
updated: 2026-08-11
owner: ai_ops
ai_generated: true
spec_archetype: governance_spec
---

<!-- markdownlint-disable-next-line MD025 -->
# Repository Indices Spec

## Purpose

Define the canonical index hierarchy so AI agents know which inventory is authoritative and how derived indices
are maintained.

## Scope

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

### 3.1 Run-Family Indices and Graph Views

Run-family identity and outgoing consumption edges remain authoritative only in
colocated `manifest.yaml` files under the purpose-specific composition
contract. The following are derived:

- `00_Admin/runbooks/run_family_registry.yaml` (repo-level machine index);
- `02_Modules/<module>/metadata/run_family_registry.yaml` (optional module aggregate);
- `00_Admin/reports/generated/graphs/artifact_dependency_graph.yaml`;
- `00_Admin/reports/generated/graphs/run_family_graph.yaml`; and
- `00_Admin/reports/generated/graphs/governance_routing_graph.yaml`.

`00_Admin/runbooks/README.md` is the human navigation surface and MUST be
mechanically checked against the derived registry. Neither the human index nor a
graph view may become an independent source for IDs, homes, or `consumes` edges.

A derived view is never a control surface: routing, gates, loops, and escalation
for run-family execution live in the authored, per-runprogram execution control
graph (`spec_execution_control_graph.md`), not in these derived views. For a
cold-start, capacity-constrained (CSCC) agent, the bounded read-unit is the
resolver context pack plus run-instance lock for the specific run, not the whole
repo-wide graph.

**Minimum root documents (three levels).** Each run-family home exposes exactly
two root surfaces, both derived and neither hand-authored as an inventory: a
generated machine index (`run_family_registry.yaml`) and a human-navigation
README that projects it and is mechanically parity-checked against it. The
pattern repeats at three levels: repo root
(`00_Admin/runbooks/run_family_registry.yaml` + `00_Admin/runbooks/README.md`),
steward/module root (optional
`02_Modules/<module>/metadata/run_family_registry.yaml` + module README), and
each artifact folder (its `manifest.yaml` + its own README). Root guidance
references canon rather than restating it. Governed repos MUST follow the same
three-level pattern. Template:
`01_Resources/templates/workflows/run_family_index_readme_template.md`.

## 4. Update Protocol

1. Update the canonical index first.
2. Regenerate derived indices from the canonical source.
3. Validate references in guides and specs after regeneration.
4. Validate deterministic sort, source hashes, and human-index parity.

## 5. Validation

Validators SHOULD confirm:

- canonical index exists and is readable,
- derived indices are in sync with canonical records,
- references to indices in guides point to the correct hierarchy.
- run-family IDs and canonical homes are unique,
- generated reverse edges equal consumer-owned outgoing edges, and
- tracked graph views contain no manual authority.

## 6. Related References

- Guide: `00_Admin/guides/ai_operations/guide_repository_indices.md`
- Identity: `00_Admin/specs/spec_artifact_graph_identity.md`
- Run-family composition: `00_Admin/specs/spec_run_family_composition.md`

## Change Log

- 0.3.0 (2026-08-11): Added the run-family control-graph vs derived-view
  boundary, the CSCC context-pack read-unit, and the three-level minimum
  root-documents contract (generated index + parity-checked README at repo,
  steward, and artifact levels; governed repos included).
- 0.2.0 (2026-07-16): Added derived run-family registry, graph-view, and
  human-index parity contracts.
- 0.1.0 (2026-05-05): Metadata normalized to declare spec_archetype.
  Existing version history remains in Git history and prior frontmatter dates.
