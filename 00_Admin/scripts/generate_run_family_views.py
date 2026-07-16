#!/usr/bin/env python3
"""Generate or drift-check canonical non-authoritative run-family views."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import yaml
from validate_run_family_graph import (
    digest,
    graph_from_manifests,
    load_yaml,
    validate_graph,
)

DEFAULT_TARGETS = {
    "registry": Path("00_Admin/runbooks/run_family_registry.yaml"),
    "run_family_graph": Path("00_Admin/reports/generated/graphs/run_family_graph.yaml"),
    "artifact_dependency_graph": Path("00_Admin/reports/generated/graphs/artifact_dependency_graph.yaml"),
    "governance_routing_graph": Path("00_Admin/reports/generated/graphs/governance_routing_graph.yaml"),
}


def render_yaml(value: dict[str, Any]) -> str:
    return yaml.safe_dump(value, sort_keys=False, allow_unicode=False)


def discover_manifests(repo_root: Path) -> list[Path]:
    patterns = (
        "00_Admin/runbooks/**/manifest.yaml",
        "02_Modules/**/docs/runbooks/**/manifest.yaml",
    )
    found: set[Path] = set()
    for pattern in patterns:
        found.update(path for path in repo_root.glob(pattern) if path.is_file())
    return sorted(found, key=lambda path: path.as_posix())


def load_source(repo_root: Path, input_override: Path | None) -> dict[str, Any]:
    if input_override is not None:
        return load_yaml(input_override)
    manifests = discover_manifests(repo_root)
    if not manifests:
        return {
            "schema_version": "0.1.0",
            "artifacts": [],
            "consumes": [],
            "parameter_profiles": {},
        }
    return graph_from_manifests(manifests)


def _repo_relative(path: str) -> str:
    normalized = path.replace("\\", "/")
    return normalized.removeprefix("ai_ops/")


def build_governance_routing_view(repo_root: Path) -> dict[str, Any]:
    """Project shallow workflow/spec/validator routing from canonical inputs."""
    context_path = repo_root / "00_Admin/configs/context_routing.yaml"
    validator_path = repo_root / "00_Admin/configs/validator/validator_config.yaml"
    commands = (load_yaml(context_path).get("commands", {}) if context_path.is_file() else {})
    validator_config = load_yaml(validator_path) if validator_path.is_file() else {}
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, str]] = []
    workflow_hashes: dict[str, str] = {}

    for command_name in ("work", "crosscheck", "closeout"):
        profile = commands.get(command_name, {})
        workflow_rel = f".ai_ops/workflows/{command_name}.md"
        workflow_path = repo_root / workflow_rel
        if not isinstance(profile, dict) or not workflow_path.is_file():
            continue
        workflow_text = workflow_path.read_text(encoding="utf-8")
        if "Run-Family Graph Hook" not in workflow_text:
            continue
        command_id = f"command:{command_name}"
        workflow_id = f"workflow:{workflow_rel}"
        nodes[command_id] = {"id": command_id, "kind": "command"}
        nodes[workflow_id] = {
            "id": workflow_id,
            "kind": "workflow_source",
            "path": workflow_rel,
        }
        workflow_hashes[workflow_rel] = hashlib.sha256(
            workflow_text.encode("utf-8")
        ).hexdigest()
        edges.append({
            "source": command_id,
            "target": workflow_id,
            "kind": "implemented_by",
            "provenance": "canonical_workflow_source",
        })
        route_targets = profile.get("read_on_demand", [])
        if not route_targets and isinstance(profile.get("default"), dict):
            route_targets = profile["default"].get("read_on_demand", [])
        for raw_target in route_targets:
            target = _repo_relative(str(raw_target))
            if target not in {
                "00_Admin/specs/spec_artifact_graph_identity.md",
                "00_Admin/specs/spec_run_family_composition.md",
                "00_Admin/runbooks/run_family_registry.yaml",
            }:
                continue
            target_id = f"artifact:{target}"
            nodes[target_id] = {
                "id": target_id,
                "kind": "run_family_authority_or_index",
                "path": target,
            }
            edges.append({
                "source": command_id,
                "target": target_id,
                "kind": "reads_on_demand",
                "provenance": "context_routing",
            })
            edges.append({
                "source": workflow_id,
                "target": target_id,
                "kind": "run_family_hook_reference",
                "provenance": "workflow_hook_plus_context_routing",
            })

    rules = validator_config.get("rules", [])
    vs036 = next(
        (rule for rule in rules if isinstance(rule, dict) and rule.get("id") == "VS036"),
        None,
    )
    if isinstance(vs036, dict) and vs036.get("enabled"):
        validator_id = "validator:VS036"
        nodes[validator_id] = {"id": validator_id, "kind": "validator_rule"}
        params = vs036.get("params", {})
        for key, edge_kind in (
            ("validator_script", "invokes"),
            ("generator_script", "invokes"),
            ("registry", "validates"),
            ("runbooks_readme", "validates"),
        ):
            target = _repo_relative(str(params.get(key, "")))
            if not target:
                continue
            target_id = f"artifact:{target}"
            nodes[target_id] = {
                "id": target_id,
                "kind": "validator_dependency",
                "path": target,
            }
            edges.append({
                "source": validator_id,
                "target": target_id,
                "kind": edge_kind,
                "provenance": "validator_config.VS036",
            })

    source_digest = digest({
        "routing_commands": {
            name: commands.get(name, {})
            for name in ("work", "crosscheck", "closeout")
        },
        "validator_rule": vs036 or {},
        "workflow_hashes": workflow_hashes,
    })
    return {
        "graph_version": "0.1.0",
        "authority": "derived_non_authoritative",
        "generated_by": "00_Admin/scripts/generate_run_family_views.py",
        "source_digest": source_digest,
        "graph_kind": "governance_routing_graph",
        "scope": "run_family_workflow_spec_validator_projection",
        "nodes": [nodes[key] for key in sorted(nodes)],
        "edges": sorted(
            edges,
            key=lambda edge: (
                edge["source"], edge["target"], edge["kind"], edge["provenance"]
            ),
        ),
    }


def build_views(
    graph: dict[str, Any], repo_root: Path | None = None
) -> dict[str, dict[str, Any]]:
    normalized = validate_graph(graph)
    artifacts, edges = normalized["artifacts"], normalized["consumes"]
    consumes = {row["artifact_id"]: [] for row in artifacts}
    consumed_by = {row["artifact_id"]: [] for row in artifacts}
    for edge in edges:
        consumes[edge["consumer_id"]].append(edge["provider_id"])
        consumed_by[edge["provider_id"]].append(edge["consumer_id"])
    source_digest = digest(normalized)
    registry = {
        "registry_version": "0.1.0",
        "authority": "derived_non_authoritative",
        "authoritative_source": "colocated_run_family_manifest",
        "generated_by": "00_Admin/scripts/generate_run_family_views.py",
        "source_digest": source_digest,
        "artifacts": [
            {
                **artifact,
                "consumes": sorted(set(consumes[artifact["artifact_id"]])),
                "consumed_by": sorted(set(consumed_by[artifact["artifact_id"]])),
            }
            for artifact in artifacts
        ],
    }
    nodes = [
        {
            "id": row["artifact_id"],
            "kind": row["artifact_kind"],
            "canonical_home": row["canonical_home"],
            "artifact_version": row["artifact_version"],
            "interface_version": row["interface_version"],
        }
        for row in artifacts
    ]
    graph_edges = [
        {
            "source": edge["consumer_id"],
            "target": edge["provider_id"],
            "kind": "consumes",
            "provenance": "explicit",
            "authority": "canonical_consumer_manifest",
            "route_order": edge["route_order"],
            "optional": edge["optional"],
            "gates": list(edge["gates"]),
        }
        for edge in edges
    ]
    common = {
        "graph_version": "0.1.0",
        "authority": "derived_non_authoritative",
        "generated_by": "00_Admin/scripts/generate_run_family_views.py",
        "source_digest": source_digest,
    }
    return {
        "registry": registry,
        "run_family_graph": {
            **common, "graph_kind": "run_family_graph",
            "nodes": nodes, "edges": graph_edges,
        },
        "artifact_dependency_graph": {
            **common, "graph_kind": "artifact_dependency_graph",
            "nodes": nodes, "edges": graph_edges,
        },
        "governance_routing_graph": (
            build_governance_routing_view(repo_root)
            if repo_root is not None
            else {
                **common,
                "graph_kind": "governance_routing_graph",
                "scope": "run_family_workflow_spec_validator_projection",
                "nodes": [],
                "edges": [],
            }
        ),
    }


def target_paths(repo_root: Path) -> dict[str, Path]:
    return {name: repo_root / path for name, path in DEFAULT_TARGETS.items()}


def write_views(views: dict[str, dict[str, Any]], targets: dict[str, Path]) -> None:
    for name, path in targets.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        # newline="\n" keeps generated views byte-identical across platforms and
        # yamllint-clean; the default would emit CRLF on Windows.
        path.write_text(render_yaml(views[name]), encoding="utf-8", newline="\n")


def check_views(
    views: dict[str, dict[str, Any]], targets: dict[str, Path]
) -> list[str]:
    drift: list[str] = []
    for name, path in sorted(targets.items()):
        expected = render_yaml(views[name])
        if not path.is_file():
            drift.append(f"missing:{path}")
        elif path.read_text(encoding="utf-8") != expected:
            drift.append(f"drift:{path}")
    return drift


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--input", type=Path, help="Approved aggregate override")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = args.repo_root.resolve()
    views = build_views(load_source(repo_root, args.input), repo_root=repo_root)
    targets = target_paths(repo_root)
    if args.write:
        write_views(views, targets)
        drift, code = [], 0
    else:
        drift = check_views(views, targets)
        code = 1 if drift else 0
    result = {
        "result": "fail" if code else "pass",
        "mode": "write" if args.write else "check",
        "drift": drift,
        "source_digest": views["registry"]["source_digest"],
        "outputs": {name: str(path) for name, path in sorted(targets.items())},
    }
    print(json.dumps(result, sort_keys=True), file=sys.stderr if code else sys.stdout)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
