#!/usr/bin/env python3
"""Validate .ai_ops/workflows frontmatter contract."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - runtime guard
    raise SystemExit("PyYAML is required. Install with: pip install pyyaml") from exc


REQUIRED_TOP_KEYS = {
    "name",
    "description",
    "kind",
    "version",
    "status",
    "owner",
    "license",
    "claude",
    "codex",
    "exports",
}

ALLOWED_STATUS = {"planned", "stub", "active", "completed", "deprecated"}
EXPECTED_KIND = "workflow"
EXPECTED_OWNER = "ai_ops"
EXPECTED_LICENSE = "Apache-2.0"

REQUIRED_CLAUDE_KEYS = {
    "argument-hint",
    "disable-model-invocation",
    "user-invocable",
    "allowed-tools",
    "model",
    "context",
    "agent",
}

REQUIRED_CODEX_KEYS = {"metadata", "interface", "policy"}
REQUIRED_CODEX_METADATA_KEYS = {"short-description"}
REQUIRED_CODEX_INTERFACE_KEYS = {"display_name", "short_description"}
REQUIRED_CODEX_POLICY_KEYS = {"allow_implicit_invocation"}

REQUIRED_EXPORT_TARGETS = {"claude_plugin", "codex", "claude_project"}
REQUIRED_EXPORT_KEYS = {"enabled", "skill_name"}


def fail(msg: str, errors: List[str]) -> None:
    errors.append(msg)


def parse_frontmatter(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", text, flags=re.DOTALL)
    if not match:
        raise ValueError("missing YAML frontmatter block")
    data = yaml.safe_load(match.group(1)) or {}
    if not isinstance(data, dict):
        raise ValueError("frontmatter must be a YAML mapping")
    return data


def validate_workflow(path: Path, errors: List[str]) -> None:
    try:
        fm = parse_frontmatter(path)
    except Exception as exc:  # pylint: disable=broad-except
        fail(f"{path}: {exc}", errors)
        return

    keys = set(fm.keys())
    missing = REQUIRED_TOP_KEYS - keys
    extra = keys - REQUIRED_TOP_KEYS
    if missing:
        fail(f"{path}: missing top-level keys: {sorted(missing)}", errors)
    if extra:
        fail(f"{path}: unexpected top-level keys: {sorted(extra)}", errors)

    name = fm.get("name")
    if not isinstance(name, str) or not name:
        fail(f"{path}: 'name' must be a non-empty string", errors)
    elif name != path.stem:
        fail(f"{path}: 'name' must match filename stem '{path.stem}'", errors)

    description = fm.get("description")
    if not isinstance(description, str) or not description.strip():
        fail(f"{path}: 'description' must be a non-empty string", errors)

    if fm.get("kind") != EXPECTED_KIND:
        fail(f"{path}: 'kind' must be '{EXPECTED_KIND}'", errors)
    if fm.get("status") not in ALLOWED_STATUS:
        fail(f"{path}: 'status' must be one of {sorted(ALLOWED_STATUS)}", errors)
    if fm.get("owner") != EXPECTED_OWNER:
        fail(f"{path}: 'owner' must be '{EXPECTED_OWNER}'", errors)
    if fm.get("license") != EXPECTED_LICENSE:
        fail(f"{path}: 'license' must be '{EXPECTED_LICENSE}'", errors)

    claude = fm.get("claude")
    if not isinstance(claude, dict):
        fail(f"{path}: 'claude' must be a mapping", errors)
    else:
        ck = set(claude.keys())
        if ck != REQUIRED_CLAUDE_KEYS:
            fail(
                f"{path}: 'claude' keys must be {sorted(REQUIRED_CLAUDE_KEYS)} (got {sorted(ck)})",
                errors,
            )
        if not isinstance(claude.get("disable-model-invocation"), bool):
            fail(f"{path}: claude.disable-model-invocation must be boolean", errors)
        if not isinstance(claude.get("user-invocable"), bool):
            fail(f"{path}: claude.user-invocable must be boolean", errors)

    codex = fm.get("codex")
    if not isinstance(codex, dict):
        fail(f"{path}: 'codex' must be a mapping", errors)
    else:
        ck = set(codex.keys())
        if ck != REQUIRED_CODEX_KEYS:
            fail(
                f"{path}: 'codex' keys must be {sorted(REQUIRED_CODEX_KEYS)} (got {sorted(ck)})",
                errors,
            )
        metadata = codex.get("metadata")
        interface = codex.get("interface")
        policy = codex.get("policy")
        if not isinstance(metadata, dict) or set(metadata.keys()) != REQUIRED_CODEX_METADATA_KEYS:
            fail(f"{path}: codex.metadata keys must be {sorted(REQUIRED_CODEX_METADATA_KEYS)}", errors)
        if not isinstance(interface, dict) or set(interface.keys()) != REQUIRED_CODEX_INTERFACE_KEYS:
            fail(f"{path}: codex.interface keys must be {sorted(REQUIRED_CODEX_INTERFACE_KEYS)}", errors)
        if not isinstance(policy, dict) or set(policy.keys()) != REQUIRED_CODEX_POLICY_KEYS:
            fail(f"{path}: codex.policy keys must be {sorted(REQUIRED_CODEX_POLICY_KEYS)}", errors)
        if isinstance(interface, dict) and interface.get("display_name") != name:
            fail(f"{path}: codex.interface.display_name must match workflow name", errors)
        if isinstance(policy, dict) and not isinstance(policy.get("allow_implicit_invocation"), bool):
            fail(f"{path}: codex.policy.allow_implicit_invocation must be boolean", errors)

    exports = fm.get("exports")
    if not isinstance(exports, dict):
        fail(f"{path}: 'exports' must be a mapping", errors)
    else:
        targets = set(exports.keys())
        if targets != REQUIRED_EXPORT_TARGETS:
            fail(
                f"{path}: export targets must be {sorted(REQUIRED_EXPORT_TARGETS)} (got {sorted(targets)})",
                errors,
            )
        for target in REQUIRED_EXPORT_TARGETS:
            entry = exports.get(target)
            if not isinstance(entry, dict):
                fail(f"{path}: exports.{target} must be a mapping", errors)
                continue
            if set(entry.keys()) != REQUIRED_EXPORT_KEYS:
                fail(f"{path}: exports.{target} keys must be {sorted(REQUIRED_EXPORT_KEYS)}", errors)
            if not isinstance(entry.get("enabled"), bool):
                fail(f"{path}: exports.{target}.enabled must be boolean", errors)
            if entry.get("skill_name") != name:
                fail(f"{path}: exports.{target}.skill_name must match workflow name", errors)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    workflow_dir = repo_root / ".ai_ops" / "workflows"
    workflows = sorted(workflow_dir.glob("*.md"))
    errors: List[str] = []

    if not workflows:
        print(f"[FAIL] no workflow files found under {workflow_dir}")
        return 1

    for path in workflows:
        validate_workflow(path, errors)

    if errors:
        print("[FAIL] workflow frontmatter validation failed:")
        for item in errors:
            print(f"- {item}")
        return 1

    print(f"[OK] workflow frontmatter validation passed ({len(workflows)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
