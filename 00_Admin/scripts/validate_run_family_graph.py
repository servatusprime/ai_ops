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
    source = parser.add_mutually_exclusive_group(required=True)
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
    parser.add_argument("--changed-provider", action="append", default=[])
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--runbooks-readme", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
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
            validate_affected_consumer_dispositions(
                normalized, load_yaml(args.run_receipt), set(args.changed_provider)
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
            "source_digest": digest(normalized),
            "artifact_count": len(normalized["artifacts"]),
            "edge_count": len(normalized["consumes"]),
        }
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
