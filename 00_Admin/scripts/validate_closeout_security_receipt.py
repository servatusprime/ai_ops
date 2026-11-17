#!/usr/bin/env python
"""Validate a closeout security receipt against repository bytes.

The validator is intentionally stricter than the pre-pass.  In gate mode it
requires complete full-file coverage, checks staged blobs, enforces the T2
floor, and rejects development-only worktree receipts.
"""

from __future__ import annotations

import argparse
import csv
import fnmatch
import hashlib
import io
import json
import math
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, NoReturn

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment diagnostic
    raise SystemExit("PyYAML is required; install it before running the validator") from exc


class _UniqueKeyLoader(yaml.SafeLoader):
    """Reject duplicate YAML keys in security policy documents."""


def _construct_unique_mapping(loader: _UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False) -> dict:
    mapping: dict = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ValueError(f"duplicate YAML key: {key}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def load_policy_yaml(text: str, label: str) -> dict[str, Any]:
    try:
        value = yaml.load(text, Loader=_UniqueKeyLoader) or {}
    except (ValueError, yaml.YAMLError) as exc:
        fail(f"{label} is not valid YAML with unique keys: {exc}")
    if not isinstance(value, dict):
        fail(f"{label} must contain a mapping")
    return value


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from target_paths import resolve_repo_input, resolve_repo_root  # noqa: E402

POLICY_PATH = "00_Admin/configs/closeout_security_tiers.yaml"
HOOK_MARKER = "validate_closeout_security_head.py"
RECEIPT_VERSIONS = {"0.1.0", "0.2.0", "0.4.0"}
DETERMINISTIC_DISPOSITIONS = {
    "deterministic_admission",
    "split_required",
}
# Aggregate review size is intentionally unbounded.  Capacity is controlled by
# per-packet sizing and the workbook's review-loop contract instead of a
# repository-wide token ceiling.
DEFAULT_MAX_TOTAL_REVIEW_TOKENS = None
MIN_FORCED_T2_PREFIXES = (
    ".ai_ops/workflows/",
    "00_Admin/configs/",
    "00_Admin/policies/",
    "00_Admin/specs/",
    "01_Resources/templates/config/",
    ".githooks/",
)
MIN_FORCED_T2_FILES = (
    "AGENTS.md",
    "CLAUDE.md",
    ".pre-commit-config.yaml",
    "SECURITY.md",
    "00_Admin/scripts/closeout_security_prepass.py",
    "00_Admin/scripts/validate_closeout_security_receipt.py",
    "00_Admin/scripts/check_outside_writes.py",
    "00_Admin/scripts/hooks/guard_workspace_writes.py",
    "00_Admin/scripts/hooks/validate_closeout_security_head.py",
    "00_Admin/scripts/target_paths.py",
)


def fail(message: str) -> "NoReturn":
    raise SystemExit(f"closeout-security-validator: {message}")


def target_policy_present(repo: Path) -> bool:
    """Return whether the target repository carries its canonical policy."""
    if (repo / POLICY_PATH).is_file():
        return True
    completed = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "-e", f"HEAD:{POLICY_PATH}"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode == 0:
        return True
    error = completed.stderr.decode("utf-8", errors="replace").strip()
    if completed.returncode == 1 or "does not exist in 'HEAD'" in error:
        return False
    fail("cannot determine target policy presence: " + error)


def closeout_hook_present(repo: Path) -> bool:
    """Return whether an installed hook invokes the HEAD closeout validator."""
    resolved = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--git-path", "hooks"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if resolved.returncode:
        error = resolved.stderr
        if isinstance(error, bytes):
            error = error.decode("utf-8", errors="replace")
        fail("cannot resolve Git hooks path: " + str(error).strip())
    candidate = resolved.stdout.strip()
    if not candidate:
        fail("cannot resolve Git hooks path: Git returned an empty path")
    hook_dir = Path(candidate)
    if not hook_dir.is_absolute():
        hook_dir = (repo / hook_dir).resolve()
    dispatcher_present = False
    for name in (
        "pre-commit",
        "commit-msg",
        "pre-push",
        "pre-commit.dispatcher",
        "commit-msg.dispatcher",
        "pre-push.dispatcher",
    ):
        hook = hook_dir / name
        if not hook.is_file():
            continue
        try:
            text = hook.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            fail(f"cannot read installed hook {hook}: {exc}")
        if HOOK_MARKER in text or ".ai_ops/local/closeout_security/latest.yaml" in text:
            return True
        if (
            name in {
                "pre-commit",
                "commit-msg",
                "pre-push",
                "pre-commit.dispatcher",
                "commit-msg.dispatcher",
                "pre-push.dispatcher",
            }
            and "hook-impl" in text
        ):
            dispatcher_present = True
    if dispatcher_present:
        config = repo / ".pre-commit-config.yaml"
        try:
            text = config.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            fail(f"cannot read dispatcher configuration {config}: {exc}")
        if HOOK_MARKER in text or "ai-ops-closeout-security" in text:
            return True
    return False


def validate_deterministic_applicability(
    repo: Path, config: dict[str, Any], policy_source: str
) -> None:
    """Keep deterministic admission away from a policy-and-hook governed repo."""
    admission = config.get("admission", {}).get("deterministic_admission", {})
    if not admission.get("enabled", False):
        fail("deterministic admission is disabled by the active closeout security policy")
    allowed_sources = set(admission.get("allowed_policy_sources", []))
    if policy_source not in allowed_sources:
        fail(f"policy source is not allowed for deterministic admission: {policy_source}")
    policy_present = target_policy_present(repo)
    if policy_source == "target_HEAD" and not policy_present:
        fail("policy_source=target_HEAD requires a target closeout policy")
    if policy_source == "missing_target_policy" and policy_present:
        fail("policy_source=missing_target_policy is invalid when the target policy exists")
    if policy_present or closeout_hook_present(repo):
        fail("deterministic admission is not applicable when the target policy or closeout hook is present")


def positive_integer(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        fail(f"packet {name} must be a positive integer")
    return value


def enforce_total_review_budget(packet_tokens: list[int], config: dict[str, Any]) -> None:
    configured = config.get("packet", {}).get(
        "max_total_review_tokens", DEFAULT_MAX_TOTAL_REVIEW_TOKENS
    )
    if configured is None:
        return
    maximum = positive_integer(configured, "max_total_review_tokens")
    total = sum(packet_tokens)
    if total > maximum:
        fail(f"review scope exceeds total token budget: estimated={total}; max={maximum}")


def git_bytes(repo: Path, spec: str) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(repo), "show", spec],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode:
        fail(f"cannot read {spec}: {completed.stderr.decode(errors='replace').strip()}")
    return completed.stdout


def git_head(repo: Path) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode:
        fail(completed.stderr.strip())
    return completed.stdout.strip()


def head_path_exists(repo: Path, path: str) -> bool:
    completed = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "-e", f"HEAD:{path}"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.returncode == 0


def safe_path(value: str) -> str:
    path = value.replace("\\", "/").strip()
    while path.startswith("./"):
        path = path[2:]
    candidate = Path(path)
    if not path or path.startswith("/") or re.match(r"^[A-Za-z]:", path) or ".." in candidate.parts:
        fail(f"unsafe receipt path: {value!r}")
    return path


def include_hash(paths: list[str]) -> str:
    return hashlib.sha256("\n".join(sorted(paths)).encode("utf-8")).hexdigest()


def is_binary(path: str, data: bytes, config: dict[str, Any]) -> bool:
    return b"\x00" in data or Path(path).suffix.lower() in {
        str(value).lower() for value in config.get("binary_extensions", [])
    }


def is_generated(path: str, config: dict[str, Any]) -> bool:
    return any(path.startswith(prefix) for prefix in config.get("generated_prefixes", []))


def _blocked_data_key(value: Any, blocked_keys: set[str], max_nodes: int) -> bool | None:
    stack = [value]
    visited = 0
    while stack:
        current = stack.pop()
        visited += 1
        if visited > max_nodes:
            return None
        if isinstance(current, dict):
            for key, child in current.items():
                if str(key).strip().lower() in blocked_keys:
                    return True
                if isinstance(child, (dict, list)):
                    stack.append(child)
        elif isinstance(current, list):
            stack.extend(child for child in current if isinstance(child, (dict, list)))
    return False


def _geojson_bbox_valid(value: Any) -> bool:
    return isinstance(value, list) and len(value) in {4, 6} and all(
        isinstance(item, (int, float)) and not isinstance(item, bool) and math.isfinite(float(item))
        for item in value
    )


def _geojson_position_valid(value: Any) -> bool:
    return isinstance(value, list) and len(value) in {2, 3} and all(
        isinstance(item, (int, float)) and not isinstance(item, bool) and math.isfinite(float(item))
        for item in value
    )


def _geojson_coordinates_valid(value: Any, geometry_type: str) -> bool:
    if geometry_type == "Point":
        return _geojson_position_valid(value)
    if geometry_type == "MultiPoint":
        return isinstance(value, list) and all(_geojson_position_valid(item) for item in value)
    if geometry_type == "LineString":
        return isinstance(value, list) and len(value) >= 2 and all(_geojson_position_valid(item) for item in value)
    if geometry_type == "MultiLineString":
        return isinstance(value, list) and all(_geojson_coordinates_valid(item, "LineString") for item in value)
    if geometry_type == "Polygon":
        return isinstance(value, list) and all(
            isinstance(ring, list)
            and len(ring) >= 4
            and ring[0] == ring[-1]
            and all(_geojson_position_valid(item) for item in ring)
            for ring in value
        )
    if geometry_type == "MultiPolygon":
        return isinstance(value, list) and all(_geojson_coordinates_valid(item, "Polygon") for item in value)
    return False


def _geojson_geometry_valid(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    geometry_type = value.get("type")
    if geometry_type == "GeometryCollection":
        if any(str(key) not in {"type", "geometries", "bbox"} for key in value):
            return False
        if "bbox" in value and not _geojson_bbox_valid(value["bbox"]):
            return False
        geometries = value.get("geometries")
        return isinstance(geometries, list) and all(_geojson_geometry_valid(item) for item in geometries)
    if any(str(key) not in {"type", "coordinates", "bbox"} for key in value):
        return False
    if "bbox" in value and not _geojson_bbox_valid(value["bbox"]):
        return False
    return geometry_type in {
        "Point", "MultiPoint", "LineString", "MultiLineString", "Polygon", "MultiPolygon"
    } and _geojson_coordinates_valid(value.get("coordinates"), geometry_type)


def _geojson_structure(value: Any, blocked_keys: set[str], max_nodes: int) -> tuple[int, list[str]] | None:
    if not isinstance(value, dict) or value.get("type") != "FeatureCollection":
        return None
    if any(str(key) not in {"type", "features", "bbox", "crs", "name"} for key in value):
        return None
    if "bbox" in value and not _geojson_bbox_valid(value["bbox"]):
        return None
    if "name" in value and not isinstance(value["name"], str):
        return None
    if "crs" in value:
        crs = value["crs"]
        if not isinstance(crs, dict) or any(str(key) not in {"type", "properties"} for key in crs):
            return None
        if not isinstance(crs.get("type"), str) or not isinstance(crs.get("properties", {}), dict):
            return None
        if _blocked_data_key(crs.get("properties", {}), blocked_keys, max_nodes) is not False:
            return None
    features = value.get("features")
    if not isinstance(features, list):
        return None
    for feature in features:
        if not isinstance(feature, dict) or any(
            str(key) not in {"type", "geometry", "properties", "id", "bbox"} for key in feature
        ):
            return None
        if "bbox" in feature and not _geojson_bbox_valid(feature["bbox"]):
            return None
        if "id" in feature and (
            not isinstance(feature["id"], (str, int, float)) or isinstance(feature["id"], bool)
        ):
            return None
        if feature.get("type") != "Feature" or not isinstance(feature.get("properties", {}), dict):
            return None
        if feature.get("geometry") is not None and not _geojson_geometry_valid(feature["geometry"]):
            return None
        blocked = _blocked_data_key(feature.get("properties", {}), blocked_keys, max_nodes)
        if blocked is not False:
            return None
    return len(features), sorted(str(key) for key in value)[:100]


def structured_data_summary(path: str, data: bytes, config: dict[str, Any]) -> str | None:
    policy = config.get("large_deleted_data", {})
    if not policy.get("enabled"):
        return None
    if len(data) < int(policy.get("min_source_bytes", 0)):
        return None
    approved_patterns = policy.get("approved_path_patterns", [])
    if not approved_patterns or not any(fnmatch.fnmatch(path, pattern) for pattern in approved_patterns):
        return None
    suffix = Path(path).suffix.lower()
    if suffix not in {str(value).lower() for value in policy.get("approved_extensions", [])}:
        return None
    blocked_keys = {
        str(value).strip().lower() for value in policy.get("blocked_structure_keys", [])
    }
    max_nodes = int(policy.get("max_structure_nodes", 250000))
    try:
        text = data.decode("utf-8")
        if suffix == ".csv":
            reader = csv.reader(io.StringIO(text))
            fields = next(reader, [])
            normalized_fields = [str(field).strip().lower() for field in fields]
            if (
                len(normalized_fields) < 2
                or len(set(normalized_fields)) != len(normalized_fields)
                or any(field in blocked_keys for field in normalized_fields)
            ):
                return None
            records = 0
            for record in reader:
                if len(record) != len(normalized_fields):
                    return None
                records += 1
            structure = {
                "format": "csv_tabular",
                "fields": normalized_fields[:100],
                "field_count": len(normalized_fields),
                "records": records,
            }
        else:
            value = json.loads(text)
            geojson = _geojson_structure(value, blocked_keys, max_nodes)
            if geojson is None:
                return None
            records, top_keys = geojson
            structure = {
                "format": "json",
                "top_level": "geojson_feature_collection",
                "top_keys": top_keys,
                "records": records,
            }
    except (UnicodeDecodeError, json.JSONDecodeError, csv.Error, ValueError):
        return None
    encoded = json.dumps(structure, sort_keys=True, separators=(",", ":"))
    return f"{encoded};summary_sha256={hashlib.sha256(encoded.encode('utf-8')).hexdigest()}"


def expected_file_kind(path: str, data: bytes, config: dict[str, Any], deleted: bool) -> str:
    binary = is_binary(path, data, config)
    if deleted and binary:
        return "deleted_binary"
    if deleted:
        return "deleted"
    if binary:
        return "binary"
    if is_generated(path, config):
        return "generated"
    return "text"


def expected_review_basis(
    path: str, data: bytes, config: dict[str, Any], file_kind: str, deleted: bool
) -> str:
    if file_kind == "deleted" and structured_data_summary(path, data, config) is not None:
        return "structured_deleted_data"
    if file_kind == "deleted_binary":
        return "hash_only_deleted_binary"
    if file_kind == "binary":
        return "digest_bound_binary"
    return "full_content"


def git_delta(
    repo: Path,
    path: str,
    source: str,
    context_lines: int,
    *,
    require_real_text: bool = False,
) -> str:
    """Return the same bounded source delta emitted by the pre-pass."""

    if source == "staged":
        command = [
            "git", "-C", str(repo), "diff", "--cached", "--no-ext-diff", "--no-textconv", "--text",
            f"--unified={context_lines}", "--", path,
        ]
    elif source == "worktree":
        command = [
            "git", "-C", str(repo), "diff", "HEAD", "--no-ext-diff", "--no-textconv", "--text",
            f"--unified={context_lines}", "--", path,
        ]
    else:
        return "(source=head; no new source delta is available)"
    completed = subprocess.run(command, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if completed.returncode:
        error = completed.stderr.decode("utf-8", errors="replace").strip()
        fail(f"cannot read source delta for {path}: {error}")
    try:
        delta = completed.stdout.decode("utf-8")
    except UnicodeDecodeError as exc:
        fail(f"source delta is not valid UTF-8 for {path}: {exc}")
    if not delta:
        if require_real_text:
            fail(f"source delta does not contain the changed text for {path}")
        return "(no source delta; current bytes equal the reviewed baseline)"
    return delta


def delta_packet_content(
    row: dict[str, Any], repo: Path, source: str, context_lines: int
) -> str:
    return (
        "Baseline attestation is reused for unchanged bytes.\n"
        f"baseline_receipt: {row['_baseline_receipt']}\n"
        f"baseline_sha256: {row['_baseline_sha256']}\n"
        f"current_sha256: {row['sha256']}\n"
        f"source_delta_unified_lines: {context_lines}\n\n"
        "source_delta:\n"
        f"{git_delta(repo, row['path'], source, context_lines)}\n"
    )


def validate_baseline_receipt_integrity(
    repo: Path,
    baseline: dict[str, Any],
    current: dict[str, Any],
    config: dict[str, Any] | None = None,
) -> None:
    """Validate the prior receipt's own binding before reusing any attestation."""

    validate_shape(baseline)
    if baseline.get("receipt_version") != "0.2.0":
        fail("delta baseline must be a reviewer-read receipt")
    if baseline.get("repo_root") != current.get("repo_root"):
        fail("delta baseline repo_root does not match current receipt")
    if baseline.get("base_head") != current.get("base_head"):
        fail("delta baseline base_head does not match current receipt")
    if baseline.get("tiers_config_version") != current.get("tiers_config_version"):
        fail("delta baseline policy version does not match current receipt")
    if baseline.get("ruleset_version") != current.get("ruleset_version"):
        fail("delta baseline ruleset version does not match current receipt")
    recorded = baseline.get("receipt_sha256")
    if not isinstance(recorded, str) or not re.fullmatch(r"[0-9a-f]{64}", recorded):
        fail("delta baseline lacks its own receipt_sha256")
    if hashlib.sha256(canonical_receipt(baseline)).hexdigest() != recorded:
        fail("delta baseline receipt_sha256 does not match its content")
    rows = baseline.get("rows", [])
    paths = sorted(str(row["path"]) for row in rows)
    if include_hash(paths) != baseline.get("include_set_sha256"):
        fail("delta baseline include-set hash does not match its rows")
    if not re.fullmatch(r"[0-9a-f]{64}", str(baseline.get("scope_lock_sha256", ""))):
        fail("delta baseline scope lock is invalid")
    baseline_statuses = baseline.get("scope_statuses")
    if not isinstance(baseline_statuses, dict) or set(baseline_statuses) != set(paths):
        fail("delta baseline lacks complete scope status evidence")
    if scope_lock(paths, rows, baseline_statuses) != baseline.get("scope_lock_sha256"):
        fail("delta baseline scope lock does not match its recorded statuses")
    packet_paths = [
        str(value)
        for batch in baseline.get("review_batches", [])
        for value in batch.get("packet_files", [])
    ]
    packet_hashes = [
        str(value)
        for batch in baseline.get("review_batches", [])
        for value in batch.get("packet_sha256", [])
    ]
    if len(packet_paths) != len(packet_hashes):
        fail("delta baseline packet bindings are inconsistent")
    sections: list[dict[str, Any]] = []
    for packet_path, digest in zip(packet_paths, packet_hashes, strict=False):
        target = Path(packet_path)
        if not target.is_absolute():
            target = repo / target
        target = target.resolve()
        try:
            target.relative_to(repo.resolve())
        except ValueError:
            fail(f"delta baseline packet escapes repository: {packet_path}")
        try:
            data = target.read_bytes()
        except OSError as exc:
            fail(f"cannot read delta baseline packet {packet_path}: {exc}")
        if hashlib.sha256(data).hexdigest() != digest:
            fail(f"delta baseline packet digest mismatch: {packet_path}")
        sections.extend(parse_packet_sections(data))
    by_path: dict[str, list[dict[str, Any]]] = {}
    for section in sections:
        by_path.setdefault(section["path"], []).append(section)
    for row in rows:
        path = str(row["path"])
        if config is not None and forced_t2(path, config) and row.get("tier") != "T2":
            fail(f"delta baseline forced-T2 path is under-tiered: {path}")
        if row.get("coverage") != "fully_reviewed" or row.get("disposition") != "pass":
            continue
        if row.get("tier") == "T2":
            if row.get("independent_pass") is not True:
                fail(f"delta baseline lacks independent T2 pass: {path}")
            if str(row.get("independent_reviewer")) in {"", "pending", str(row.get("reviewer"))}:
                fail(f"delta baseline lacks a distinct T2 reviewer: {path}")
            validate_independent_snapshot(
                repo, row, str(row.get("independent_evidence", "")), baseline
            )
        if row.get("review_basis") != "full_content" or row.get("file_kind") in {"binary", "deleted_binary"}:
            continue
        prior_bytes = git_bytes(repo, f"HEAD:{path}")
        ordered = sorted(by_path.get(path, []), key=lambda section: int(section["chunk"]))
        if not ordered or "".join(section.get("content") or "" for section in ordered) != prior_bytes.decode(
            "utf-8", errors="replace"
        ):
            fail(f"delta baseline packet does not bind full HEAD content: {path}")


def validate_delta_baseline(
    repo: Path,
    receipt: dict[str, Any],
    row: dict[str, Any],
    source: str,
    *,
    config: dict[str, Any],
    require_attestation: bool = True,
) -> dict[str, Any]:
    """Require an immutable, fully reviewed prior row before delta reuse."""

    if source not in {"staged", "worktree"}:
        fail(f"delta_with_baseline requires staged or worktree source: {row['path']}")
    if row.get("file_kind") not in {"text", "generated"}:
        fail(f"delta_with_baseline is limited to text/generated rows: {row['path']}")
    baseline_ref = receipt.get("baseline_receipt")
    baseline_hash = receipt.get("baseline_receipt_sha256")
    if not isinstance(baseline_ref, str) or not isinstance(baseline_hash, str):
        fail(f"delta row lacks a bound baseline receipt: {row['path']}")
    baseline_path = (repo / Path(safe_path(baseline_ref))).resolve()
    try:
        baseline_path.relative_to(repo.resolve())
    except ValueError:
        fail(f"baseline receipt escapes repository: {baseline_ref}")
    try:
        baseline_bytes = baseline_path.read_bytes()
    except OSError as exc:
        fail(f"cannot read baseline receipt {baseline_ref}: {exc}")
    if hashlib.sha256(baseline_bytes).hexdigest() != baseline_hash:
        fail(f"baseline receipt digest mismatch: {baseline_ref}")
    try:
        baseline = yaml.safe_load(baseline_bytes.decode("utf-8")) or {}
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        fail(f"cannot parse baseline receipt {baseline_ref}: {exc}")
    if not isinstance(baseline, dict) or baseline.get("receipt_version") != "0.2.0":
        fail(f"baseline receipt must be a reviewer-read v0.2.0 receipt: {baseline_ref}")
    validate_baseline_receipt_integrity(repo, baseline, receipt, config)
    baseline_rows = {
        str(item.get("path")): item
        for item in baseline.get("rows", [])
        if isinstance(item, dict)
    }
    prior = baseline_rows.get(str(row["path"]))
    if not isinstance(prior, dict):
        fail(f"baseline receipt does not cover delta row: {row['path']}")
    if prior.get("mode") != row.get("mode"):
        fail(f"delta row mode differs from its baseline for {row['path']}")
    if prior.get("file_kind") != row.get("file_kind"):
        fail(f"delta row file kind differs from its baseline for {row['path']}")
    if prior.get("prepass_status") != row.get("prepass_status"):
        fail(f"delta row pre-pass status differs from its baseline for {row['path']}")
    if not re.fullmatch(r"[0-9a-f]{64}", str(prior.get("sha256", ""))):
        fail(f"delta baseline has an invalid source digest: {row['path']}")
    if not head_path_exists(repo, str(row["path"])):
        fail(f"delta baseline requires an existing HEAD file: {row['path']}")
    head_digest = hashlib.sha256(git_bytes(repo, f"HEAD:{row['path']}")).hexdigest()
    if head_digest != str(prior["sha256"]):
        fail(f"delta baseline does not bind the target HEAD bytes: {row['path']}")
    if prior.get("review_basis") != "full_content":
        fail(f"delta baseline must originate from full_content review: {row['path']}")
    if prior.get("coverage") != "fully_reviewed" or prior.get("disposition") != "pass":
        fail(f"delta baseline is not a passing full review: {row['path']}")
    if prior.get("review_method") != "full-file-plus-diff" or prior.get("reviewer") in {None, "", "pending"}:
        fail(f"delta baseline lacks a complete reviewer attestation: {row['path']}")
    packet = config.get("packet", {})
    if str(prior.get("sha256")) == str(row.get("sha256")) and int(prior.get("source_bytes", 0)) < int(
        packet.get("delta_reuse_min_bytes", 20000)
    ):
        fail(f"delta baseline is below delta_reuse_min_bytes: {row['path']}")
    if require_attestation:
        if row.get("review_method") != "delta-plus-baseline":
            fail(f"delta row review_method is incomplete: {row['path']}")
        if row.get("coverage") != "fully_reviewed" or row.get("disposition") != "pass":
            fail(f"delta row must retain passing coverage: {row['path']}")
    return prior


def scan_text(path: str, data: bytes, config: dict[str, Any]) -> tuple[str, list[str]]:
    """Recompute the pre-pass classification from trusted bytes and policy."""
    if is_binary(path, data, config):
        return "clean", []
    text = data.decode("utf-8", errors="replace")
    patterns = list(config.get("secret_patterns", [])) + list(
        config.get("instruction_patterns", [])
    )
    patterns += [
        r"\bshell\s*=\s*True\b",
        r"\bos\.system\s*\(",
        r"\b(?:eval|exec)\s*\(",
        r"\bpickle\.loads?\s*\(",
        r"\byaml\.load\s*\(",
    ]
    patterns += list(config.get("additional_tripwires", []))
    hits = [pattern for pattern in patterns if re.search(pattern, text)]
    return ("candidate" if hits else "clean"), hits


def note_value(notes: str, key: str) -> str | None:
    match = re.search(rf"(?:^|[;\s]){re.escape(key)}\s*[:=]\s*([^;\s]+)", notes)
    return match.group(1) if match else None


def evidence_bytes(repo: Path, value: str) -> tuple[str, bytes]:
    path = safe_path(value)
    target = (repo / Path(path)).resolve()
    try:
        target.relative_to(repo.resolve())
    except ValueError:
        fail(f"evidence path escapes repository: {value}")
    if target.exists():
        return path, target.read_bytes()
    if head_path_exists(repo, path):
        return path, git_bytes(repo, f"HEAD:{path}")
    fail(f"evidence path does not exist: {path}")


def validate_evidence_ref(repo: Path, value: str, *, expected_hash: str | None = None) -> None:
    path_value, separator, declared_hash = value.rpartition("@")
    if not separator or not re.fullmatch(r"[0-9a-f]{64}", declared_hash):
        fail(f"evidence reference must be path@sha256: {value}")
    path, data = evidence_bytes(repo, path_value)
    actual_hash = hashlib.sha256(data).hexdigest()
    if actual_hash != declared_hash:
        fail(f"evidence digest mismatch: {path}")
    if expected_hash is not None and actual_hash != expected_hash:
        fail(f"evidence does not preserve the deleted artifact digest: {path}")


def validate_independent_snapshot(
    repo: Path,
    row: dict[str, Any],
    evidence: str,
    receipt: dict[str, Any] | None = None,
) -> None:
    """Validate the structured independent-review artifact bound to a T2 row."""

    snapshot_ref = note_value(evidence, "snapshot")
    evidence_hash = note_value(evidence, "evidence_sha256")
    if snapshot_ref is None or evidence_hash is None:
        fail(f"independent T2 reviewer evidence is incomplete: {row['path']}")
    validate_evidence_ref(repo, f"{snapshot_ref}@{evidence_hash}")
    snapshot_path, snapshot_bytes = evidence_bytes(repo, snapshot_ref)
    try:
        snapshot = yaml.safe_load(snapshot_bytes.decode("utf-8")) or {}
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        fail(f"independent snapshot is not valid YAML: {snapshot_path}: {exc}")
    if not isinstance(snapshot, dict) or snapshot.get("snapshot_version") != "1.0.0":
        fail(f"independent snapshot version is invalid: {snapshot_path}")
    if receipt is not None:
        for key in ("repo_root", "base_head", "scope_lock_sha256"):
            if snapshot.get(key) != receipt.get(key):
                fail(f"independent snapshot {key} mismatch: {snapshot_path}")
    rows = {
        str(item.get("path")): item
        for item in snapshot.get("rows", [])
        if isinstance(item, dict) and item.get("path")
    }
    snapshot_row = rows.get(str(row["path"]))
    if not isinstance(snapshot_row, dict):
        fail(f"independent snapshot does not cover: {row['path']}")
    for key in ("sha256", "mode", "disposition"):
        if snapshot_row.get(key) != row.get(key):
            fail(f"independent snapshot {key} mismatch: {row['path']}")
    if snapshot_row.get("reviewer") != row.get("independent_reviewer"):
        fail(f"independent snapshot reviewer mismatch: {row['path']}")
    if snapshot_row.get("disposition") != "pass":
        fail(f"independent snapshot disposition is not pass: {row['path']}")


def validate_structured_deleted_data_review(repo: Path, row: dict[str, Any]) -> None:
    path = str(row["path"])
    if row.get("file_kind") != "deleted" or row.get("review_basis") != "structured_deleted_data":
        fail(f"structured deleted-data basis is inconsistent: {path}")
    if row.get("prepass_status") != "clean":
        fail(f"structured deleted-data review requires a clean pre-pass: {path}")
    if row.get("review_method") != "structured-deletion-reference-review":
        fail(f"structured deleted-data review method is incomplete: {path}")
    notes = str(row.get("coverage_notes", ""))
    references = note_value(notes, "references")
    recovery = note_value(notes, "recovery")
    structure = note_value(notes, "structure")
    if any(
        value in {None, "pending", "missing", "unknown", "none", "not_required"}
        for value in (references, recovery, structure)
    ):
        fail(f"structured deleted-data evidence is incomplete: {path}")
    if note_value(notes, "references_target_sha256") != str(row["sha256"]):
        fail(f"reference evidence is not bound to the deleted artifact: {path}")
    if note_value(notes, "recovery_target_sha256") != str(row["sha256"]):
        fail(f"recovery evidence is not bound to the deleted artifact: {path}")
    recovery_path, _, _ = str(recovery).rpartition("@")
    if note_value(notes, "recovery_path") != recovery_path:
        fail(f"recovery_path does not identify the recovered artifact: {path}")
    summary = str(row.get("structural_summary", ""))
    expected_summary_hash = hashlib.sha256(summary.encode("utf-8")).hexdigest()
    if note_value(notes, "structure_summary_sha256") != expected_summary_hash:
        fail(f"structural summary evidence is not bound to the receipt: {path}")
    for key in ("producer", "consumers", "retention_owner", "retrieval_method"):
        value = note_value(notes, key)
        if value in {None, "pending", "missing", "unknown", "none", "not_required"}:
            fail(f"structured deleted-data evidence lacks {key}: {path}")
    validate_evidence_ref(repo, str(references))
    validate_evidence_ref(repo, str(structure))
    validate_evidence_ref(repo, str(recovery), expected_hash=str(row["sha256"]))


def validate_review_approval(approval: Any, scope_lock: str) -> None:
    if not isinstance(approval, dict):
        fail("structured deleted-data review requires review_approval")
    if approval.get("scope_lock_sha256") != scope_lock:
        fail("review_approval is not bound to the frozen scope lock")
    if approval.get("decision") != "approve":
        fail("review_approval decision must be approve")
    approved_by = approval.get("approved_by")
    approved_at = approval.get("approved_at")
    placeholders = {"", "pending", "unknown", "none", "missing", "not_required", "n/a"}
    if not isinstance(approved_by, str) or approved_by.strip().casefold() in placeholders:
        fail("review_approval lacks a valid approved_by identity")
    if not isinstance(approved_at, str) or not approved_at.strip():
        fail("review_approval lacks approved_at")
    try:
        timestamp = datetime.fromisoformat(approved_at.replace("Z", "+00:00"))
    except ValueError:
        fail("review_approval approved_at must be an ISO-8601 timestamp")
    if timestamp.tzinfo is None:
        fail("review_approval approved_at must include a timezone")


def scope_lock(paths: list[str], rows: list[dict[str, Any]], statuses: dict[str, str]) -> str:
    row_by_path = {str(row["path"]): row for row in rows}
    material = "\n".join(
        f"{path}\t{statuses.get(path, 'H')}\t{row_by_path[path]['mode']}\t{row_by_path[path]['sha256']}"
        for path in sorted(paths)
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def tree_manifest_hash(paths: list[str], rows: list[dict[str, Any]]) -> str:
    row_by_path = {str(row["path"]): row for row in rows}
    material = "\n".join(
        f"{path}\t{row_by_path[path]['mode']}\t{row_by_path[path]['sha256']}"
        for path in sorted(paths)
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def validate_deterministic_admission(
    receipt: dict[str, Any], rows: list[dict[str, Any]], actual_scope_lock: str,
    actual_tree_manifest: str, *, gate: bool, repo: Path, config: dict[str, Any],
) -> None:
    disposition = str(receipt.get("overall_disposition", ""))
    if disposition not in DETERMINISTIC_DISPOSITIONS:
        fail(f"invalid deterministic overall_disposition: {disposition}")
    if receipt.get("validator_mode") != "deterministic_admission":
        fail("deterministic receipt must declare validator_mode=deterministic_admission")
    policy_source = receipt.get("policy_source")
    if policy_source not in {"target_HEAD", "missing_target_policy"}:
        fail("deterministic receipt has an invalid policy_source")
    validate_deterministic_applicability(repo, config, str(policy_source))
    for key in ("policy_version", "packet_builder_version", "disposition_reason"):
        if not isinstance(receipt.get(key), str) or not receipt[key].strip():
            fail(f"deterministic receipt requires {key}")
    approval_ref = str(receipt.get("operator_commit_approval_ref", "")).strip().casefold()
    if gate and approval_ref in {"", "pending", "pending_commit_approval", "unknown", "missing"}:
        fail("deterministic admission requires an operator commit-approval reference")
    if receipt.get("review_tokens_total") != 0 or receipt.get("review_batches") != []:
        fail("deterministic admission must not contain reviewer packet cost or batches")
    if receipt.get("scope_lock_sha256") != actual_scope_lock:
        fail("scope lock does not match the deterministic admission rows")
    if receipt.get("tree_manifest_sha256") != actual_tree_manifest:
        fail("tree manifest does not match the deterministic admission rows")
    tripwires = receipt.get("known_tripwire_results")
    if not isinstance(tripwires, dict) or tripwires.get("status") not in {"clean", "candidate"}:
        fail("deterministic admission requires known_tripwire_results")
    candidates = [str(row.get("path")) for row in rows if row.get("prepass_status") == "candidate"]
    listed_candidates = tripwires.get("candidate_rows")
    if listed_candidates != candidates:
        fail("known tripwire candidate rows do not match receipt rows")
    if candidates:
        if disposition != "split_required":
            fail("deterministic admission with candidates must be split_required")
        if tripwires.get("status") != "candidate":
            fail("candidate deterministic admission must declare candidate tripwires")
    else:
        if disposition != "deterministic_admission":
            fail("clean deterministic admission must be deterministic_admission")
        if tripwires.get("status") != "clean":
            fail("clean deterministic admission must declare clean tripwire results")
    if gate and disposition == "split_required":
        fail("deterministic admission disposition cannot pass the commit gate: split_required")
    for row in rows:
        if row.get("coverage") != "not_reviewed" or row.get("review_method") != "deterministic-admission":
            fail(f"deterministic row has reviewer coverage: {row.get('path')}")
        if row.get("disposition") != "pending":
            fail(f"deterministic row disposition must be pending: {row.get('path')}")


def staged_records(repo: Path) -> dict[str, str]:
    completed = subprocess.run(
        ["git", "-C", str(repo), "diff", "--cached", "--name-status", "--no-renames", "--diff-filter=ACDMRTUXB"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode:
        fail(f"cannot inspect staged paths: {completed.stderr.strip()}")
    records: dict[str, str] = {}
    for line in completed.stdout.splitlines():
        status, _, path = line.partition("\t")
        if status and path:
            records[safe_path(path)] = status[0]
    return records


def worktree_records(repo: Path, paths: list[str]) -> dict[str, str]:
    requested = set(paths)
    completed = subprocess.run(
        [
            "git", "-C", str(repo), "diff", "HEAD", "--name-status", "--no-renames"
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode:
        fail(f"cannot inspect worktree paths: {completed.stderr.strip()}")
    records: dict[str, str] = {}
    for line in completed.stdout.splitlines():
        status, _, path = line.partition("\t")
        if status and path and path in requested:
            records[safe_path(path)] = status[0]
    untracked = subprocess.run(
        ["git", "-C", str(repo), "ls-files", "--others", "--exclude-standard"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if untracked.returncode:
        fail(f"cannot inspect untracked paths: {untracked.stderr.strip()}")
    for path in untracked.stdout.splitlines():
        if path in requested:
            records[safe_path(path)] = "A"
    return {path: records.get(path, "H") for path in paths}


def validate_shape(receipt: dict[str, Any]) -> None:
    version = str(receipt.get("receipt_version", ""))
    if version not in RECEIPT_VERSIONS:
        fail(f"unsupported receipt_version: {version}")
    required = {
        "receipt_version", "repo_root", "base_head", "source", "include_set_sha256",
        "tiers_config_version", "ruleset_version", "estimated_tokens_total",
        "packet_files", "packet_estimated_tokens", "packet_sha256", "rows",
    }
    if version == "0.2.0":
        required = {
            "receipt_version", "repo_root", "base_head", "source", "include_set_sha256",
            "tiers_config_version", "ruleset_version", "scope_lock_sha256",
            "source_bytes_total", "review_tokens_total", "review_batches", "rows",
        }
    elif version == "0.4.0":
        required = {
            "receipt_version", "repo_root", "base_head", "source", "include_set_sha256",
            "tiers_config_version", "ruleset_version", "scope_lock_sha256",
            "source_bytes_total", "review_tokens_total", "review_batches", "rows",
            "tree_manifest_sha256", "overall_disposition", "disposition_reason",
            "policy_source", "policy_version", "validator_mode",
            "packet_builder_version", "known_tripwire_results",
            "operator_commit_approval_ref",
        }
    missing = sorted(required - set(receipt))
    if missing:
        fail(f"receipt missing fields: {', '.join(missing)}")
    top_allowed = required | {"receipt_sha256"}
    if version == "0.2.0":
        top_allowed |= {
            "review_approval",
            "baseline_receipt",
            "baseline_receipt_sha256",
            "scope_statuses",
        }
    elif version == "0.4.0":
        top_allowed |= set()
    unknown_top = sorted(set(receipt) - top_allowed)
    if unknown_top:
        fail(f"receipt has unknown fields: {', '.join(unknown_top)}")
    if receipt.get("source") not in {"head", "staged", "worktree"}:
        fail("receipt source is invalid")
    if version == "0.1.0":
        if not isinstance(receipt.get("estimated_tokens_total"), int) or receipt["estimated_tokens_total"] < 0:
            fail("estimated_tokens_total must be a non-negative integer")
        if not all(
            isinstance(receipt.get(key), list)
            for key in ("packet_files", "packet_estimated_tokens", "packet_sha256")
        ):
            fail("packet files, token counts, and digests must be lists")
        if len(receipt["packet_files"]) != len(receipt["packet_estimated_tokens"]) or (
            len(receipt["packet_files"]) != len(receipt["packet_sha256"])
        ):
            fail("packet file, token-count, and digest lists must have equal length")
        if not all(isinstance(value, str) and value for value in receipt["packet_files"]):
            fail("packet_files must contain non-empty strings")
        if not receipt["packet_files"] or not all(
            re.fullmatch(r"[0-9a-f]{64}", str(value)) for value in receipt["packet_sha256"]
        ):
            fail("packet_sha256 must contain one lowercase digest per packet")
    elif version in {"0.2.0", "0.4.0"}:
        if not re.fullmatch(r"[0-9a-f]{64}", str(receipt.get("scope_lock_sha256", ""))):
            fail("scope_lock_sha256 must be a lowercase SHA-256")
        if "scope_statuses" in receipt:
            statuses = receipt["scope_statuses"]
            if not isinstance(statuses, dict) or any(
                not isinstance(key, str) or not isinstance(value, str) or not value
                for key, value in statuses.items()
            ):
                fail("scope_statuses must be a non-empty string mapping")
        if version == "0.4.0":
            if not re.fullmatch(r"[0-9a-f]{64}", str(receipt.get("tree_manifest_sha256", ""))):
                fail("tree_manifest_sha256 must be a lowercase SHA-256")
            if receipt.get("overall_disposition") not in DETERMINISTIC_DISPOSITIONS:
                fail("overall_disposition is invalid")
            if receipt.get("policy_source") not in {"target_HEAD", "missing_target_policy"}:
                fail("policy_source is invalid")
            for key in (
                "disposition_reason", "policy_version", "validator_mode",
                "packet_builder_version", "operator_commit_approval_ref",
            ):
                if not isinstance(receipt.get(key), str) or not receipt[key].strip():
                    fail(f"{key} must be a non-empty string")
            if receipt.get("validator_mode") != "deterministic_admission":
                fail("validator_mode must be deterministic_admission")
        for key in ("source_bytes_total", "review_tokens_total"):
            if not isinstance(receipt.get(key), int) or receipt[key] < 0:
                fail(f"{key} must be a non-negative integer")
        batches = receipt.get("review_batches")
        if not isinstance(batches, list) or (version == "0.2.0" and not batches):
            fail("review_batches must be a list and non-empty for reviewer-read receipts")
        if version == "0.4.0" and batches:
            fail("deterministic admission must not contain reviewer batches")
        batch_ids: set[str] = set()
        for batch in batches:
            if not isinstance(batch, dict) or not isinstance(batch.get("id"), str) or not batch["id"]:
                fail("each review batch needs a non-empty id")
            if batch["id"] in batch_ids:
                fail(f"duplicate review batch id: {batch['id']}")
            batch_ids.add(batch["id"])
            for key in ("packet_files", "packet_estimated_tokens", "packet_sha256"):
                if not isinstance(batch.get(key), list):
                    fail(f"review batch {batch['id']} field {key} must be a list")
            if (
                not batch["packet_files"]
                or len(batch["packet_files"]) != len(batch["packet_estimated_tokens"])
                or len(batch["packet_files"]) != len(batch["packet_sha256"])
            ):
                fail(f"review batch {batch['id']} packet lists are inconsistent")
            if not all(isinstance(value, str) and value for value in batch["packet_files"]):
                fail(f"review batch {batch['id']} has an invalid packet path")
            if not all(re.fullmatch(r"[0-9a-f]{64}", str(value)) for value in batch["packet_sha256"]):
                fail(f"review batch {batch['id']} has an invalid packet digest")
    if not isinstance(receipt.get("rows"), list) or not receipt["rows"]:
        fail("receipt rows must be a non-empty list")
    row_allowed = {
        "path", "sha256", "revision_basis", "file_kind", "tier", "coverage",
        "prepass_status", "reviewer", "reviewer_model", "reviewer_runtime",
        "review_method", "independent_pass", "chunk_count", "disposition",
        "finding_refs", "coverage_notes",
    }
    if version in {"0.2.0", "0.4.0"}:
        row_allowed |= {
            "review_basis",
            "mode",
            "source_bytes",
            "independent_reviewer",
            "independent_evidence",
            "structural_summary",
        }
    for row in receipt["rows"]:
        if not isinstance(row, dict):
            fail("receipt row must be a mapping")
        unknown = sorted(set(row) - row_allowed)
        if unknown:
            fail(f"receipt row has unknown fields: {', '.join(unknown)}")
        for key in (
            "path",
            "sha256",
            "revision_basis",
            "reviewer",
            "reviewer_model",
            "reviewer_runtime",
            "review_method",
        ):
            if not isinstance(row.get(key), str) or not row[key]:
                fail(f"receipt row field {key} is required")
        allowed_kinds = {"text", "binary", "generated", "deleted", "unsupported"}
        if version in {"0.2.0", "0.4.0"}:
            allowed_kinds.add("deleted_binary")
        if row.get("file_kind") not in allowed_kinds:
            fail(f"unsupported file_kind in receipt row: {row.get('path')}")
        if row.get("tier") not in {"T0", "T1", "T2"}:
            fail(f"invalid tier in receipt row: {row.get('path')}")
        if row.get("coverage") not in {"fully_reviewed", "partially_reviewed", "unsupported", "not_reviewed"}:
            fail(f"invalid coverage in receipt row: {row.get('path')}")
        if row.get("disposition") not in {"pass", "needs_work", "escalate", "pending"}:
            fail(f"invalid disposition in receipt row: {row.get('path')}")
        if (
            not isinstance(row.get("independent_pass"), bool)
            or not isinstance(row.get("chunk_count"), int)
            or row["chunk_count"] < 1
        ):
            fail(f"review attestation fields are invalid: {row.get('path')}")
        if version in {"0.2.0", "0.4.0"}:
            if row.get("review_basis") not in {
                "full_content",
                "delta_with_baseline",
                "digest_bound_binary",
                "hash_only_deleted_binary",
                "structured_deleted_data",
            }:
                fail(f"invalid review_basis in receipt row: {row.get('path')}")
            if not isinstance(row.get("mode"), str) or not re.fullmatch(r"[0-9]{6}", row["mode"]):
                fail(f"mode is invalid: {row.get('path')}")
            if not isinstance(row.get("source_bytes"), int) or row["source_bytes"] < 0:
                fail(f"source_bytes is invalid: {row.get('path')}")
            for key in ("independent_reviewer", "independent_evidence"):
                if not isinstance(row.get(key), str) or not row[key]:
                    fail(f"receipt row field {key} is required: {row.get('path')}")
            if "structural_summary" in row and not isinstance(row["structural_summary"], str):
                fail(f"structural_summary must be text: {row.get('path')}")


def load_config(repo: Path, config_path: Path | None) -> dict[str, Any]:
    target = config_path or (repo / "00_Admin/configs/closeout_security_tiers.yaml")
    if target.exists():
        return load_policy_yaml(target.read_text(encoding="utf-8"), "closeout security policy")
    raw = git_bytes(repo, "HEAD:00_Admin/configs/closeout_security_tiers.yaml")
    return load_policy_yaml(raw.decode("utf-8"), "HEAD closeout security policy")


def load_staged_config(repo: Path, config_path: Path) -> dict[str, Any]:
    try:
        relative = config_path.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        fail("first-landing policy must be inside the repository")
    if relative != "00_Admin/configs/closeout_security_tiers.yaml":
        fail("first-landing policy must be the canonical closeout security policy")
    raw = git_bytes(repo, f":{relative}")
    return load_policy_yaml(raw.decode("utf-8"), "staged closeout security policy")


def load_head_config(repo: Path) -> dict[str, Any]:
    raw = git_bytes(repo, "HEAD:00_Admin/configs/closeout_security_tiers.yaml")
    return load_policy_yaml(raw.decode("utf-8"), "HEAD closeout security policy")


def forced_t2(path: str, config: dict[str, Any]) -> bool:
    files = set(config.get("forced_t2_files", [])) | set(MIN_FORCED_T2_FILES)
    prefixes = tuple(config.get("forced_t2_prefixes", [])) + MIN_FORCED_T2_PREFIXES
    return path in files or any(path.startswith(prefix) for prefix in prefixes)


def source_bytes(repo: Path, path: str, source: str, file_kind: str) -> tuple[bytes, str]:
    if file_kind in {"deleted", "deleted_binary"}:
        return git_bytes(repo, f"HEAD:{path}"), f"HEAD:{path}"
    if source == "head":
        return git_bytes(repo, f"HEAD:{path}"), f"HEAD:{path}"
    if source == "staged":
        return git_bytes(repo, f":{path}"), f":{path}"
    target = (repo / Path(path)).resolve()
    try:
        target.relative_to(repo.resolve())
    except ValueError:
        fail(f"worktree path escapes repository: {path}")
    return target.read_bytes(), f"worktree:{path}"


def source_mode(repo: Path, path: str, source: str, file_kind: str) -> str:
    if file_kind in {"deleted", "deleted_binary"} or source == "head":
        command = ["git", "-C", str(repo), "ls-tree", "HEAD", "--", path]
    else:
        command = ["git", "-C", str(repo), "ls-files", "--stage", "--", path]
    completed = subprocess.run(command, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if completed.returncode:
        fail(f"cannot inspect mode for {path}: {completed.stderr.strip()}")
    line = completed.stdout.splitlines()[0] if completed.stdout.splitlines() else ""
    if line:
        return line.split(" ", 1)[0]
    if source == "worktree" and (repo / Path(path)).exists():
        return "100644"
    fail(f"cannot determine repository mode for {path}")


def parse_packet_sections(data: bytes) -> list[dict[str, Any]]:
    text = data.decode("utf-8")
    headers = list(re.finditer(r"(?m)^## `([^`]+)`\n", text))
    sections: list[dict[str, Any]] = []
    for index, header in enumerate(headers):
        section = text[header.start() : headers[index + 1].start() if index + 1 < len(headers) else len(text)]
        sha_match = re.search(r"(?m)^- sha256: `([0-9a-f]{64})`$", section)
        chunk_match = re.search(r"(?m)^chunk: (\d+)/(\d+)$", section)
        content_sha_match = re.search(r"(?m)^content_sha256: `([0-9a-f]{64})`$", section)
        bytes_match = re.search(r"(?m)^content_bytes: (\d+)$", section)
        chars_match = re.search(r"(?m)^content_chars: (\d+)$", section)
        if not all((sha_match, chunk_match, content_sha_match, bytes_match, chars_match)):
            fail(f"reviewer packet section is missing binding metadata: {header.group(1)}")
        chars = int(chars_match.group(1))
        marker = "```text\n"
        marker_pos = section.find(marker)
        payload: str | None = None
        if marker_pos >= 0:
            start = marker_pos + len(marker)
            payload = section[start : start + chars]
            if len(payload) != chars or not section[start + chars :].startswith("\n```"):
                fail(f"reviewer packet content length is invalid: {header.group(1)}")
        elif chars:
            fail(f"reviewer packet omits content for {header.group(1)}")
        sections.append(
            {
                "path": safe_path(header.group(1)),
                "sha256": sha_match.group(1),
                "chunk": int(chunk_match.group(1)),
                "chunk_count": int(chunk_match.group(2)),
                "content_sha256": content_sha_match.group(1),
                "content_bytes": int(bytes_match.group(1)),
                "content_chars": chars,
                "content": payload,
            }
        )
    if not sections:
        fail("reviewer packet contains no file sections")
    return sections


def canonical_receipt(receipt: dict[str, Any]) -> bytes:
    copy = dict(receipt)
    copy.pop("receipt_sha256", None)
    return yaml.safe_dump(copy, sort_keys=True).encode("utf-8")


def check_trailer(trailer: str, disposition: str, include_digest: str, receipt_digest: str) -> None:
    match = re.fullmatch(r"Closeout-Security:\s+(\S+)\s+(\S+)\s+(\S+)", trailer.strip())
    if not match:
        fail("trailer format is invalid; expected Closeout-Security: <disposition> <include-set-hash> <receipt-digest>")
    if match.group(1) != disposition or match.group(2) != include_digest or match.group(3) != receipt_digest:
        fail("trailer does not match the validated receipt")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--workspace-root", type=Path, help="workspace containing named governed repositories")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--gate", action="store_true", help="apply real closeout admission rules")
    parser.add_argument("--staged", action="store_true", help="validate against staged blobs")
    parser.add_argument(
        "--first-landing",
        action="store_true",
        help="allow the explicit staged policy for the first landing only",
    )
    parser.add_argument("--trailer")
    parser.add_argument("--commit-msg-file", type=Path)
    parser.add_argument("--discard", action="store_true", help="discard the supplied machine-local receipt")
    args = parser.parse_args()
    workspace_root = args.workspace_root.resolve() if args.workspace_root else None
    try:
        repo = resolve_repo_root(
            args.repo_root, workspace_root=workspace_root, cwd=Path.cwd()
        )
    except ValueError as exc:
        fail(str(exc))
    if args.commit_msg_file:
        try:
            lines = args.commit_msg_file.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            fail(f"cannot read commit message file: {exc}")
        trailers = [line.strip() for line in lines if line.strip().startswith("Closeout-Security:")]
        if len(trailers) != 1:
            fail("commit message must contain exactly one Closeout-Security trailer")
        args.trailer = trailers[0]
    if args.discard:
        receipt_path = resolve_repo_input(
            args.receipt, repo, workspace_root=workspace_root, cwd=Path.cwd()
        )
        if receipt_path == (repo / ".ai_ops/local/closeout_security/latest.yaml"):
            receipt_path.unlink(missing_ok=True)
            print("DISCARDED closeout security receipt")
            return 0
        fail("--discard is limited to .ai_ops/local/closeout_security/latest.yaml")
    receipt_path = resolve_repo_input(
        args.receipt, repo, workspace_root=workspace_root, cwd=Path.cwd()
    )
    try:
        receipt = yaml.safe_load(receipt_path.read_text(encoding="utf-8")) or {}
    except OSError as exc:
        fail(f"cannot read receipt: {exc}")
    if not isinstance(receipt, dict):
        fail("receipt root must be a mapping")
    if receipt.get("receipt_version") not in RECEIPT_VERSIONS:
        fail("unsupported receipt_version")
    validate_shape(receipt)
    if args.gate and not args.staged:
        fail("real gate mode requires --staged so the receipt covers the commit slug")
    if args.gate and str(receipt["receipt_version"]) not in {"0.2.0", "0.4.0"}:
        fail("legacy receipt versions cannot pass the real gate; regenerate a v0.2.0 or v0.4.0 receipt")
    if args.gate and args.config and not args.first_landing:
        if not (
            str(receipt.get("receipt_version")) == "0.4.0"
            and receipt.get("policy_source") == "missing_target_policy"
        ):
            fail(
                "real gate mode binds policy to HEAD; --config requires "
                "--first-landing unless the target policy is missing"
            )
    if args.first_landing and (not args.gate or not args.staged or not args.config):
        fail("--first-landing requires --gate, --staged, and an explicit --config")
    source = "staged" if args.staged else str(receipt["source"])
    if args.gate and source == "worktree":
        fail("development-only source=worktree receipt is rejected in real gate mode")
    if source not in {"head", "staged", "worktree"}:
        fail(f"unsupported receipt source: {source}")
    if str(receipt["repo_root"]) != str(repo):
        fail("receipt repo_root does not match current repository")
    if str(receipt["base_head"]) != git_head(repo):
        fail("receipt base_head does not match current HEAD")
    if not re.fullmatch(r"[0-9a-f]{40}", str(receipt["base_head"])):
        fail("receipt base_head is not a lowercase commit SHA")
    if not re.fullmatch(r"[0-9a-f]{64}", str(receipt["include_set_sha256"])):
        fail("receipt include_set_sha256 is not a lowercase SHA-256")
    resolved_config = (
        resolve_repo_input(args.config, repo, workspace_root=workspace_root, cwd=Path.cwd())
        if args.config
        else None
    )
    if args.first_landing:
        config_path = resolved_config
        if config_path is None:
            fail("--first-landing requires an explicit --config")
        staged = staged_records(repo)
        if staged.get("00_Admin/configs/closeout_security_tiers.yaml") not in {"A", "M"}:
            fail("--first-landing requires the canonical policy to be staged")
        config = load_staged_config(repo, config_path)
        if head_path_exists(repo, "00_Admin/configs/closeout_security_tiers.yaml"):
            head_config = load_head_config(repo)
            if (
                str(head_config.get("version")) == str(config.get("version"))
                and str(head_config.get("ruleset_version")) == str(config.get("ruleset_version"))
            ):
                fail("--first-landing requires a new canonical policy version")
    elif args.gate and resolved_config:
        config = load_config(repo, resolved_config)
    elif args.gate:
        config = load_head_config(repo)
    else:
        config = load_config(repo, resolved_config)
    if str(receipt.get("tiers_config_version")) != str(config.get("version")):
        fail("receipt tiers_config_version does not match the active policy")
    if str(receipt.get("ruleset_version")) != str(config.get("ruleset_version")):
        fail("receipt ruleset_version does not match the active policy")
    packet = config.get("packet", {})
    packet_budget = positive_integer(packet.get("estimated_tokens_per_packet", 20000), "estimated_tokens_per_packet")
    delta_context_limit = positive_integer(packet.get("delta_context_lines", 80), "delta_context_lines")
    delta_max_bytes = positive_integer(packet.get("delta_max_bytes", 100000), "delta_max_bytes")
    configured_session_budget = packet.get("session_token_budget")
    session_budget = (
        positive_integer(configured_session_budget, "session_token_budget")
        if configured_session_budget is not None
        else None
    )
    if str(receipt["receipt_version"]) == "0.2.0":
        packet_groups = [
            (
                str(batch["id"]),
                [str(value) for value in batch["packet_files"]],
                [int(value) for value in batch["packet_estimated_tokens"]],
                [str(value) for value in batch["packet_sha256"]],
            )
            for batch in receipt["review_batches"]
        ]
    elif str(receipt["receipt_version"]) == "0.4.0":
        packet_groups = []
    else:
        packet_groups = [
            (
                "legacy",
                [str(value) for value in receipt["packet_files"]],
                [int(value) for value in receipt["packet_estimated_tokens"]],
                [str(value) for value in receipt["packet_sha256"]],
            )
        ]
    actual_packet_tokens: list[int] = []
    packet_sections: list[dict[str, Any]] = []
    enforce_total_review_budget(
        [token for _, _, tokens, _ in packet_groups for token in tokens], config
    )
    for batch_id, packet_paths, packet_tokens, packet_digests in packet_groups:
        if any(value > packet_budget for value in packet_tokens):
            fail(f"packet token cap exceeded: max={packet_budget}")
        if session_budget is not None and sum(packet_tokens) > session_budget:
            fail(f"review batch token cap exceeded: max={session_budget}; batch={batch_id}")
        batch_actual_tokens: list[int] = []
        for packet_path, recorded_sha in zip(packet_paths, packet_digests, strict=False):
            target = Path(str(packet_path))
            if not target.is_absolute():
                target = repo / target
            target = target.resolve()
            try:
                target.relative_to(repo)
            except ValueError:
                fail(f"packet path escapes repository: {packet_path}")
            try:
                data = target.read_bytes()
            except OSError as exc:
                fail(f"cannot read reviewer packet {packet_path}: {exc}")
            actual_sha = hashlib.sha256(data).hexdigest()
            if actual_sha != str(recorded_sha):
                fail(f"reviewer packet digest mismatch: {packet_path}")
            token_count = (len(data) + 3) // 4
            actual_packet_tokens.append(token_count)
            batch_actual_tokens.append(token_count)
            for section in parse_packet_sections(data):
                section["batch_id"] = batch_id
                packet_sections.append(section)
        if batch_actual_tokens != packet_tokens:
            fail(f"reviewer packet token counts do not match packet bytes: batch={batch_id}")
    if str(receipt["receipt_version"]) == "0.2.0":
        if sum(actual_packet_tokens) != int(receipt["review_tokens_total"]):
            fail("review_tokens_total does not match reviewer packet bytes")
        enforce_total_review_budget(actual_packet_tokens, config)
    rows = receipt["rows"]
    if not isinstance(rows, list) or not rows:
        fail("receipt rows must be a non-empty list")
    receipt_paths = [safe_path(str(row.get("path", ""))) for row in rows if isinstance(row, dict)]
    if args.gate and source == "staged":
        statuses = staged_records(repo)
    elif source == "worktree":
        statuses = worktree_records(repo, sorted(set(receipt_paths)))
    else:
        statuses = {path: "H" for path in receipt_paths}
    if "scope_statuses" in receipt and receipt["scope_statuses"] != statuses:
        fail("receipt scope_statuses do not match the live source status")
    seen: set[str] = set()
    rows_by_path: dict[str, dict[str, Any]] = {}
    dispositions: list[str] = []
    actual_total_tokens = 0
    actual_source_bytes_total = 0
    delta_prior_sha256: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, dict):
            fail("receipt row must be a mapping")
        path = safe_path(str(row.get("path", "")))
        if path in seen:
            fail(f"duplicate receipt row: {path}")
        seen.add(path)
        rows_by_path[path] = row
        change = statuses.get(path, "H")
        deleted = change == "D"
        tier = str(row.get("tier", ""))
        if forced_t2(path, config) and tier != "T2":
            fail(f"forced-T2 path is under-tiered: {path}")
        if not re.fullmatch(r"[0-9a-f]{64}", str(row.get("sha256", ""))):
            fail(f"invalid row sha256 for {path}")
        read_kind = "deleted" if deleted else str(row.get("file_kind", "text"))
        try:
            data, basis = source_bytes(repo, path, source, read_kind)
        except OSError as exc:
            fail(f"cannot read {path}: {exc}")
        actual = hashlib.sha256(data).hexdigest()
        if actual != str(row.get("sha256", "")):
            fail(f"digest mismatch for {path} ({basis})")
        if str(receipt["receipt_version"]) in {"0.2.0", "0.4.0"}:
            actual_kind = expected_file_kind(path, data, config, deleted)
            actual_mode = source_mode(repo, path, source, actual_kind)
            if str(row.get("file_kind")) != actual_kind:
                fail(f"receipt file_kind does not match repository bytes for {path}: {actual_kind}")
            expected_status, expected_findings = scan_text(path, data, config)
            if str(row.get("review_basis")) == "delta_with_baseline":
                baseline_row = validate_delta_baseline(
                    repo, receipt, row, source, config=config, require_attestation=args.gate
                )
                delta_prior_sha256[path] = str(baseline_row["sha256"])
                expected_basis = "delta_with_baseline"
            else:
                expected_basis = (
                    expected_review_basis(path, data, config, actual_kind, deleted)
                    if expected_status == "clean"
                    else "full_content"
                )
            if str(row.get("review_basis")) != expected_basis:
                fail(f"receipt review_basis does not match file_kind for {path}")
            expected_summary = structured_data_summary(path, data, config)
            if (
                expected_basis == "structured_deleted_data"
                and str(row.get("structural_summary", "")) != expected_summary
            ):
                fail(f"structural summary does not match repository bytes for {path}")
            if actual_mode != str(row["mode"]):
                fail(f"mode mismatch for {path}: {actual_mode}")
            if str(row.get("prepass_status")) != expected_status:
                fail(f"pre-pass status does not match repository bytes for {path}: {expected_status}")
            if list(row.get("finding_refs", [])) != expected_findings:
                fail(f"pre-pass findings do not match repository bytes for {path}")
        actual_total_tokens += (len(data) + 3) // 4
        actual_source_bytes_total += len(data)
        if str(receipt["receipt_version"]) in {"0.2.0", "0.4.0"} and int(row["source_bytes"]) != len(data):
            fail(f"source_bytes does not match repository bytes for {path}")
        coverage = str(row.get("coverage", ""))
        disposition = str(row.get("disposition", ""))
        dispositions.append(disposition)
        if args.gate and str(receipt["receipt_version"]) != "0.4.0":
            if coverage != "fully_reviewed":
                fail(f"incomplete full-file coverage for {path}: {coverage}")
            if disposition != "pass":
                fail(f"non-pass disposition for {path}: {disposition}")
            if str(row.get("file_kind")) == "unsupported":
                fail(f"unsupported file kind cannot pass the gate: {path}")
            if str(row.get("reviewer")) == "pending":
                fail(f"review attestation is incomplete for {path}")
            file_kind = str(row.get("file_kind"))
            review_basis = str(row.get("review_basis", "full_content"))
            if file_kind == "deleted_binary":
                if (
                    review_basis != "hash_only_deleted_binary"
                    or str(row.get("review_method")) != "hash-only-deletion-reference-review"
                ):
                    fail(f"deleted binary review basis is incomplete for {path}")
                notes = str(row.get("coverage_notes", ""))
                references = note_value(notes, "references")
                recovery = note_value(notes, "recovery")
                references_target = note_value(notes, "references_target_sha256")
                recovery_target = note_value(notes, "recovery_target_sha256")
                if (
                    references in {None, "pending", "missing", "unknown", "none"}
                    or recovery in {None, "pending", "missing", "unknown", "not_required"}
                    or references_target != str(row["sha256"])
                    or recovery_target != str(row["sha256"])
                ):
                    fail(f"deleted binary lacks references= and recovery= evidence: {path}")
                validate_evidence_ref(repo, references)
                validate_evidence_ref(repo, recovery)
            elif review_basis == "structured_deleted_data":
                validate_structured_deleted_data_review(repo, row)
            elif review_basis == "delta_with_baseline":
                validate_delta_baseline(repo, receipt, row, source, config=config)
            elif str(row.get("review_method")) != "full-file-plus-diff":
                fail(f"review attestation is incomplete for {path}")
            if tier == "T2" and row.get("independent_pass") is not True:
                fail(f"independent T2 pass is missing for {path}")
            if tier == "T2":
                independent_reviewer = str(row.get("independent_reviewer"))
                independent_evidence = str(row.get("independent_evidence", ""))
                snapshot = note_value(independent_evidence, "snapshot")
                evidence_hash = note_value(independent_evidence, "evidence_sha256")
                if (
                    independent_reviewer in {"pending", str(row.get("reviewer"))}
                    or snapshot in {None, "pending", "missing", "unknown"}
                    or evidence_hash is None
                    or not re.fullmatch(r"[0-9a-f]{64}", evidence_hash)
                ):
                    fail(f"independent T2 reviewer evidence is missing for {path}")
                validate_independent_snapshot(repo, row, independent_evidence, receipt)
            if (
                file_kind in {"binary", "generated"}
                and not any(
                    marker in str(row.get("coverage_notes", ""))
                    for marker in ("generator:", "parser:", "render:")
                )
            ):
                fail(f"binary/generated row lacks generator, parser, or render evidence: {path}")
            if row.get("prepass_status") == "candidate" and (
                not row.get("finding_refs")
                or note_value(str(row.get("coverage_notes", "")), "candidate_resolution")
                not in {"resolved", "accepted", "closed"}
            ):
                fail(f"candidate pre-pass row lacks finding references or resolution: {path}")
    packet_by_path: dict[str, list[dict[str, Any]]] = {}
    if str(receipt["receipt_version"]) == "0.4.0" and packet_sections:
        fail("deterministic admission must not contain reviewer packet sections")
    for section in packet_sections:
        path = section["path"]
        if path not in rows_by_path:
            fail(f"reviewer packet contains an unlisted path: {path}")
        row = rows_by_path[path]
        if section["sha256"] != row["sha256"]:
            fail(f"reviewer packet file digest does not match receipt row: {path}")
        if section["content_bytes"] < 0:
            fail(f"reviewer packet content byte count is invalid: {path}")
        if section["content"] is not None:
            payload_bytes = section["content"].encode("utf-8")
            if hashlib.sha256(payload_bytes).hexdigest() != section["content_sha256"]:
                fail(f"reviewer packet content digest mismatch: {path}")
            if len(payload_bytes) != section["content_bytes"]:
                fail(f"reviewer packet content byte count mismatch: {path}")
        elif section["content_sha256"] != row["sha256"]:
            fail(f"omitted reviewer packet content is not bound to the file digest: {path}")
        packet_by_path.setdefault(path, []).append(section)
    if str(receipt["receipt_version"]) != "0.4.0" and set(packet_by_path) != seen:
        missing = sorted(seen - set(packet_by_path))
        extra = sorted(set(packet_by_path) - seen)
        fail(f"reviewer packets do not cover receipt rows; missing={missing}; extra={extra}")
    for path, row in rows_by_path.items() if str(receipt["receipt_version"]) != "0.4.0" else []:
        sections = packet_by_path[path]
        expected_count = int(row["chunk_count"])
        if len(sections) != expected_count:
            fail(f"reviewer packet chunk count does not match receipt row: {path}")
        if {int(section["chunk"]) for section in sections} != set(range(1, expected_count + 1)):
            fail(f"reviewer packet chunk numbering is incomplete: {path}")
        if any(int(section["chunk_count"]) != expected_count for section in sections):
            fail(f"reviewer packet declares inconsistent chunk counts: {path}")
        omitted_content = row.get("review_basis") == "structured_deleted_data"
        if row["file_kind"] not in {"binary", "deleted_binary"} and not omitted_content:
            ordered = sorted(sections, key=lambda section: int(section["chunk"]))
            if any(section["content"] is None for section in ordered):
                fail(f"reviewer packet omits text content: {path}")
            if row.get("review_basis") == "delta_with_baseline":
                context_lines = note_value(str(row.get("coverage_notes", "")), "delta_context_lines")
                if context_lines is None or not context_lines.isdigit():
                    fail(f"delta row lacks a valid delta_context_lines note: {path}")
                if int(context_lines) != delta_context_limit:
                    fail(
                        f"delta row context lines do not match policy for {path}: "
                        f"{context_lines} != {delta_context_limit}"
                    )
                baseline_ref = str(receipt.get("baseline_receipt", ""))
                baseline_hash = str(receipt.get("baseline_receipt_sha256", ""))
                require_real_text = delta_prior_sha256.get(path) != str(row["sha256"])
                source_delta = git_delta(
                    repo,
                    path,
                    source,
                    int(context_lines),
                    require_real_text=require_real_text,
                )
                if len(source_delta.encode("utf-8")) > delta_max_bytes:
                    fail(f"delta exceeds delta_max_bytes for {path}")
                expected_text = (
                    "Baseline attestation is reused for unchanged bytes.\n"
                    f"baseline_receipt: {baseline_ref}\n"
                    f"baseline_sha256: {baseline_hash}\n"
                    f"current_sha256: {row['sha256']}\n"
                    f"source_delta_unified_lines: {int(context_lines)}\n\n"
                    "source_delta:\n"
                    f"{source_delta}\n"
                )
            else:
                expected_data, _ = source_bytes(repo, path, source, str(row["file_kind"]))
                expected_text = expected_data.decode("utf-8", errors="replace")
            if "".join(section["content"] for section in ordered) != expected_text:
                fail(f"reviewer packet content does not match reviewed bytes: {path}")
    actual_include = include_hash(sorted(seen))
    if actual_include != str(receipt["include_set_sha256"]):
        fail("include-set hash does not match receipt rows")
    if str(receipt["receipt_version"]) in {"0.2.0", "0.4.0"}:
        if actual_source_bytes_total != int(receipt["source_bytes_total"]):
            fail(f"source_bytes_total does not match repository bytes: {actual_source_bytes_total}")
    elif actual_total_tokens != int(receipt["estimated_tokens_total"]):
        fail(f"estimated token total does not match reviewed bytes: {actual_total_tokens}")
    if args.gate and source == "staged":
        if set(statuses) != seen:
            missing = sorted(set(statuses) - seen)
            extra = sorted(seen - set(statuses))
            fail(f"receipt does not exactly cover staged paths; missing={missing}; extra={extra}")
        for row in rows:
            change = statuses[str(row["path"])]
            if row["file_kind"] in {"deleted", "deleted_binary"} and change != "D":
                fail(f"row marks a non-deletion as deleted: {row['path']}")
            if row["file_kind"] not in {"deleted", "deleted_binary"} and change == "D":
                fail(f"staged deletion is not classified as deleted: {row['path']}")
    if str(receipt["receipt_version"]) in {"0.2.0", "0.4.0"}:
        actual_scope_lock = scope_lock(sorted(seen), rows, statuses)
        if actual_scope_lock != str(receipt["scope_lock_sha256"]):
            fail("scope lock does not match the frozen paths, statuses, and digests")
        if str(receipt["receipt_version"]) == "0.4.0":
            validate_deterministic_admission(
                receipt,
                rows,
                str(receipt["scope_lock_sha256"]),
                tree_manifest_hash(sorted(seen), rows),
                gate=args.gate,
                repo=repo,
                config=config,
            )
        if (
            args.gate
            and str(receipt["receipt_version"]) == "0.2.0"
            and any(row.get("review_basis") == "structured_deleted_data" for row in rows)
        ):
            validate_review_approval(receipt.get("review_approval"), str(receipt["scope_lock_sha256"]))
    receipt_digest = hashlib.sha256(canonical_receipt(receipt)).hexdigest()
    recorded_digest = receipt.get("receipt_sha256")
    if recorded_digest and recorded_digest != receipt_digest:
        fail("receipt_sha256 does not match receipt content")
    if args.trailer:
        if str(receipt["receipt_version"]) == "0.4.0":
            disposition = str(receipt["overall_disposition"])
        else:
            disposition = "pass" if args.gate else ("needs_work" if "needs_work" in dispositions else "pending")
        check_trailer(args.trailer, disposition, actual_include, receipt_digest)
    print(f"PASS {len(rows)} rows source={source} gate={str(args.gate).lower()}")
    print(f"include_set_sha256={actual_include}")
    print(f"receipt_sha256={receipt_digest}")
    return 0


if __name__ == "__main__":
    main()
