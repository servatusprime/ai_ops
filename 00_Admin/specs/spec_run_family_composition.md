---
title: Run-Family Composition Spec
id: spec_run_family_composition
module: admin
status: active
license: Apache-2.0
version: 0.3.1
created: 2026-07-16
last_updated: 2026-09-08
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
- `version_constraint` and an `interface_constraint` compatible with the
  provider identity's `interface_version` (the edge field is
  `interface_constraint`; the two field names are distinct);
- `parameter_profile`;
- route or queue order;
- gate and optionality data;
- entry and exit artifacts;
- idempotency semantics; and
- retry semantics where applicable.

The route/queue order on an edge is a **single-route convenience**. For programs
with more than one route, the authority for multi-route sequencing is the
execution control graph (`spec_execution_control_graph.md`, `routes`); the
manifest MUST NOT be relied on to express multiple routes.

`consumed_by`, affected-consumer closure, human navigation, and graph views are
derived. They MUST NOT be hand-maintained authority.

### Executability Closure

Structural composition validity is distinct from execution validity. When an
artifact has a colocated `execution_graph.yaml`, every interface named in a
node's `interface.consumes` MUST be satisfied by exactly one of:

- a `produces` interface on another node in the same graph;
- an interface admitted in the manifest's top-level `entry_artifacts`; or
- a `produces` interface on a graph owned by a provider declared in the
  manifest's outgoing `consumes` edges.

Operator-node outputs are ordinary graph-produced interfaces and may satisfy a
downstream external handoff through the declared provider edge. A repository-
wide union of outputs is not valid: an unrelated artifact must never satisfy a
graph's input. The companion closure entry point is
`00_Admin/scripts/validate_graph_artifact_closure.py`, backed by the canonical
run-family validator's explicit `--check-closure` flag; it is an executability
gate, not a replacement for structural validation.

`entry_artifacts` are node-interface identifiers, not prose descriptions.
Their source-specific meaning belongs in the profile or receipt consumed by the
run; the manifest only declares the graph boundary.

### Declared-Not-Consumed Profile Blocks

Parameter profiles MUST make the status of each top-level block explicit with
`block_classification`:

```yaml
block_classification:
  <block_name>: consumed | declaration
```

`consumed` means implementation code reads the block during execution and the
governed repository's profile-consumption validator is responsible for proving
that claim. `declaration` means the block is a governance or explanatory
record and MUST NOT be treated as an executable input. A block absent from the
classification is not an implicit live value; it is a contract defect. The
classification rule is generic ai_ops contract; proving code-level consumption
remains a governed-repository implementation because the consumer runtime is
repo-specific.

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
- Each graph-addressable artifact SHOULD be stored folder-per-artifact with a
  colocated `manifest.yaml` and its companions. The uniform manifest name
  `manifest.yaml`, discovered under the approved canonical homes, is the single
  discovery contract; a `<name>.manifest.yaml` sidecar is not a canonical
  discovery surface and MUST NOT require a second discovery/validator
  implementation.
- An artifact is homed by its steward at the broadest scope covering all declared
  consumers; it MUST NOT be homed under a consumer. A shared artifact gets a
  neutral home and is referenced by stable ID. Directory layout never conveys
  authority (see `spec_artifact_graph_identity.md`).
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
it MUST NOT create a second canonical class or retain parallel discovery
paths. Contract v0.1 rejects every alias record and field. If a named consumer
cannot migrate atomically, the work stops for a separately approved Level-4
contract version that defines enforcement, removal ownership, and a fixed
removal date. An operator exception alone does not create a bridge, authority,
or valid closeout state.

For compatibility with existing governed repositories, the manifest's
`promotion_target`, `promotion_gate`, and top-level `entry_artifacts` fields
are optional in contract v0.1. The promotion fields are strictly validated
when present. `entry_artifacts` remains a string array for legacy manifests;
only values matching the node-interface identifier contract participate in
closure satisfaction. New ai_ops-authored manifests SHOULD use unique
node-interface identifiers. Making any of these fields required is a separate
contract-tightening change and MUST include an inventory, migration owner, and
same-batch validation of every affected consumer.

## Shared-Artifact Completion

A change to a shared runbook or runbundle is not globally complete until every
affected declared consumer has a validation receipt or an operator-approved
disposition. One named writer/merge owner MUST serialize shared implementation
changes.

## Provider Suitability Receipt

Shared-Artifact Completion governs the **consumer** side: known declared
consumers must each be validated or dispositioned before a shared change is
complete. A shared provider MAY additionally publish a **provider suitability
receipt** to serve **future** consumers that are not yet declared.

- A provider (runbundle or runbook) that is designed for reuse SHOULD publish a
  suitability receipt when it exposes normalized outputs or an interface that
  later, still-unknown consumers are expected to bind to.
- The receipt MUST reference the provider `artifact_id` and `interface_version`
  and declare: the exposed entry/exit artifacts, the validated capabilities and
  the evidence for each, known limits or excluded cases, and the run-instance
  lock or run receipt that substantiates it.
- The receipt is derived run evidence, not authority. It MUST NOT mint identity,
  redefine the interface, or substitute for a consumer's own affected-consumer
  validation when it later binds. A consumer still owns its own outgoing
  `consumes` edge and its affected-consumer validation.
- The receipt is optional under this contract. Its absence does not block a
  shared change; only undischarged **declared** consumers do.
- When a receipt is supplied it MUST be well-formed and complete. The canonical
  shape is `00_Admin/configs/validator/schema_run_family_provider_receipt.yaml`,
  enforced by `validate_run_family_graph.py --provider-receipt <path>`, which
  rejects malformed or incomplete records.

## Validation

Validators MUST reject duplicate IDs/homes, unresolved paths or edges, illegal
directions, cycles, incompatible interfaces, ambiguous providers, manual
reverse-index authority, copied forks, hidden parent defaults, nondeterministic
resolution, and missing affected-consumer dispositions. When a provider
suitability receipt or an intake/admission receipt is supplied, validators MUST
reject malformed or incomplete records (missing required fields, an item without
a disposition, missing provenance, or an admitted/converted item with no
admission evidence).

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
- `00_Admin/scripts/validate_graph_artifact_closure.py`
- `01_Resources/templates/workflows/run_family_execution_profile_template.yaml`

## Change Log

- 0.3.1 (2026-09-08): Restored v0.1 manifest compatibility for legacy
  consumers; promotion fields remain validated when present, legacy entry
  metadata is not executable closure evidence, and closure checking is exposed
  through the canonical run-family validator rather than a standing duplicate
  rule.
- 0.3.0 (2026-09-08): Added executable input closure, node-interface
  `entry_artifacts`, explicit promotion intent, declared-not-consumed profile
  classification, and the one-contract execution-profile reference.
- 0.2.2 (2026-08-11): Clarified that manifest edge route/queue order is a
  single-route convenience; the execution control graph is the authority for
  multi-route sequencing.
- 0.2.1 (2026-08-11): Added file-organization rules to Canonical Homes and
  Indexes -- folder-per-artifact with a single `manifest.yaml` discovery
  contract, and home-by-steward (never under a consumer) for shared artifacts.
- 0.2.0 (2026-08-10): Added the optional Provider Suitability Receipt to serve
  future, not-yet-declared consumers, complementing consumer-side
  Shared-Artifact Completion without weakening it; made supplied provider and
  intake/admission receipts validator-enforced (reject malformed or incomplete
  records) via `schema_run_family_provider_receipt.yaml`,
  `schema_run_family_intake_receipt.yaml`, and `validate_run_family_graph.py`;
  corrected the consumer-edge field name to `interface_constraint` (distinct
  from the provider identity's `interface_version`).
- 0.1.0 (2026-07-16): Established many-to-many run-family composition,
  consumer-manifest authority, resolution, evidence, and adoption contracts.
