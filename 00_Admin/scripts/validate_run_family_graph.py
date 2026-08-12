#!/usr/bin/env python3
"""Validate the ai_ops run-family graph contract without hidden authority."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

EXACT_SEMVER = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)
VERSION_CONSTRAINT = re.compile(
    r"^(?:(?:>=|<=|>|<|==|=)?[0-9]+(?:\.[0-9]+){0,2})"
    r"(?:,(?:>=|<=|>|<|==|=)?[0-9]+(?:\.[0-9]+){0,2})*$"
)
INTERFACE_VERSION = re.compile(r"^(0|[1-9][0-9]*)(?:\.(0|[1-9][0-9]*)){0,2}$")
SHA256 = re.compile(r"^[a-f0-9]{64}$")
KINDS = {"runprogram", "runbundle", "runbook"}
DIRECTIONS = {
    ("runprogram", "runbundle"),
    ("runbundle", "runbook"),
}
ARTIFACT_REQUIRED = {
    "artifact_id",
    "artifact_kind",
    "canonical_home",
    "artifact_version",
    "interface_version",
    "lifecycle",
    "steward",
    "content_sha256",
}
EDGE_REQUIRED = {
    "consumer_id",
    "provider_id",
    "version_constraint",
    "interface_constraint",
    "parameter_profile",
    "route_order",
    "optional",
    "gates",
    "entry_artifacts",
    "exit_artifacts",
    "idempotency",
}
ROOT_ALLOWED = {"schema_version", "artifacts", "consumes", "parameter_profiles"}
ARTIFACT_ALLOWED = set(ARTIFACT_REQUIRED)
EDGE_ALLOWED = set(EDGE_REQUIRED) | {"retry"}
RECEIPT_VERSION = "0.1.0"
DERIVED_NON_AUTHORITATIVE = "derived_non_authoritative"
PROVIDER_RECEIPT_REQUIRED = {
    "receipt_version",
    "authority",
    "provider_id",
    "interface_version",
    "entry_artifacts",
    "exit_artifacts",
    "validated_capabilities",
    "known_limits",
    "substantiated_by",
}
INTAKE_RECEIPT_REQUIRED = {
    "receipt_version",
    "authority",
    "provider_id",
    "source_snapshot",
    "items",
}
ADMISSION_DISPOSITIONS = {
    "admitted",
    "conversion_required",
    "reference_only",
    "quarantine",
    "unsupported",
    "blocked",
}
ADMISSION_EVIDENCE_REQUIRED = {"admitted", "conversion_required"}
GRAPH_VERSION = "0.1.0"
CONTROL_AUTHORITY = "authored_control_surface"
EXECUTION_GRAPH_REQUIRED = {
    "graph_version",
    "authority",
    "scope",
    "owner_id",
    "reasoning_owner",
    "nodes",
    "edges",
}
NODE_KINDS = {"deterministic", "agentic", "operator"}
ESCALATE_TARGETS = {"reasoning_owner", "operator"}
CHECKPOINT_POLICIES = {
    "none",
    "before_edge",
    "after_receipt",
    "before_edge_and_after_receipt",
}
EDGE_CONTROL_STRINGS = ("entry_evidence", "exit_evidence", "receipt_contract")
# Runtime allowlists mirror the schemas' additionalProperties: false (parity).
EXECUTION_GRAPH_ALLOWED = EXECUTION_GRAPH_REQUIRED | {"routes"}
CRITICAL_EDGE_CONTROLS = (
    "entry_evidence",
    "exit_evidence",
    "receipt_contract",
    "checkpoint",
)
NODE_ALLOWED = {
    "id",
    "kind",
    "interface",
    "determinism",
    "onboarding",
    "handoff",
    "gate",
    "executor_ref",
}
GRAPH_EDGE_ALLOWED = {
    "from",
    "to",
    "condition",
    "entry_evidence",
    "exit_evidence",
    "receipt_contract",
    "checkpoint",
    "critical",
    "loop",
}
RUN_STATE_ALLOWED = {
    "state_version",
    "authority",
    "owner_id",
    "graph_ref",
    "graph_sha256",
    "run_instance_id",
    "status",
    "completed_nodes",
    "loop_counters",
    "current_node",
    "handoff_receipts",
    "updated_at",
}
# Nested allowlists mirror the schemas' nested additionalProperties: false.
NODE_INTERFACE_ALLOWED = {"consumes", "produces", "binding"}
NODE_DETERMINISM_ALLOWED = {"idempotent", "content_hashed"}
NODE_ONBOARDING_ALLOWED = {"required_context_pack"}
NODE_HANDOFF_ALLOWED = {"return_contract", "write_scope"}
EDGE_LOOP_ALLOWED = {"condition", "max_cycles", "on_exceed"}
EDGE_LOOP_ON_EXCEED_ALLOWED = {"escalate_to"}
ROUTE_ALLOWED = {"route_id", "depends_on_route", "sequence"}
ROUTE_STEP_ALLOWED = {"node", "order", "profile"}
RUN_STATE_LOOP_COUNTER_ALLOWED = {"edge", "count"}
# Identity/composition authority that MUST stay in manifest.yaml, never the graph.
FORBIDDEN_GRAPH_FIELDS = {
    "artifact_id",
    "canonical_home",
    "consumes",
    "interface_version",
    "steward",
    "lifecycle",
}
RUN_STATE_VERSION = "0.1.0"
RUN_STATE_AUTHORITY = "derived_run_state_non_authoritative"
RUN_STATE_REQUIRED = {
    "state_version",
    "authority",
    "owner_id",
    "graph_ref",
    "graph_sha256",
    "run_instance_id",
    "status",
    "completed_nodes",
    "loop_counters",
}
RUN_STATE_STATUS = {"running", "complete", "escalated", "blocked"}


class ContractError(ValueError):
    """Raised when one or more contract violations are found."""

    def __init__(self, errors: list[str]):
        self.errors = sorted(set(errors))
        super().__init__("; ".join(self.errors))


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ContractError([f"{path}: document must be a mapping"])
    return data


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def is_repo_relative(value: str) -> bool:
    normalized = value.replace("\\", "/")
    pure = PurePosixPath(normalized)
    return (
        bool(value)
        and not pure.is_absolute()
        and not re.match(r"^[A-Za-z]:", value)
        and ".." not in pure.parts
    )


def interface_compatible(required: str, provided: str) -> bool:
    """Initial compatibility contract: equal major interface version."""
    return required.split(".", 1)[0] == provided.split(".", 1)[0]


def version_tuple(value: str) -> tuple[int, int, int]:
    core = value.split("-", 1)[0].split("+", 1)[0]
    parts = [int(part) for part in core.split(".")]
    return tuple((parts + [0, 0, 0])[:3])


def version_satisfies(constraint: str, provided: str) -> bool:
    candidate = version_tuple(provided)
    operations = {
        ">=": lambda left, right: left >= right,
        "<=": lambda left, right: left <= right,
        ">": lambda left, right: left > right,
        "<": lambda left, right: left < right,
        "==": lambda left, right: left == right,
        "=": lambda left, right: left == right,
        "": lambda left, right: left == right,
    }
    for term in constraint.split(","):
        match = re.fullmatch(
            r"(>=|<=|>|<|==|=)?([0-9]+(?:\.[0-9]+){0,2})", term
        )
        if not match:
            return False
        operator, expected = match.groups()
        if not operations[operator or ""](candidate, version_tuple(expected)):
            return False
    return True


def has_hidden_parent_default(artifact: dict[str, Any]) -> bool:
    home = str(artifact.get("canonical_home", "")).replace("\\", "/").lower()
    kind = artifact.get("artifact_kind")
    if kind == "runbundle":
        return "/run_program_" in f"/{home}" or "/runprogram_" in f"/{home}"
    if kind == "runbook":
        return "/rnb_" in f"/{home}" or "/runbundle" in f"/{home}"
    return False


def has_noncanonical_module_runbook_home(artifact: dict[str, Any]) -> bool:
    """Reject the retired module runbooks path as a parallel discovery home."""
    home = str(artifact.get("canonical_home", "")).replace("\\", "/")
    parts = home.split("/")
    return (
        artifact.get("artifact_kind") == "runbook"
        and len(parts) >= 4
        and parts[0] == "02_Modules"
        and parts[2] == "runbooks"
    )


def affected_consumer_closure(
    graph: dict[str, Any], changed_provider_ids: set[str]
) -> set[str]:
    reverse: dict[str, set[str]] = {}
    for edge in graph["consumes"]:
        reverse.setdefault(edge["provider_id"], set()).add(edge["consumer_id"])
    affected: set[str] = set()
    queue = sorted(changed_provider_ids)
    while queue:
        provider = queue.pop(0)
        for consumer in sorted(reverse.get(provider, set())):
            if consumer not in affected:
                affected.add(consumer)
                queue.append(consumer)
    return affected


def validate_affected_consumer_dispositions(
    graph: dict[str, Any],
    receipt: dict[str, Any],
    changed_provider_ids: set[str],
) -> None:
    if not changed_provider_ids:
        raise ContractError(["at least one --changed-provider is required"])
    expected = affected_consumer_closure(graph, changed_provider_ids)
    actual = {
        row.get("consumer_id")
        for row in receipt.get("affected_consumers", [])
        if row.get("disposition")
        in {"validated", "operator_approved_exception", "not_affected"}
    }
    missing = sorted(expected - actual)
    if missing:
        raise ContractError([
            "missing affected-consumer disposition: " + ", ".join(missing)
        ])


def validate_provider_receipt(receipt: dict[str, Any]) -> None:
    """Reject a malformed or incomplete provider suitability receipt.

    The receipt is optional (see spec_run_family_composition Provider Suitability
    Receipt); enforcement applies only when one is supplied. It is derived
    evidence and never mints identity or redefines an interface.
    """
    errors: list[str] = []
    missing = sorted(PROVIDER_RECEIPT_REQUIRED - receipt.keys())
    if missing:
        errors.append("provider receipt missing fields: " + ", ".join(missing))
    if receipt.get("receipt_version") not in (None, RECEIPT_VERSION):
        errors.append(f"provider receipt_version must be {RECEIPT_VERSION}")
    if "authority" in receipt and receipt["authority"] != DERIVED_NON_AUTHORITATIVE:
        errors.append(
            f"provider receipt authority must be {DERIVED_NON_AUTHORITATIVE}"
        )
    interface = receipt.get("interface_version")
    if interface is not None and not (
        isinstance(interface, str) and INTERFACE_VERSION.fullmatch(interface)
    ):
        errors.append("provider receipt interface_version is invalid")
    exits = receipt.get("exit_artifacts")
    if isinstance(exits, list) and not exits:
        errors.append("provider receipt exit_artifacts is empty")
    capabilities = receipt.get("validated_capabilities")
    if isinstance(capabilities, list):
        if not capabilities:
            errors.append("provider receipt validated_capabilities is empty")
        for index, cap in enumerate(capabilities):
            if (
                not isinstance(cap, dict)
                or not cap.get("capability")
                or not cap.get("evidence_ref")
            ):
                errors.append(
                    f"provider receipt capability[{index}] needs "
                    "capability and evidence_ref"
                )
    elif "validated_capabilities" not in missing:
        errors.append("provider receipt validated_capabilities must be a list")
    substantiated = receipt.get("substantiated_by")
    if isinstance(substantiated, dict):
        if substantiated.get("kind") not in {
            "run_instance_lock",
            "run_receipt",
        } or not substantiated.get("ref"):
            errors.append(
                "provider receipt substantiated_by needs kind "
                "(run_instance_lock|run_receipt) and ref"
            )
    elif "substantiated_by" not in missing:
        errors.append("provider receipt substantiated_by must be an object")
    if errors:
        raise ContractError(errors)


def validate_intake_receipt(receipt: dict[str, Any]) -> None:
    """Reject an intake/admission receipt with missing provenance, incomplete
    dispositions, or unsupported admission evidence.

    Enforces the "nothing disappears silently" rule: every received item must
    carry exactly one disposition plus provenance, and admitted or converted
    items must cite admission evidence.
    """
    errors: list[str] = []
    missing = sorted(INTAKE_RECEIPT_REQUIRED - receipt.keys())
    if missing:
        errors.append("intake receipt missing fields: " + ", ".join(missing))
    if receipt.get("receipt_version") not in (None, RECEIPT_VERSION):
        errors.append(f"intake receipt_version must be {RECEIPT_VERSION}")
    if "authority" in receipt and receipt["authority"] != DERIVED_NON_AUTHORITATIVE:
        errors.append(
            f"intake receipt authority must be {DERIVED_NON_AUTHORITATIVE}"
        )
    snapshot = receipt.get("source_snapshot")
    if isinstance(snapshot, dict):
        package = snapshot.get("package_sha256")
        if not isinstance(package, str) or not SHA256.fullmatch(package):
            errors.append("intake receipt source_snapshot.package_sha256 is invalid")
        if not snapshot.get("inventory_ref"):
            errors.append("intake receipt source_snapshot.inventory_ref is required")
    elif "source_snapshot" not in missing:
        errors.append("intake receipt source_snapshot must be an object")
    items = receipt.get("items")
    if isinstance(items, list):
        if not items:
            errors.append("intake receipt items is empty")
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f"intake item [{index}] must be an object")
                continue
            label = item.get("name") or f"[{index}]"
            disposition = item.get("disposition")
            if disposition not in ADMISSION_DISPOSITIONS:
                errors.append(
                    f"intake item {label} disposition must be one of "
                    + ", ".join(sorted(ADMISSION_DISPOSITIONS))
                )
            provenance = item.get("provenance")
            if not isinstance(provenance, dict):
                errors.append(f"intake item {label} missing provenance")
            else:
                content_hash = provenance.get("content_sha256")
                if not isinstance(content_hash, str) or not SHA256.fullmatch(
                    content_hash
                ):
                    errors.append(
                        f"intake item {label} provenance.content_sha256 is invalid"
                    )
                if not provenance.get("source_path"):
                    errors.append(
                        f"intake item {label} provenance.source_path is required"
                    )
                if not isinstance(provenance.get("size_bytes"), int):
                    errors.append(
                        f"intake item {label} provenance.size_bytes is required"
                    )
            if disposition in ADMISSION_EVIDENCE_REQUIRED and not item.get(
                "evidence_ref"
            ):
                errors.append(
                    f"intake item {label} disposition '{disposition}' "
                    "requires evidence_ref"
                )
    elif "items" not in missing:
        errors.append("intake receipt items must be a list")
    if errors:
        raise ContractError(errors)


def _reject_unsupported(
    obj: Any, allowed: set[str], label: str, errors: list[str]
) -> None:
    """Runtime mirror of a schema's `additionalProperties: false` for a mapping."""
    if isinstance(obj, dict):
        extra = obj.keys() - allowed
        if extra:
            errors.append(
                f"{label} has unsupported fields: " + ", ".join(sorted(extra))
            )


def _has_cycle(adjacency: dict[str, list[str]]) -> bool:
    """Detect a cycle in a directed graph via DFS coloring."""
    white, gray, black = 0, 1, 2
    color: dict[str, int] = {}

    def visit(node: str) -> bool:
        color[node] = gray
        for nxt in adjacency.get(node, []):
            state = color.get(nxt, white)
            if state == gray:
                return True
            if state == white and visit(nxt):
                return True
        color[node] = black
        return False

    return any(
        color.get(node, white) == white and visit(node)
        for node in list(adjacency)
    )


def validate_execution_graph(graph: dict[str, Any]) -> None:
    """Reject a malformed run-family execution control graph.

    See spec_execution_control_graph.md. The graph is an authored control
    surface (routing/gates/loops); it MUST NOT carry identity or composition
    authority, every loop MUST be bounded and escalate upward, and only
    explicitly declared loop edges may form a cycle.
    """
    errors: list[str] = []
    missing = sorted(EXECUTION_GRAPH_REQUIRED - graph.keys())
    if missing:
        errors.append("execution graph missing fields: " + ", ".join(missing))
    if graph.get("graph_version") not in (None, GRAPH_VERSION):
        errors.append(f"execution graph_version must be {GRAPH_VERSION}")
    if "authority" in graph and graph["authority"] != CONTROL_AUTHORITY:
        errors.append(f"execution graph authority must be {CONTROL_AUTHORITY}")
    if "scope" in graph and graph["scope"] not in {"runprogram", "runbundle"}:
        errors.append("execution graph scope must be runprogram or runbundle")
    for field in ("owner_id", "reasoning_owner"):
        if field not in missing and not graph.get(field):
            errors.append(f"execution graph {field} must be a non-empty string")
    leaked_top = FORBIDDEN_GRAPH_FIELDS & graph.keys()
    if leaked_top:
        errors.append(
            "execution graph must not carry composition/identity fields: "
            + ", ".join(sorted(leaked_top))
        )
    unsupported_top = graph.keys() - EXECUTION_GRAPH_ALLOWED
    if unsupported_top:
        errors.append(
            "execution graph has unsupported fields: "
            + ", ".join(sorted(unsupported_top))
        )

    node_ids: set[str] = set()
    nodes = graph.get("nodes")
    if isinstance(nodes, list):
        if not nodes:
            errors.append("execution graph has no nodes")
        for index, node in enumerate(nodes):
            if not isinstance(node, dict):
                errors.append(f"execution node [{index}] must be an object")
                continue
            label = node.get("id") or f"[{index}]"
            node_id = node.get("id")
            if node_id:
                if node_id in node_ids:
                    errors.append(f"execution node id is duplicated: {node_id}")
                node_ids.add(node_id)
            kind = node.get("kind")
            if kind not in NODE_KINDS:
                errors.append(
                    f"execution node {label} kind must be one of "
                    + ", ".join(sorted(NODE_KINDS))
                )
            interface = node.get("interface")
            if (
                not isinstance(interface, dict)
                or interface.get("binding") != "resolved_per_run"
            ):
                errors.append(
                    f"execution node {label} interface.binding must be "
                    "resolved_per_run"
                )
            leaked = FORBIDDEN_GRAPH_FIELDS & node.keys()
            if leaked:
                errors.append(
                    f"execution node {label} must not carry composition/identity "
                    "fields: " + ", ".join(sorted(leaked))
                )
            node_extra = node.keys() - NODE_ALLOWED
            if node_extra:
                errors.append(
                    f"execution node {label} has unsupported fields: "
                    + ", ".join(sorted(node_extra))
                )
            _reject_unsupported(
                node.get("interface"), NODE_INTERFACE_ALLOWED,
                f"execution node {label} interface", errors,
            )
            _reject_unsupported(
                node.get("determinism"), NODE_DETERMINISM_ALLOWED,
                f"execution node {label} determinism", errors,
            )
            _reject_unsupported(
                node.get("onboarding"), NODE_ONBOARDING_ALLOWED,
                f"execution node {label} onboarding", errors,
            )
            _reject_unsupported(
                node.get("handoff"), NODE_HANDOFF_ALLOWED,
                f"execution node {label} handoff", errors,
            )
            if kind == "agentic":
                pack = (node.get("onboarding") or {}).get("required_context_pack")
                if not isinstance(pack, list) or not pack:
                    errors.append(
                        f"execution node {label} (agentic) needs a non-empty "
                        "onboarding.required_context_pack"
                    )
                if not node.get("gate"):
                    errors.append(
                        f"execution node {label} (agentic) must declare a gate"
                    )
                handoff = node.get("handoff") or {}
                if not handoff.get("return_contract"):
                    errors.append(
                        f"execution node {label} (agentic) must declare "
                        "handoff.return_contract (evidence/receipt to return)"
                    )
                if not handoff.get("write_scope"):
                    errors.append(
                        f"execution node {label} (agentic) must declare "
                        "handoff.write_scope (permission envelope)"
                    )
            if kind == "deterministic":
                det = node.get("determinism") or {}
                if det.get("idempotent") is not True or det.get(
                    "content_hashed"
                ) is not True:
                    errors.append(
                        f"execution node {label} (deterministic) must declare "
                        "idempotent and content_hashed true"
                    )
    elif "nodes" not in missing:
        errors.append("execution graph nodes must be a list")

    edges = graph.get("edges")
    plain_adjacency: dict[str, list[str]] = {}
    if isinstance(edges, list):
        for index, edge in enumerate(edges):
            if not isinstance(edge, dict):
                errors.append(f"execution edge [{index}] must be an object")
                continue
            src = edge.get("from")
            dst = edge.get("to")
            for endpoint in (src, dst):
                if endpoint and node_ids and endpoint not in node_ids:
                    errors.append(
                        f"execution edge references unknown node id: {endpoint}"
                    )
            if not edge.get("condition"):
                errors.append(f"execution edge {src}->{dst} needs a condition")
            edge_extra = edge.keys() - GRAPH_EDGE_ALLOWED
            if edge_extra:
                errors.append(
                    f"execution edge {src}->{dst} has unsupported fields: "
                    + ", ".join(sorted(edge_extra))
                )
            checkpoint = edge.get("checkpoint")
            if checkpoint is not None and checkpoint not in CHECKPOINT_POLICIES:
                errors.append(
                    f"execution edge {src}->{dst} checkpoint must be one of "
                    + ", ".join(sorted(CHECKPOINT_POLICIES))
                )
            for field in EDGE_CONTROL_STRINGS:
                value = edge.get(field)
                if value is not None and (
                    not isinstance(value, str) or not value.strip()
                ):
                    errors.append(
                        f"execution edge {src}->{dst} {field} must be a "
                        "non-empty string"
                    )
            if "critical" in edge and not isinstance(edge["critical"], bool):
                errors.append(
                    f"execution edge {src}->{dst} critical must be a boolean"
                )
            if edge.get("critical") is True:
                missing_controls = [
                    control
                    for control in CRITICAL_EDGE_CONTROLS
                    if not edge.get(control)
                ]
                if missing_controls:
                    errors.append(
                        f"execution edge {src}->{dst} is critical (fail-closed) "
                        "and must declare: " + ", ".join(missing_controls)
                    )
            loop = edge.get("loop")
            if loop is None:
                if src and dst:
                    plain_adjacency.setdefault(src, []).append(dst)
            elif not isinstance(loop, dict):
                errors.append(f"execution edge {src}->{dst} loop must be an object")
            else:
                _reject_unsupported(
                    loop, EDGE_LOOP_ALLOWED,
                    f"execution edge {src}->{dst} loop", errors,
                )
                _reject_unsupported(
                    loop.get("on_exceed"), EDGE_LOOP_ON_EXCEED_ALLOWED,
                    f"execution edge {src}->{dst} loop.on_exceed", errors,
                )
                cycles = loop.get("max_cycles")
                if not isinstance(cycles, int) or isinstance(cycles, bool) or cycles < 1:
                    errors.append(f"execution loop {src}->{dst} needs max_cycles >= 1")
                escalate = (loop.get("on_exceed") or {}).get("escalate_to")
                if escalate not in ESCALATE_TARGETS:
                    errors.append(
                        f"execution loop {src}->{dst} on_exceed.escalate_to must be "
                        "reasoning_owner or operator"
                    )
    elif "edges" not in missing:
        errors.append("execution graph edges must be a list")

    if _has_cycle(plain_adjacency):
        errors.append(
            "execution graph has an undeclared cycle (only explicit loop edges "
            "may cycle)"
        )

    routes = graph.get("routes")
    if routes is not None:
        if not isinstance(routes, list):
            errors.append("execution graph routes must be a list")
        else:
            route_ids: set[str] = set()
            for index, route in enumerate(routes):
                if not isinstance(route, dict):
                    errors.append(f"execution route [{index}] must be an object")
                    continue
                rid = route.get("route_id")
                label = rid or f"[{index}]"
                if not rid:
                    errors.append(f"execution route [{index}] needs a route_id")
                elif rid in route_ids:
                    errors.append(f"execution route_id is duplicated: {rid}")
                else:
                    route_ids.add(rid)
                _reject_unsupported(
                    route, ROUTE_ALLOWED, f"execution route {label}", errors
                )
                sequence = route.get("sequence")
                if not isinstance(sequence, list) or not sequence:
                    errors.append(
                        f"execution route {label} needs a non-empty sequence"
                    )
                else:
                    seen_orders: set[int] = set()
                    for step in sequence:
                        if not isinstance(step, dict):
                            errors.append(
                                f"execution route {label} sequence step must be "
                                "an object"
                            )
                            continue
                        _reject_unsupported(
                            step, ROUTE_STEP_ALLOWED,
                            f"execution route {label} step", errors,
                        )
                        ref = step.get("node")
                        if node_ids and ref not in node_ids:
                            errors.append(
                                f"execution route {label} references unknown "
                                f"node: {ref}"
                            )
                        order = step.get("order")
                        if (
                            not isinstance(order, int)
                            or isinstance(order, bool)
                            or order < 1
                        ):
                            errors.append(
                                f"execution route {label} step needs order >= 1"
                            )
                        elif order in seen_orders:
                            errors.append(
                                f"execution route {label} has a duplicate step "
                                f"order: {order}"
                            )
                        else:
                            seen_orders.add(order)
            for route in routes:
                if isinstance(route, dict):
                    dep = route.get("depends_on_route")
                    if dep and dep == route.get("route_id"):
                        errors.append(
                            f"execution route {route.get('route_id')} cannot "
                            "depend on itself"
                        )
                    elif dep and dep not in route_ids:
                        errors.append(
                            "execution route depends_on_route references unknown "
                            f"route: {dep}"
                        )

    if errors:
        raise ContractError(errors)


def validate_execution_graph_run_state(
    state: dict[str, Any], graph: dict[str, Any] | None = None
) -> None:
    """Reject a malformed run-instance execution state for a control graph.

    The run state makes graph execution resumable for a CSCC agent: it freezes
    the graph hash and records progress (current/completed nodes, loop counters,
    handoff receipts). When the graph definition is supplied, the state is
    cross-checked against it (hash match, node membership, loop bounds).
    """
    errors: list[str] = []
    missing = sorted(RUN_STATE_REQUIRED - state.keys())
    if missing:
        errors.append(
            "execution graph run-state missing fields: " + ", ".join(missing)
        )
    if "owner_id" not in missing and not state.get("owner_id"):
        errors.append("execution graph run-state owner_id must be a non-empty string")
    state_extra = state.keys() - RUN_STATE_ALLOWED
    if state_extra:
        errors.append(
            "execution graph run-state has unsupported fields: "
            + ", ".join(sorted(state_extra))
        )
    if state.get("state_version") not in (None, RUN_STATE_VERSION):
        errors.append(f"execution graph run-state state_version must be {RUN_STATE_VERSION}")
    if "authority" in state and state["authority"] != RUN_STATE_AUTHORITY:
        errors.append(
            f"execution graph run-state authority must be {RUN_STATE_AUTHORITY}"
        )
    graph_hash = state.get("graph_sha256")
    if not isinstance(graph_hash, str) or not SHA256.fullmatch(graph_hash):
        errors.append("execution graph run-state graph_sha256 is invalid")
    status = state.get("status")
    if status not in RUN_STATE_STATUS:
        errors.append(
            "execution graph run-state status must be one of "
            + ", ".join(sorted(RUN_STATE_STATUS))
        )
    if status == "running" and not state.get("current_node"):
        errors.append(
            "execution graph run-state with status running needs current_node"
        )
    completed = state.get("completed_nodes")
    if completed is not None and not isinstance(completed, list):
        errors.append("execution graph run-state completed_nodes must be a list")
        completed = None
    loop_counts: dict[str, int] = {}
    counters = state.get("loop_counters")
    if counters is not None:
        if not isinstance(counters, list):
            errors.append("execution graph run-state loop_counters must be a list")
        else:
            for i, counter in enumerate(counters):
                _reject_unsupported(
                    counter, RUN_STATE_LOOP_COUNTER_ALLOWED,
                    f"execution graph run-state loop_counter[{i}]", errors,
                )
                count = counter.get("count") if isinstance(counter, dict) else None
                if (
                    not isinstance(counter, dict)
                    or not counter.get("edge")
                    or not isinstance(count, int)
                    or isinstance(count, bool)
                    or count < 0
                ):
                    errors.append(
                        f"execution graph run-state loop_counter[{i}] needs edge "
                        "and count >= 0"
                    )
                else:
                    loop_counts[counter["edge"]] = count
    receipts = state.get("handoff_receipts")
    if receipts is not None:
        if not isinstance(receipts, list):
            errors.append(
                "execution graph run-state handoff_receipts must be a list"
            )
        elif any(not isinstance(item, str) or not item.strip() for item in receipts):
            errors.append(
                "execution graph run-state handoff_receipts must be non-empty "
                "strings"
            )

    if isinstance(graph, dict):
        if (
            isinstance(graph_hash, str)
            and SHA256.fullmatch(graph_hash)
            and graph_hash != digest(graph)
        ):
            errors.append(
                "execution graph run-state graph_sha256 does not match the "
                "supplied graph"
            )
        if (
            state.get("owner_id")
            and graph.get("owner_id")
            and state["owner_id"] != graph["owner_id"]
        ):
            errors.append(
                f"execution graph run-state owner_id '{state['owner_id']}' does "
                f"not match graph owner_id '{graph['owner_id']}'"
            )
        node_ids = {
            node.get("id")
            for node in graph.get("nodes", [])
            if isinstance(node, dict)
        }
        current = state.get("current_node")
        if current and current not in node_ids:
            errors.append(
                f"execution graph run-state current_node is not a graph node: {current}"
            )
        for done in completed or []:
            if done not in node_ids:
                errors.append(
                    f"execution graph run-state completed node not in graph: {done}"
                )
        loop_bounds: dict[str, Any] = {}
        for edge in graph.get("edges", []):
            if isinstance(edge, dict) and isinstance(edge.get("loop"), dict):
                loop_bounds[f"{edge.get('from')}->{edge.get('to')}"] = edge[
                    "loop"
                ].get("max_cycles")
        for edge_key, count in loop_counts.items():
            if edge_key not in loop_bounds:
                errors.append(
                    "execution graph run-state loop_counter references a non-loop "
                    f"edge: {edge_key}"
                )
            elif isinstance(loop_bounds[edge_key], int) and count > loop_bounds[edge_key]:
                errors.append(
                    f"execution graph run-state loop {edge_key} exceeded max_cycles "
                    f"({count} > {loop_bounds[edge_key]})"
                )

    if errors:
        raise ContractError(errors)


def validate_registry_readme_parity(
    registry: dict[str, Any], readme_text: str
) -> None:
    missing = sorted(
        row["artifact_id"]
        for row in registry.get("artifacts", [])
        if row.get("artifact_kind") == "runbook"
        and row["artifact_id"] not in readme_text
    )
    if missing:
        raise ContractError([
            "README/registry parity missing runbooks: " + ", ".join(missing)
        ])


def graph_from_manifests(paths: list[Path]) -> dict[str, Any]:
    artifacts: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    parameter_profiles: dict[str, Any] = {}
    for path in sorted(paths, key=lambda item: item.as_posix()):
        manifest = load_yaml(path)
        artifact = {
            key: manifest.get(key)
            for key in ARTIFACT_REQUIRED
            if key in manifest
        }
        artifacts.append(artifact)
        consumer_id = manifest.get("artifact_id")
        for edge in manifest.get("consumes", []):
            copied = dict(edge)
            copied["_declared_by"] = consumer_id
            edges.append(copied)
        for name, profile in manifest.get("parameter_profiles", {}).items():
            profile_key = f"{consumer_id}:{name}"
            parameter_profiles[profile_key] = profile
    return {
        "schema_version": "0.1.0",
        "artifacts": artifacts,
        "consumes": edges,
        "parameter_profiles": parameter_profiles,
    }


def discover_manifests(repo_root: Path) -> list[Path]:
    """Discover authoritative run-family manifests at approved canonical homes."""
    patterns = (
        "00_Admin/runbooks/**/manifest.yaml",
        "02_Modules/**/docs/runbooks/**/manifest.yaml",
    )
    found: set[Path] = set()
    for pattern in patterns:
        found.update(path for path in repo_root.glob(pattern) if path.is_file())
    return sorted(found, key=lambda path: path.as_posix())


def validate_graph(
    document: dict[str, Any],
    *,
    repo_root: Path | None = None,
    check_files: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    unsupported_root = sorted(set(document) - ROOT_ALLOWED)
    if unsupported_root:
        errors.append(
            "unsupported top-level fields: " + ", ".join(unsupported_root)
        )
    if "consumed_by" in document:
        errors.append("top-level consumed_by is prohibited manual reverse authority")
    artifacts_raw = document.get("artifacts")
    edges_raw = document.get("consumes")
    if not isinstance(artifacts_raw, list):
        raise ContractError(["artifacts must be an array"])
    if not isinstance(edges_raw, list):
        raise ContractError(["consumes must be an array"])

    by_id: dict[str, dict[str, Any]] = {}
    by_home: dict[str, str] = {}
    by_hash: dict[str, str] = {}
    for index, artifact in enumerate(artifacts_raw):
        label = f"artifacts[{index}]"
        if not isinstance(artifact, dict):
            errors.append(f"{label} must be a mapping")
            continue
        missing = sorted(ARTIFACT_REQUIRED - artifact.keys())
        if missing:
            errors.append(f"{label} missing fields: {', '.join(missing)}")
        unsupported = sorted(set(artifact) - ARTIFACT_ALLOWED)
        if unsupported:
            errors.append(f"{label} unsupported fields: {', '.join(unsupported)}")
        if "consumed_by" in artifact:
            errors.append(f"{label} contains prohibited consumed_by")
        artifact_id = artifact.get("artifact_id")
        kind = artifact.get("artifact_kind")
        home = artifact.get("canonical_home")
        version = artifact.get("artifact_version")
        interface = artifact.get("interface_version")
        content_hash = artifact.get("content_sha256")
        if not isinstance(artifact_id, str) or not artifact_id:
            errors.append(f"{label}.artifact_id must be non-empty")
        elif artifact_id in by_id:
            errors.append(f"duplicate artifact_id: {artifact_id}")
        else:
            by_id[artifact_id] = artifact
        if kind not in KINDS:
            errors.append(f"{label}.artifact_kind is invalid: {kind}")
        if has_hidden_parent_default(artifact):
            errors.append(f"{label} contains hidden parent default: {home}")
        if has_noncanonical_module_runbook_home(artifact):
            errors.append(f"{label} uses retired module runbooks home: {home}")
        if not isinstance(home, str) or not is_repo_relative(home):
            errors.append(f"{label}.canonical_home must be repo-relative")
        elif home in by_home and by_home[home] != artifact_id:
            errors.append(f"duplicate canonical_home: {home}")
        else:
            by_home[home] = str(artifact_id)
        if not isinstance(version, str) or not EXACT_SEMVER.fullmatch(version):
            errors.append(f"{label}.artifact_version must be exact semver")
        if not isinstance(interface, str) or not INTERFACE_VERSION.fullmatch(interface):
            errors.append(f"{label}.interface_version is invalid")
        if not isinstance(content_hash, str) or not SHA256.fullmatch(content_hash):
            errors.append(f"{label}.content_sha256 is invalid")
        elif content_hash in by_hash and by_hash[content_hash] != artifact_id:
            errors.append(
                "copied implementation hash shared by "
                f"{by_hash[content_hash]} and {artifact_id}"
            )
        else:
            by_hash[content_hash] = str(artifact_id)
        if check_files and repo_root is not None and isinstance(home, str):
            target = (repo_root / home).resolve()
            try:
                target.relative_to(repo_root.resolve())
            except ValueError:
                errors.append(f"{label}.canonical_home escapes repo root")
            else:
                if not target.is_file():
                    errors.append(f"canonical_home does not exist: {home}")
                elif isinstance(content_hash, str):
                    actual = hashlib.sha256(target.read_bytes()).hexdigest()
                    if actual != content_hash:
                        errors.append(f"content hash mismatch: {home}")

    adjacency: dict[str, list[str]] = {artifact_id: [] for artifact_id in by_id}
    route_orders: dict[str, set[int]] = {}
    clean_edges: list[dict[str, Any]] = []
    for index, edge in enumerate(edges_raw):
        label = f"consumes[{index}]"
        if not isinstance(edge, dict):
            errors.append(f"{label} must be a mapping")
            continue
        public_edge = {k: v for k, v in edge.items() if not k.startswith("_")}
        missing = sorted(EDGE_REQUIRED - public_edge.keys())
        if missing:
            errors.append(f"{label} missing fields: {', '.join(missing)}")
        unsupported = sorted(set(public_edge) - EDGE_ALLOWED)
        if unsupported:
            errors.append(f"{label} unsupported fields: {', '.join(unsupported)}")
        consumer_id = public_edge.get("consumer_id")
        provider_id = public_edge.get("provider_id")
        declared_by = edge.get("_declared_by")
        if declared_by is not None and declared_by != consumer_id:
            errors.append(
                f"{label} is declared by {declared_by}, not consumer {consumer_id}"
            )
        consumer = by_id.get(consumer_id)
        provider = by_id.get(provider_id)
        if consumer is None:
            errors.append(f"{label} unresolved consumer_id: {consumer_id}")
        if provider is None:
            errors.append(f"{label} unresolved provider_id: {provider_id}")
        if consumer_id == provider_id:
            errors.append(f"{label} self-consumption is prohibited")
        if consumer and provider:
            direction = (
                consumer.get("artifact_kind"),
                provider.get("artifact_kind"),
            )
            if direction not in DIRECTIONS:
                errors.append(
                    f"{label} illegal direction: {direction[0]}->{direction[1]}"
                )
            version = public_edge.get("version_constraint")
            if not isinstance(version, str) or not VERSION_CONSTRAINT.fullmatch(version):
                errors.append(f"{label}.version_constraint is invalid")
            elif not version_satisfies(
                version, str(provider.get("artifact_version", ""))
            ):
                errors.append(
                    f"{label} version constraint not satisfied by provider {provider_id}"
                )
            interface = public_edge.get("interface_constraint")
            if not isinstance(interface, str) or not INTERFACE_VERSION.fullmatch(interface):
                errors.append(f"{label}.interface_constraint is invalid")
            elif not interface_compatible(
                interface, str(provider.get("interface_version", ""))
            ):
                errors.append(
                    f"{label} incompatible interface for provider {provider_id}"
                )
            adjacency.setdefault(str(consumer_id), []).append(str(provider_id))
        route_order = public_edge.get("route_order")
        if not isinstance(route_order, int) or isinstance(route_order, bool) or route_order < 0:
            errors.append(f"{label}.route_order must be a non-negative integer")
        elif isinstance(consumer_id, str):
            used = route_orders.setdefault(consumer_id, set())
            if route_order in used:
                errors.append(
                    f"duplicate route_order {route_order} for {consumer_id}"
                )
            used.add(route_order)
        if not isinstance(public_edge.get("optional"), bool):
            errors.append(f"{label}.optional must be boolean")
        for field in ("gates", "entry_artifacts", "exit_artifacts"):
            values = public_edge.get(field)
            if (
                not isinstance(values, list)
                or any(not isinstance(value, str) or not value for value in values)
                or len(values) != len(set(values))
            ):
                errors.append(f"{label}.{field} must be a unique string array")
        idempotency = public_edge.get("idempotency")
        if not isinstance(idempotency, dict):
            errors.append(f"{label}.idempotency must be a mapping")
        else:
            keys = idempotency.get("key_fields")
            if (
                not isinstance(keys, list)
                or not keys
                or any(not isinstance(value, str) or not value for value in keys)
                or len(keys) != len(set(keys))
            ):
                errors.append(
                    f"{label}.idempotency.key_fields must be a non-empty unique string array"
                )
            if not isinstance(idempotency.get("replay_safe"), bool):
                errors.append(f"{label}.idempotency.replay_safe must be boolean")
        clean_edges.append(public_edge)

    state: dict[str, int] = {}

    def visit(node: str, trail: list[str]) -> None:
        if state.get(node) == 1:
            errors.append(f"consumption cycle: {' -> '.join(trail + [node])}")
            return
        if state.get(node) == 2:
            return
        state[node] = 1
        for provider in sorted(adjacency.get(node, [])):
            visit(provider, trail + [node])
        state[node] = 2

    for artifact_id in sorted(by_id):
        visit(artifact_id, [])
    if errors:
        raise ContractError(errors)
    return {
        "artifacts": sorted(by_id.values(), key=lambda row: row["artifact_id"]),
        "consumes": sorted(
            clean_edges,
            key=lambda row: (
                row["consumer_id"],
                row["route_order"],
                row["provider_id"],
            ),
        ),
        "parameter_profiles": document.get("parameter_profiles", {}),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    # The composition source is optional: receipt and execution-graph
    # validators run standalone. --run-receipt still requires a source.
    source = parser.add_mutually_exclusive_group(required=False)
    source.add_argument("--input", type=Path, help="Aggregate graph YAML")
    source.add_argument(
        "--manifest",
        type=Path,
        action="append",
        help="Consumer manifest; repeat for each manifest",
    )
    source.add_argument(
        "--discover",
        action="store_true",
        help="Discover manifests from approved canonical homes under --repo-root",
    )
    source.add_argument(
        "--check",
        action="store_true",
        help="Run the canonical discovery, file, registry, and README parity checks",
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--check-files", action="store_true")
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--run-receipt", type=Path)
    parser.add_argument("--provider-receipt", type=Path)
    parser.add_argument("--intake-receipt", type=Path)
    parser.add_argument("--execution-graph", type=Path)
    parser.add_argument("--execution-graph-state", type=Path)
    parser.add_argument("--changed-provider", action="append", default=[])
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--runbooks-readme", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    has_source = bool(args.input or args.manifest or args.discover or args.check)
    standalone = bool(
        args.provider_receipt
        or args.intake_receipt
        or args.execution_graph
        or args.execution_graph_state
    )
    try:
        if not has_source and not standalone and not args.run_receipt:
            raise ContractError([
                "supply a composition source (--input/--manifest/--discover/"
                "--check) or a standalone --provider-receipt/--intake-receipt/"
                "--execution-graph/--execution-graph-state argument"
            ])
        normalized = None
        if has_source:
            if args.input:
                document = load_yaml(args.input)
            elif args.discover or args.check:
                document = graph_from_manifests(discover_manifests(args.repo_root))
            else:
                document = graph_from_manifests(args.manifest)
            normalized = validate_graph(
                document,
                repo_root=args.repo_root,
                check_files=args.check_files or args.check,
            )
        if args.check:
            args.registry = args.registry or args.repo_root / "00_Admin/runbooks/run_family_registry.yaml"
            args.runbooks_readme = args.runbooks_readme or args.repo_root / "00_Admin/runbooks/README.md"
        if args.run_receipt:
            if normalized is None:
                raise ContractError([
                    "--run-receipt requires a composition source "
                    "(--input/--manifest/--discover/--check)"
                ])
            validate_affected_consumer_dispositions(
                normalized, load_yaml(args.run_receipt), set(args.changed_provider)
            )
        if args.provider_receipt:
            validate_provider_receipt(load_yaml(args.provider_receipt))
        if args.intake_receipt:
            validate_intake_receipt(load_yaml(args.intake_receipt))
        if args.execution_graph:
            validate_execution_graph(load_yaml(args.execution_graph))
        if args.execution_graph_state:
            paired = load_yaml(args.execution_graph) if args.execution_graph else None
            validate_execution_graph_run_state(
                load_yaml(args.execution_graph_state), paired
            )
        if args.registry or args.runbooks_readme:
            if not (args.registry and args.runbooks_readme):
                raise ContractError([
                    "--registry and --runbooks-readme must be supplied together"
                ])
            validate_registry_readme_parity(
                load_yaml(args.registry),
                args.runbooks_readme.read_text(encoding="utf-8"),
            )
        receipt = {
            "validator": "validate_run_family_graph.py",
            "result": "pass",
        }
        if normalized is not None:
            receipt["source_digest"] = digest(normalized)
            receipt["artifact_count"] = len(normalized["artifacts"])
            receipt["edge_count"] = len(normalized["consumes"])
        if args.receipt:
            args.receipt.parent.mkdir(parents=True, exist_ok=True)
            args.receipt.write_text(
                json.dumps(receipt, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        print(json.dumps(receipt, sort_keys=True))
        return 0
    except (ContractError, OSError, yaml.YAMLError) as exc:
        errors = exc.errors if isinstance(exc, ContractError) else [str(exc)]
        print(
            json.dumps(
                {
                    "validator": "validate_run_family_graph.py",
                    "result": "fail",
                    "errors": sorted(errors),
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
