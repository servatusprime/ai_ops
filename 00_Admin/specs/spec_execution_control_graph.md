---
title: Execution Control Graph Spec
id: spec_execution_control_graph
module: admin
status: active
license: Apache-2.0
version: 0.1.5
created: 2026-08-10
last_updated: 2026-08-11
owner: ai_ops
ai_generated: true
spec_archetype: governance_spec
---

<!-- markdownlint-disable MD013 MD025 -->

# Execution Control Graph Spec

## Purpose

Define the authored, per-runprogram **execution control graph**: the control
surface that governs routing, handoffs, loops, and escalation for run-family
execution. It is authoritative for control flow, in contrast to the derived,
non-authoritative composition/impact graph, which remains a read-only lookup
layer.

## Relationship to Existing Specs

- Identity and composition stay authoritative only in colocated `manifest.yaml`
  (`spec_artifact_graph_identity.md`, `spec_run_family_composition.md`). The
  control graph MUST NOT mint identity or `consumes` edges.
- The derived composition/impact graph and registry
  (`spec_repository_indices.md`) remain `derived_non_authoritative`. The control
  graph MAY read them; a derived view MUST NOT be used as a control surface.
- The control graph is the run-family control surface. It supersedes the prose
  sequence/handoff/checkpoint mechanics of `execution_spine.md` **for
  runprograms only**. The execution spine remains an ephemeral work-family
  artifact (workprograms/workbundles) and is unchanged.

## Scope and Non-Goals

In scope:

- Run-family execution control: runprograms, and runbundles that meet the
  subordinate-graph threshold.

Non-goals:

- The **work-family** execution spine (workprograms/workbundles) is unchanged.
  This spec does not retire the spine for work-family artifacts.
- Identity, composition, resolution, and receipt contracts, which remain owned
  by their existing specs.

## Location and Cardinality

- One `execution_graph.yaml` per runprogram, colocated in
  `run_program_<program_id>/`. Never one shared document across runprograms.
- A runbundle MAY carry a subordinate `execution_graph.yaml` **only** when it
  has real internal branching or loops; otherwise the runbundle is a single
  node in the parent runprogram graph.
- The graph is the control authority; the README is its human projection; the
  `manifest.yaml` remains authoritative for identity and composition.
- The graph names the artifact it controls by stable ID (`owner_id`), not by
  path. The control graph is a satellite of that runprogram/runbundle, not an
  independently graph-addressable artifact; binding by ID keeps it correct
  across folder moves (least-fragile organization).

## Definition Versus Instance

- The graph file is the reusable **definition** (Execution axis, persistent):
  nodes, edges, kinds, loops, ownership.
- The per-run **instance** (resolved inputs/outputs, gates, hashes) is the
  resolver context pack plus run-instance lock (Commitment axis, run-scoped).
  This instance is the CSCC read-unit. Definitions and run evidence stay
  separate.

## Run-Instance Execution State (Resumable)

Graph execution is resumable through a **run-state** artifact, separate from the
definition and non-authoritative. It freezes the exact graph and records progress
so a cold-start, capacity-constrained agent can resume without session memory:

- `owner_id` (stable ID of the runprogram/runbundle being executed) plus
  `graph_ref` and `graph_sha256` (the exact definition this run executes;
  `owner_id` + hash are the authoritative binding, `graph_ref` a locator);
- `run_instance_id` and `status` (`running` | `complete` | `escalated` |
  `blocked`);
- `current_node` (required while `running`) and `completed_nodes`;
- `loop_counters` (per loop edge; never exceeding that edge's `max_cycles`); and
- `handoff_receipts` (evidence returned by completed nodes).

Canonical shape:
`00_Admin/configs/validator/schema_execution_graph_run_state.yaml`. Validate,
optionally cross-checked against the graph, with
`validate_run_family_graph.py --execution-graph-state <path> [--execution-graph <path>]`.

## Ownership Contract

- The graph declares exactly one program-level `reasoning_owner`. That owner
  holds end-to-end ownership of the reasoning.
- Nodes may be delegated to executors, but delegated nodes return to the owner
  under a declared return contract. Delegation MUST NOT fragment the reasoning
  across multiple owners.

## Node Contract

Each node declares:

- `id`: unique within the graph.
- `kind`: `deterministic` | `agentic` | `operator`.
  - `deterministic`: a script/tool with fixed behavior; MUST be idempotent and
    content-hashed (replayable and verifiable by hash).
  - `agentic`: requires judgment; MUST produce evidence or a receipt and be
    gated; MUST declare a bounded `onboarding.required_context_pack`.
  - `operator`: a human decision/gate.
- `interface`: `consumes` and `produces` declared as stable interface
  references, with `binding: resolved_per_run`. Concrete inputs/outputs are
  derived per project from admission receipts and manifests, not rigidly
  enumerated (municipal data varies per project).
- `onboarding.required_context_pack` (agentic nodes): the bounded read set a
  CSCC subagent needs to execute the node self-contained.
- `handoff`: `return_contract` (result shape) and `write_scope` (permission
  envelope; what the node may touch).
- `gate`: the precondition that must pass before downstream nodes run.
- `executor_ref` (optional): a stable reference to the runbook, script, or tool
  that executes the node.

## Edge Contract

Each edge declares `from`, `to`, and a routing `condition`. An edge MAY also
declare **transition (handoff) controls** -- optional, but validated when
present (adopted from governed-repo edge-controls, without their
`present_unvalidated` state marker since ai_ops enforces rather than declares):

- `entry_evidence`: the evidence required to cross the transition.
- `exit_evidence`: the evidence the transition must produce.
- `receipt_contract`: the named receipt contract written when the edge is
  traversed.
- `checkpoint`: when a resumable run-state checkpoint is persisted for this
  transition -- `none` | `before_edge` | `after_receipt` |
  `before_edge_and_after_receipt`.
- `critical`: when `true`, the edge is **fail-closed** and MUST declare all four
  transition controls above. This lets a program pin the edges where controls
  are mandatory, so a migration cannot fail open by dropping them.

An edge MAY be a loop:

- `loop.condition`: what triggers rework.
- `loop.max_cycles`: integer >= 1.
- `loop.on_exceed.escalate_to`: `reasoning_owner` or `operator`.

Rules:

- The graph MUST be acyclic except where an edge is explicitly declared a loop.
- Every loop MUST declare `max_cycles` and `on_exceed.escalate_to`.
- Escalation MUST terminate at the `reasoning_owner` or the operator. Sideways
  or unbounded agentic loops are rejected.

## Routing (Multi-Route Programs)

The execution control graph is the authority for **multi-route** sequencing. A
program with more than one named route declares an optional `routes` block; the
manifest `route_order` is a single-route convenience only and MUST NOT be relied
on to express multiple routes.

- Each route declares `route_id` (unique) and an ordered `sequence` of node
  steps; a step names a graph `node`, an `order` (>= 1), and an optional
  `profile` (a route-specific parameter/mode for that node).
- The same node MAY appear in several routes with different `profile`s and
  orders; this preserves programs where one runbundle is invoked in two routes
  with different modes without flattening them.
- A route MAY declare `depends_on_route`, which MUST reference another declared
  route.
- Routes name orderings over nodes; they do not mint composition edges (those
  stay in the manifest) and do not replace the edge/condition control layer.

## Authority Boundary

- The control graph is authored and approved; it is authoritative for routing,
  gates, and loops.
- It MUST NOT contain identity or composition authority (those stay in the
  manifest) and MUST NOT be generated from or treated as a derived view.
- A derived composition/impact graph MUST NOT be used to route, gate, or
  escalate execution.

## Validation

`validate_run_family_graph.py --execution-graph <path>` MUST reject:

- missing or empty `owner_id` or `reasoning_owner`;
- any unsupported top-level, node, or edge field (schema/runtime parity);
- a node without a valid `kind`;
- an `agentic` node without a non-empty `onboarding.required_context_pack`;
- a `deterministic` node without an idempotency/content-hash declaration;
- a node `interface` missing `binding: resolved_per_run`;
- a loop edge missing `max_cycles` or `on_exceed.escalate_to`;
- an `escalate_to` target that is not `reasoning_owner` or `operator`;
- a duplicate node id;
- an `agentic` node without a `gate`, or without both `handoff.return_contract`
  and `handoff.write_scope` (the permission envelope);
- a cycle that is not an explicitly declared loop;
- an edge referencing an unknown node id;
- an edge `checkpoint` outside the allowed set, or an empty `entry_evidence`,
  `exit_evidence`, or `receipt_contract` when the field is present;
- an edge marked `critical: true` that omits any of the four transition
  controls;
- a route with a missing or duplicate `route_id`, an unknown `node`, an `order`
  below 1, or a `depends_on_route` that references no declared route;
- identity or `consumes` composition fields embedded in the graph.

`validate_run_family_graph.py --execution-graph-state <path>` MUST reject a
run-state whose `owner_id` is empty or (when a graph is supplied) does not equal
the graph's `owner_id`, whose `graph_sha256` does not match the supplied graph,
whose `current_node` or `completed_nodes` are not graph nodes, whose loop counter
exceeds the edge's `max_cycles`, or that carries an unsupported field. The receipt and execution-graph validators run
standalone (no composition source required).

## Related References

- `00_Admin/specs/spec_artifact_graph_identity.md`
- `00_Admin/specs/spec_run_family_composition.md`
- `00_Admin/specs/spec_repository_indices.md`
- `00_Admin/guides/ai_operations/guide_run_programs.md`
- `00_Admin/configs/validator/schema_execution_graph.yaml`
- `00_Admin/configs/validator/schema_execution_graph_run_state.yaml`

## Change Log

- 0.1.5 (2026-08-11): The graph is now the explicit authority for multi-route
  sequencing (optional `routes` block with per-route node profiles and
  `depends_on_route`); added `critical` fail-closed edges that require the full
  transition-control set. Resolves governed-repo design-crosscheck C-01/C-02.
- 0.1.4 (2026-08-11): Closed fail-open enforcement gaps -- run-state `owner_id`
  must be non-empty and equal the graph's when supplied, agentic nodes must
  declare `handoff.write_scope`, and unsupported top-level/node/edge/run-state
  fields are now rejected for schema/runtime parity.
- 0.1.3 (2026-08-11): Adopted governed-repo edge-controls as optional, enforced
  edge transition controls -- `entry_evidence`, `exit_evidence`,
  `receipt_contract`, and a `checkpoint` policy -- dropping the
  `present_unvalidated` state marker in favor of validation.
- 0.1.2 (2026-08-11): Bound the graph and its run-state to the controlled
  artifact by stable ID (`owner_id`), not path -- least-fragile organization;
  the graph is a satellite of its runprogram/runbundle.
- 0.1.1 (2026-08-11): Added the resumable run-instance execution-state contract
  (graph hash, current/completed nodes, loop counters, handoff receipts) and its
  schema/validator; enforced agentic gate + handoff and duplicate-node-id
  rejection; added optional node `executor_ref`; noted standalone validator runs.
- 0.1.0 (2026-08-10): Established the authored run-family execution control
  graph, distinct from the derived non-authoritative view: node/edge contract,
  deterministic/agentic/operator kinds, single reasoning owner, per-run I/O
  binding, bounded loops with escalation, and validator enforcement.
