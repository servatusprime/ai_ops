---
title: Guide: Runprograms
version: 0.2.0
status: active
license: Apache-2.0
last_updated: 2026-08-10
owner: ai_ops
related:
- 00_Admin/guides/ai_operations/guide_workflows.md
- 00_Admin/guides/ai_operations/guide_ai_ops_vocabulary.md
- 00_Admin/guides/ai_operations/guide_execution_spines.md
- 00_Admin/guides/authoring/guide_runbooks.md
- 00_Admin/specs/spec_run_family_composition.md
- 00_Admin/specs/spec_artifact_graph_identity.md
---

<!-- markdownlint-disable MD013 MD025 -->

# Guide: Runprograms

## Purpose and scope

A **Runprogram** is an execution-level container that coordinates a set of
**runbundles** in a required order. It sits at the top of the run-family
composition `runprogram -> runbundle -> runbook`.

This guide defines how to structure a runprogram and how it composes runbundles.
Enforceable requirements live in `00_Admin/specs/spec_run_family_composition.md`
and `00_Admin/specs/spec_artifact_graph_identity.md`. This guide is advisory; if
there is a conflict, the spec wins.

## Definition

A runprogram:

1. Coordinates a sequence of runbundles (which in turn coordinate runbooks).
1. Defines run-order dependencies, batch gates, and checkpoints.
1. Owns its outgoing `consumes` edges in a colocated `manifest.yaml`.
1. Uses an authored execution control graph (`execution_graph.yaml`) and,
   optionally, a pipeline artifact to sequence execution and hold gate
   visibility. A runprogram does not use a work-family execution spine.

Runprograms are not runbooks and are not executed directly. They are the
orchestration surface; the reusable implementations live in their own neutral
canonical homes and are consumed **by reference**.

## Composition, not containment

Membership and execution order come from **explicit references in the consumer
manifest**, not from directory ancestry. Two consequences:

- A runbundle MAY be consumed by more than one runprogram without being copied.
  Placing a runbundle inside a program folder does not make that program its
  owner (see `spec_artifact_graph_identity.md`, single-home and edge-authority
  rules).
- A runbundle has exactly **one** neutral canonical home. A program-contained
  candidate must be affirmed as the sole canonical home or moved to a neutral
  home in the same adoption batch; it cannot remain as a second compatibility
  location (see `guide_runbooks.md` section 2.1).

Runbundles are **not** informal groupings. Every graph-addressable runbundle
exposes a `README.md` plus a colocated `manifest.yaml`; structured frontmatter
is not a substitute for run-family graph authority.

## File Organization

Applies to run-family artifacts in both ai_ops and governed repos. Directory
layout carries **no** authority (authority is in manifests + stable IDs + the
generated registry), so the layout is chosen for least fragility and AI/CSCC
ergonomics, not for correctness.

- **Folder-per-artifact.** Each runprogram, runbundle, and runbook is a folder
  holding its own `manifest.yaml` plus companions (the artifact doc, tests,
  fixtures, and -- for a runprogram -- `execution_graph.yaml`). One bounded read
  yields full context. Use one uniform manifest name (`manifest.yaml`),
  discovered under the approved canonical homes, as the single discovery
  contract; do not mix in `<name>.manifest.yaml` sidecars, which force a second
  validator.
- **Home by steward, not by consumer.** An artifact's home is decided by who
  maintains it and the broadest scope covering all its consumers -- never placed
  under a consumer. A runbook shared across modules homes at the repo level; one
  shared within a module homes in that module. Consumers reference it by stable
  ID; "who consumes X" is the registry's derived reverse-index.
- **`canonical_home` is the one binding.** It is the single load-bearing path;
  update it in the same governed batch as any move, then regenerate. Everything
  else (inventory, reverse edges, human READMEs) is derived or parity-checked.
- **Kind buckets are optional.** Grouping folders as `programs/`, `bundles/`,
  `books/` is a human-scan convenience only, never an authority boundary.

### Minimum root documents

Every run-family home exposes two root surfaces at each applicable level, both
derived -- never a hand-authored inventory:

- a **generated machine index** (`run_family_registry.yaml`,
  `derived_non_authoritative`); and
- a **human-navigation README** that projects the registry and is
  mechanically parity-checked against it.

The same pattern repeats at three levels -- repo root, steward/module root, and
each artifact folder -- with the artifact's own `manifest.yaml`/README as the
leaf. Root guidance is a thin local layer that *references* canon, never a copy
of it. Start from
`01_Resources/templates/workflows/run_family_index_readme_template.md` and
`01_Resources/templates/workflows/run_family_manifest_template.yaml`.

## Required contents

Each runprogram folder MUST include:

1. **Program README** (`README.md`) -- purpose, consumed runbundles, execution
   strategy, and status. Use
   `01_Resources/templates/workflows/runprogram_readme_template.md`.
1. **Consumer manifest** (`manifest.yaml`) -- the machine authority for this
   program's outgoing `consumes` edges (each edge carries `consumer_id`,
   `provider_id`, `version_constraint`, `interface_constraint`,
   `parameter_profile`, route/queue order, gates, entry/exit artifacts, and
   idempotency/retry semantics). The edge's `interface_constraint` must be
   compatible with the provider identity's `interface_version`; the two field
   names are not interchangeable.
1. **Execution control graph** (`execution_graph.yaml`) -- the authored control
   surface: nodes (deterministic/agentic/operator), one reasoning owner, per-node
   CSCC onboarding, handoff scopes, routing conditions, and bounded loops with
   escalation. Authoritative for control flow (see
   `00_Admin/specs/spec_execution_control_graph.md`). A runprogram uses the
   control graph, not a work-family execution spine.

Optional:

1. **Program pipeline** (`runprogram_pipeline_<nn>.md`) -- execution-queue
   mirror synced after the control graph; the control graph wins on conflict.
1. **Program Spec** (`spec_<program_id>.md`) when the program needs a formal
   specification beyond the control graph.
1. Environment/readiness notes and validation gates; reference packs for
   handoff.

## Location and naming

Runprograms use a neutral repo- or module-owned home:

- Cross-cutting: `00_Admin/runbooks/run_program_<program_id>/`
- Module-specific: `02_Modules/<module>/docs/runbooks/run_program_<program_id>/`

Naming rules:

- `program_id` is lower_snake_case.
- Keep runprogram orchestration artifacts inside a single folder named
  `run_program_<program_id>/`.
- Consumed runbundles and runbooks are referenced by stable ID and a path
  resolved from the manifest; they live in their own neutral homes.

## Structure (example)

```text
00_Admin/runbooks/run_program_<program_id>/
  README.md
  manifest.yaml            # authoritative consumes edges (-> runbundles)
  execution_graph.yaml     # authored control surface (routing/loops/escalation)
  runprogram_pipeline_01.md  # optional queue mirror

# consumed runbundles live in their own neutral homes and are
# referenced by stable ID + resolved path, not copied under the program:
00_Admin/runbooks/rnb_<bundle_name>/
  README.md
  manifest.yaml            # authoritative consumes edges (-> runbooks)
  runbooks/
    rb_<step_00>.md
```

## Runbundle vs Runprogram

| Aspect | Runbundle | Runprogram |
| --- | --- | --- |
| Role | Groups and sequences runbooks | Coordinates runbundles across a program |
| Authority | Colocated `manifest.yaml` (required) | Colocated `manifest.yaml` (required) |
| Coordination | README + optional local pipeline | README + `execution_graph.yaml` (+ optional pipeline) |
| Use when | Runbooks are frequently executed together | Multiple runbundles run in a required, gated order |
| Home | One neutral `rnb_<bundle_name>/` home | One neutral `run_program_<program_id>/` home |

## Shared providers and staged programs

- **Shared reuse.** A runprogram MAY consume a runbundle also consumed by other
  runprograms. Before changing a shared runbundle or runbook, resolve all
  declared consumers, name one merge owner, and require a validation receipt or
  operator-approved disposition for each affected consumer (see
  `spec_run_family_composition.md`, Shared-Artifact Completion). A provider MAY
  publish a **suitability receipt** declaring the interface and validated
  capabilities that consumers bind to.
- **Staged reconciliation.** When a program reconciles or blends inputs across
  ordered stages, preserve distinct artifact identities across stages, declare
  the stage order and boundary assumptions, and carry a per-stage
  `candidate -> validated -> accepted` disposition (see the runprogram README
  template, Staged Reconciliation and Identity Preservation).
- **Intake providers.** When a consumed runbundle admits heterogeneous inputs,
  it carries an Intake / Admission Contract so nothing is admitted or dropped
  silently (see `guide_runbooks.md` section 2.1).

## Graph surfaces

A runprogram has two distinct graph surfaces; do not conflate them.

- **Authored execution control graph** (`execution_graph.yaml`, colocated) is the
  control surface. It declares nodes (deterministic/agentic/operator), one
  reasoning owner, per-node CSCC onboarding, handoff scopes, routing conditions,
  and bounded loops with escalation, and is authoritative for control flow. For
  multi-route programs it is the routing authority (named `routes` with
  per-route node profiles); `critical: true` edges pin fail-closed control sets.
  See
  `00_Admin/specs/spec_execution_control_graph.md` and
  `01_Resources/templates/workflows/execution_graph_template.yaml`. Validate with:

  ```powershell
  python 00_Admin/scripts/validate_run_family_graph.py --execution-graph run_program_<id>/execution_graph.yaml
  ```

- **Derived composition/impact views** (`00_Admin/runbooks/run_family_registry.yaml`
  and the graph views under `00_Admin/reports/generated/graphs/`) are
  non-authoritative lookup layers generated from the manifests. They answer "what
  exists / who consumes whom / who is affected," never "what runs next."

Keep the derived views current: manifests are the authored input; after adding or
changing a `manifest.yaml`, regenerate the derived views and validate them.

```powershell
python 00_Admin/scripts/generate_run_family_views.py --repo-root . --write
python 00_Admin/scripts/generate_run_family_views.py --repo-root . --check
python 00_Admin/scripts/validate_run_family_graph.py --discover --check-files
```

## Cost Governance

The `cost_governance:` field is optional frontmatter available in all execution
artifact types including runbundles and runprograms. Absence means thrift
judgment applies without a hard budget constraint. See
`00_Admin/specs/spec_cost_governance.md` for the full schema.

## References

- `00_Admin/specs/spec_run_family_composition.md`
- `00_Admin/specs/spec_artifact_graph_identity.md`
- `00_Admin/specs/spec_execution_control_graph.md`
- `00_Admin/guides/authoring/guide_runbooks.md`
- `00_Admin/guides/ai_operations/guide_execution_spines.md`
- `00_Admin/specs/spec_cost_governance.md`
