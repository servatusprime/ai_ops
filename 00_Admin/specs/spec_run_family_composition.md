---
title: Run-Family Composition Spec
id: spec_run_family_composition
module: admin
status: active
license: Apache-2.0
version: 0.1.1
created: 2026-07-16
last_updated: 2026-07-16
owner: ai_ops
ai_generated: true
spec_archetype: governance_spec
---

<!-- markdownlint-disable MD013 MD025 -->

# Run-Family Composition Spec

## Purpose

Define reusable, many-to-many composition for runprograms, runbundles, and
runbooks without making filesystem containment an ownership boundary.

## Relationship to Shared Identity

This is a purpose-specific view governed by
`spec_artifact_graph_identity.md`. Run-family artifacts inherit its stable-ID,
single-home, provenance, authority, alias, and impact rules.

## Legal Composition

The only legal direct consumption directions are:

- `runprogram -> runbundle`; and
- `runbundle -> runbook`.

A runprogram MAY consume a runbundle also consumed by other runprograms. A
runbundle MAY consume a runbook also consumed by other runbundles. The graph
MUST be acyclic. Containment MAY be used for convenient storage, but membership
and execution order come from explicit references, not directory ancestry.

## Consumer Manifest Authority

Every graph-addressable runprogram, runbundle, or runbook MUST expose a
colocated `manifest.yaml`. For this purpose-specific run-family contract, the
colocated manifest is the only machine authority for identity and composition;
generic artifact-frontmatter authority does not apply. A runprogram or
runbundle manifest owns its outgoing `consumes` edges. Each edge MUST provide:

- `consumer_id` and `provider_id`;
- `version_constraint` and compatible `interface_version` expectation;
- `parameter_profile`;
- route or queue order;
- gate and optionality data;
- entry and exit artifacts;
- idempotency semantics; and
- retry semantics where applicable.

`consumed_by`, affected-consumer closure, human navigation, and graph views are
derived. They MUST NOT be hand-maintained authority.

## Resolution Contract

The initial resolver MUST select the single canonical provider for each stable
ID, evaluate its declared constraint and interface compatibility, resolve the
transitive route deterministically, and fail on ambiguity or incompatibility.
General selection among competing provider versions is future work.

Resolution MUST emit:

1. a minimal context pack containing the selected route, transitive artifact
   set, resolved paths/interfaces, required gates, and source hashes; and
2. a run-instance lock containing exact IDs, artifact/interface versions,
   paths, parameters, content hashes, route, gates, and receipt references.

## Run Receipt

A run receipt MUST reference the run-instance lock and its hash and record run
ID, inputs, outputs, gates, validations, affected-consumer receipts or approved
dispositions, and completion state. Reusable definitions and run evidence MUST
remain separate.

## Canonical Homes and Indexes

- Runbooks retain valid repo- or module-owned canonical homes.
- Runprograms and runbundles use neutral repo- or module-owned homes; they MUST
  NOT require an exclusive consumer parent.
- `00_Admin/runbooks/run_family_registry.yaml` is the generated repo-level
  machine index.
- `02_Modules/<module>/metadata/module.yaml` provides a module discovery
  pointer; an optional module aggregate may live at
  `02_Modules/<module>/metadata/run_family_registry.yaml`.
- `00_Admin/runbooks/README.md` is the human navigation surface and MUST be
  mechanically checked against the registry.
- Tracked derived graph views live under
  `00_Admin/reports/generated/graphs/` and remain non-authoritative.

## Compatibility and Deprecation

Every stable ID has one canonical home and one registry-backed discovery route.
An adoption map MUST either affirm the current path as the permanent canonical
home or move the artifact and update every consumer in the same governed batch;
it MUST NOT create a "legacy canonical" class or retain parallel discovery
paths. Contract v0.1 rejects every alias record and field. If a named consumer
cannot migrate atomically, the work stops for a separately approved Level-4
contract version that defines enforcement, removal ownership, and a fixed
removal date. An operator exception alone does not create a bridge, authority,
or valid closeout state.

## Shared-Artifact Completion

A change to a shared runbook or runbundle is not globally complete until every
affected declared consumer has a validation receipt or an operator-approved
disposition. One named writer/merge owner MUST serialize shared implementation
changes.

## Validation

Validators MUST reject duplicate IDs/homes, unresolved paths or edges, illegal
directions, cycles, incompatible interfaces, ambiguous providers, manual
reverse-index authority, copied forks, hidden parent defaults, nondeterministic
resolution, and missing affected-consumer dispositions.

## Generic Governed-Repository Adoption

`<governed_repo>` adoption MUST inventory existing artifacts, map stable IDs
and canonical homes, classify copies as canonical implementations, aliases,
migration candidates, or unauthorized forks, update consumers, validate fan-
out, and retain local project profiles and run evidence separately from shared
definitions. Canonical ai_ops artifacts MUST remain repository-neutral.

## Related References

- `00_Admin/specs/spec_artifact_graph_identity.md`
- `00_Admin/specs/spec_runbook_structure.md`
- `00_Admin/specs/spec_repository_indices.md`
- `00_Admin/guides/authoring/guide_runbooks.md`

## Change Log

- 0.1.0 (2026-07-16): Established many-to-many run-family composition,
  consumer-manifest authority, resolution, evidence, and adoption contracts.
