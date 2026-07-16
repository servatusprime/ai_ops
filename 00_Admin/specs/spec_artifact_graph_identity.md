---
title: Artifact Graph Identity Spec
id: spec_artifact_graph_identity
module: admin
status: active
license: Apache-2.0
version: 0.1.2
created: 2026-07-16
last_updated: 2026-07-16
owner: ai_ops
ai_generated: true
spec_archetype: governance_spec
---

<!-- markdownlint-disable MD013 MD025 -->

# Artifact Graph Identity Spec

## Purpose

Define the shared identity, authority, provenance, and lifecycle contract used
by purpose-specific artifact graphs. A graph is a view over repository-owned
artifacts; it is not a second source of truth.

## Scope

This spec applies when a canonical artifact participates in a machine-readable
dependency, routing, consumption, or impact graph. Purpose-specific specs may
add fields and legal edges but may not redefine identity or authority.

## Identity Authority

Every graph-addressable artifact MUST have one stable identity record with:

- `artifact_id`: stable identifier, unique within the repository;
- `artifact_kind`: canonical artifact class;
- `canonical_home`: one resolved repo-relative path;
- `artifact_version`: exact version of the implementation;
- `interface_version`: compatibility boundary exposed to consumers;
- `lifecycle`: current lifecycle state; and
- `steward`: authority responsible for the canonical implementation.

The identity record MUST live in artifact frontmatter or a colocated manifest.
The artifact or manifest is authoritative. Registries, indexes, graph views,
context packs, and receipts MUST reference the identity; they MUST NOT mint a
competing ID, home, version, lifecycle, or steward.

Filesystem placement communicates artifact kind and stewardship. It MUST NOT
be interpreted as exclusive ownership by a parent consumer.

## Edge Authority and Provenance

Every graph edge MUST declare or deterministically inherit:

- `provenance`: `explicit`, `derived`, or `inferred`; and
- `authority`: `canonical`, `derived`, `local`, or `discovery`.

Only an explicit edge declared by its authority source, or a deterministic
derived edge generated from canonical inputs, may influence execution.
Inferred edges are questions for review and MUST remain sandbox/local until an
authorized canonical source declares them.

An outgoing dependency edge is owned by the consumer unless a purpose-specific
spec names another authority. Reverse edges and transitive closures are derived.
Manually maintained reverse edges MUST NOT be treated as authority.

## Single-Home and Alias Rules

- One stable artifact has exactly one canonical home at a resolved version.
- Two stable IDs MUST NOT claim the same canonical implementation path.
- Compatibility aliases are unsupported and rejected by contract v0.1. An
  operator exception alone is insufficient: a named consumer that cannot
  migrate in the same batch requires a separately approved Level-4 contract
  version defining and enforcing a reference-only bridge. Any future bridge
  MUST identify its one canonical target and MUST NOT contain executable,
  normative, registry, or discovery authority.
- When a future approved contract version enables a reference-only bridge, its
  alias record MUST declare `alias_id`, `target_id`, `target_path`,
  `deprecated_since`, `remove_after`, and `removal_owner`, and `remove_after`
  MUST act as a hard closeout gate that blocks completion once expired. These
  fields set the minimum bar for that future contract; under v0.1 no alias
  record or field is valid.
- A copied implementation is a fork, not an alias, and requires its own
  identity and explicit compatibility disposition.

## Derived Views

Tracked derived views MUST be reproducible from declared canonical inputs and
record generator identity/version. They MUST be replaceable without loss of
authority. Local portfolio views belong under `.ai_ops/local/`; inferred and
experimental views belong in sandbox/local surfaces until promoted.

## Change and Impact Contract

Before changing a shared artifact, the execution lane MUST resolve affected
declared consumers, assess interface compatibility, serialize shared-file
writes under one merge owner, and collect a validation receipt or an
operator-approved disposition for every affected consumer.

## Validation

Validators MUST reject duplicate IDs, duplicate homes, missing canonical
paths, invalid lifecycle/version fields, competing authority records, manually
authoritative reverse edges, and aliases containing copied implementation.

## Related References

- `00_Admin/specs/spec_run_family_composition.md`
- `00_Admin/specs/spec_repository_indices.md`
- `00_Admin/specs/spec_repo_metadata_standard.md`

## Change Log

- 0.1.0 (2026-07-16): Established shared artifact identity, edge authority,
  provenance, alias, and affected-consumer contracts.
