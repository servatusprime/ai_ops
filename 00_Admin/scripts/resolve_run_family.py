#!/usr/bin/env python3
"""Resolve one run-family route into an exact lock and minimal context pack."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml
from validate_run_family_graph import (
    canonical_bytes,
    digest,
    load_yaml,
    validate_graph,
)


def write_yaml(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(value, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )


def resolve(
    graph: dict[str, Any],
    *,
    root_id: str,
    run_instance_id: str,
    parameters: dict[str, Any] | None = None,
    receipt_references: list[str] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    normalized = validate_graph(graph)
    artifacts = {
        artifact["artifact_id"]: artifact
        for artifact in normalized["artifacts"]
    }
    if root_id not in artifacts:
        raise ValueError(f"unknown root artifact: {root_id}")
    if artifacts[root_id]["artifact_kind"] != "runprogram":
        raise ValueError("root artifact must be a runprogram")
    outgoing: dict[str, list[dict[str, Any]]] = {}
    for edge in normalized["consumes"]:
        outgoing.setdefault(edge["consumer_id"], []).append(edge)
    selected_ids: set[str] = set()
    selected_edges: list[dict[str, Any]] = []
    depth: dict[str, int] = {root_id: 0}
    queue = [root_id]
    while queue:
        consumer = queue.pop(0)
        selected_ids.add(consumer)
        for edge in sorted(
            outgoing.get(consumer, []),
            key=lambda row: (row["route_order"], row["provider_id"]),
        ):
            selected_edges.append(edge)
            provider = edge["provider_id"]
            candidate_depth = depth[consumer] + 1
            depth[provider] = min(depth.get(provider, candidate_depth), candidate_depth)
            if provider not in selected_ids and provider not in queue:
                queue.append(provider)

    resolved_artifacts = [
        {
            "artifact_id": artifact_id,
            "artifact_kind": artifacts[artifact_id]["artifact_kind"],
            "canonical_home": artifacts[artifact_id]["canonical_home"],
            "artifact_version": artifacts[artifact_id]["artifact_version"],
            "interface_version": artifacts[artifact_id]["interface_version"],
            "content_sha256": artifacts[artifact_id]["content_sha256"],
        }
        for artifact_id in sorted(selected_ids)
    ]
    resolved_edges = [
        {
            "consumer_id": edge["consumer_id"],
            "provider_id": edge["provider_id"],
            "artifact_version": artifacts[edge["provider_id"]]["artifact_version"],
            "interface_version": artifacts[edge["provider_id"]]["interface_version"],
            "parameter_profile": edge["parameter_profile"],
            "route_order": edge["route_order"],
            "optional": edge["optional"],
            "gates": list(edge["gates"]),
            "entry_artifacts": list(edge["entry_artifacts"]),
            "exit_artifacts": list(edge["exit_artifacts"]),
            "idempotency": dict(edge["idempotency"]),
        }
        for edge in sorted(
            selected_edges,
            key=lambda row: (
                row["consumer_id"],
                row["route_order"],
                row["provider_id"],
            ),
        )
    ]
    selected_route = [
        artifact_id
        for artifact_id in sorted(
            selected_ids,
            key=lambda item: (
                depth[item],
                artifacts[item]["canonical_home"],
                item,
            ),
        )
    ]
    gates = list(dict.fromkeys(
        gate for edge in resolved_edges for gate in edge["gates"]
    ))
    lock = {
        "lock_version": "0.1.0",
        "authority": "derived_resolution_evidence",
        "run_instance_id": run_instance_id,
        "root_consumer_id": root_id,
        "source_manifest_sha256": digest(normalized),
        "resolved_artifacts": resolved_artifacts,
        "resolved_edges": resolved_edges,
        "parameter_bindings": parameters or {},
        "selected_route": selected_route,
        "gates": gates,
        "receipt_references": receipt_references
        or [f"evidence/{run_instance_id}/run_receipt.yaml"],
    }
    lock["lock_sha256"] = hashlib.sha256(canonical_bytes(lock)).hexdigest()
    reads = [
        {
            "path": artifacts[artifact_id]["canonical_home"],
            "artifact_id": artifact_id,
            "rationale": (
                "root_consumer"
                if depth[artifact_id] == 0
                else "direct_provider"
                if depth[artifact_id] == 1
                else "transitive_provider"
            ),
            "content_sha256": artifacts[artifact_id]["content_sha256"],
        }
        for artifact_id in sorted(
            selected_ids,
            key=lambda item: (
                depth[item],
                artifacts[item]["canonical_home"],
                item,
            ),
        )
    ]
    context_pack = {
        "context_pack_version": "0.1.0",
        "authority": "derived_non_authoritative",
        "root_consumer_id": root_id,
        "resolution_lock_sha256": lock["lock_sha256"],
        "required_reads": reads,
        "selected_artifact_ids": sorted(selected_ids),
        "resolved_interfaces": {
            artifact_id: artifacts[artifact_id]["interface_version"]
            for artifact_id in sorted(selected_ids)
        },
        "required_gates": gates,
        "source_digest": digest(reads),
    }
    return lock, context_pack


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--root-id", required=True)
    parser.add_argument("--run-instance-id", required=True)
    parser.add_argument("--parameters", type=Path)
    parser.add_argument("--output-lock", type=Path, required=True)
    parser.add_argument("--output-context-pack", type=Path, required=True)
    parser.add_argument("--receipt-reference", action="append", default=[])
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    graph = load_yaml(args.input)
    parameters = load_yaml(args.parameters) if args.parameters else {}
    lock, context_pack = resolve(
        graph,
        root_id=args.root_id,
        run_instance_id=args.run_instance_id,
        parameters=parameters,
        receipt_references=args.receipt_reference or None,
    )
    write_yaml(args.output_lock, lock)
    write_yaml(args.output_context_pack, context_pack)
    print(
        json.dumps(
            {
                "result": "pass",
                "lock": str(args.output_lock),
                "context_pack": str(args.output_context_pack),
                "lock_sha256": lock["lock_sha256"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
