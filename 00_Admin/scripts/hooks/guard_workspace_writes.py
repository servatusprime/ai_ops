#!/usr/bin/env python
"""Claude PreToolUse adapter for the shared workspace-containment policy."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
WORKSPACE_ROOT = ROOT.parent

# Agent-control surfaces: protected in the workspace root and in every repo directly under it.
CONTROL_PATHS = (
    ".claude",
    ".git",
    ".pre-commit-config.yaml",
    ".github",
    ".githooks",
    ".vscode",
    ".gitattributes",
    ".gitmodules",
    ".agents",
    ".codex",
    ".mcp.json",
    "AGENTS.md",
    "CLAUDE.md",
    "tmp/pre-commit",
)
# Policy and hook code: protected in the repo that carries the containment policy.
POLICY_PATHS = (
    "00_Admin/configs/workspace_containment.yaml",
    "00_Admin/configs/closeout_security_tiers.yaml",
    "00_Admin/configs/validator/schema_closeout_security_receipt.yaml",
    ".ai_ops/local/closeout_security",
    ".ai_ops/setup",
    "00_Admin/scripts/sync_claude_settings.py",
    "00_Admin/scripts/closeout_security_prepass.py",
    "00_Admin/scripts/validate_closeout_security_receipt.py",
    "00_Admin/scripts/hooks",
    "01_Resources/templates/config",
)


def reject_expansion_syntax(value: str, label: str) -> None:
    """Reject shell-style expansion before path normalization can hide it."""
    if "%" in value or "$" in value:
        raise ValueError(f"{label} contains environment-variable syntax")


def reject_ads_syntax(value: str, label: str) -> None:
    """Reject Windows alternate-data-stream syntax in a target path."""
    normalized = value.replace("/", "\\")
    suffix = normalized[2:] if re.match(r"^[A-Za-z]:", normalized) else normalized
    if ":" in suffix:
        raise ValueError(f"{label} contains alternate-data-stream syntax")


def reject_windows_path_tricks(value: str, label: str) -> None:
    """Reject path spellings that depend on Windows normalization quirks."""
    if re.match(r"^[A-Za-z]:", value) and not re.match(r"^[A-Za-z]:[\\/]", value):
        raise ValueError(f"{label} is drive-relative; use an absolute path")
    components = value.replace("/", "\\").split("\\")
    if any(component == ".." for component in components):
        raise ValueError(f"{label} contains traversal syntax")
    if any(component.startswith("~") for component in components if component):
        raise ValueError(f"{label} contains home-directory expansion syntax")
    if any(component and component not in {"."} and component[-1] in ". " for component in components):
        raise ValueError(f"{label} contains a trailing dot or space")


def deny(cause: str, owner: str = "workspace owner") -> int:
    reason = f"cause={cause}; owner={owner}; next=review the path and apply the declared workspace exception"
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(output))
    return 0


def expand(value: str, root: Path) -> Path:
    workspace = root.parent.resolve() if (root / "00_Admin").exists() else root.resolve()
    drive = workspace.drive.rstrip(":").lower()
    remainder = str(workspace)[2:].replace("\\", "-").replace("/", "-").replace("_", "-")
    project_slug = f"{drive}-{remainder}"
    return Path(
        value.replace("<workspace-root>", str(root))
        .replace("<workspace-project>", project_slug)
        .replace("<user-profile>", os.environ.get("USERPROFILE", str(Path.home())))
        .replace("<os-temp>", os.environ.get("TEMP", str(Path(os.environ.get("TMP", "C:/tmp")))))
    ).expanduser()


def load_exceptions(root: Path, raw: bytes) -> list[Path]:
    """Return the harness exception paths declared in the containment policy."""
    exceptions: list[Path] = []
    in_exceptions = False
    for line in raw.decode("utf-8").splitlines():
        if line and not line[0].isspace() and not line.startswith("#"):
            in_exceptions = line.startswith("harness_exceptions:")
        elif in_exceptions and line.strip().startswith("path:"):
            exceptions.append(expand(line.split(":", 1)[1].strip().strip("\"'"), root))
    return exceptions


def resolve_workspace_root(argument: Path) -> Path:
    """Resolve hook arguments even when the hook runner changes its cwd."""
    if argument.is_absolute():
        return argument.resolve()
    candidate = (Path.cwd() / argument).resolve()
    if (candidate / "00_Admin").exists() or (candidate / "ai_ops" / "00_Admin").exists():
        return candidate
    if argument == Path(".") and (ROOT / "00_Admin").exists():
        return WORKSPACE_ROOT
    return candidate


def resolve_config_path(argument: Path | None, root: Path) -> Path:
    """Resolve a relative policy path against cwd, workspace, and policy roots."""
    if argument is None:
        return root / "00_Admin/configs/workspace_containment.yaml"
    if argument.is_absolute():
        return argument.resolve()
    for candidate in (Path.cwd() / argument, root / argument, WORKSPACE_ROOT / argument, ROOT / argument):
        if candidate.exists():
            return candidate.resolve()
    return (Path.cwd() / argument).resolve()


def target_from_input(payload: dict[str, Any]) -> Path | None:
    values = payload.get("tool_input") or payload.get("input") or {}
    if not isinstance(values, dict):
        return None
    for key in ("file_path", "path", "target_file", "filePath", "notebook_path"):
        value = values.get(key)
        if isinstance(value, str) and value.strip():
            raw = value.strip()
            reject_expansion_syntax(raw, "target path")
            reject_ads_syntax(raw, "target path")
            reject_windows_path_tricks(raw, "target path")
            candidate = Path(raw)
            if candidate.is_absolute():
                return candidate.resolve()
            cwd_value = payload.get("cwd") or payload.get("working_directory") or values.get("cwd")
            if not isinstance(cwd_value, str) or not cwd_value.strip():
                raise ValueError("relative target requires an absolute payload cwd")
            cwd = Path(cwd_value.strip())
            if not cwd.is_absolute():
                raise ValueError("payload cwd must be absolute for a relative target")
            return (cwd / candidate).resolve()
    return None


def protected_paths(root: Path, config: Path, policy_root: Path) -> list[Path]:
    """Every path the file tools may not modify: policy and hook code, then control surfaces."""
    protected = [Path(__file__).resolve(), config]
    protected += [policy_root / relative for relative in POLICY_PATHS]
    for base in {root.resolve(), WORKSPACE_ROOT.resolve(), policy_root.resolve()}:
        protected += [base / relative for relative in CONTROL_PATHS]
        for child in base.iterdir():
            if child.is_dir():
                protected += [child / relative for relative in CONTROL_PATHS]
    return protected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", type=Path, default=ROOT)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--config-sha256", required=True)
    args = parser.parse_args()
    root = resolve_workspace_root(args.workspace_root)
    config = resolve_config_path(args.config, root)
    policy_root = (
        config.parents[2]
        if config.parent.name == "configs" and config.parent.parent.name == "00_Admin"
        else root
    )
    if not config.exists():
        return deny(f"containment policy is missing: {config}")
    try:
        config_bytes = config.read_bytes()
    except OSError as exc:
        return deny(f"containment policy cannot be read: {exc}")
    if hashlib.sha256(config_bytes).hexdigest().lower() != args.config_sha256.lower():
        return deny("containment policy digest mismatch")
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return deny("hook input is not valid JSON")
    if not isinstance(payload, dict):
        return deny("hook input is not an object")
    try:
        target = target_from_input(payload)
    except ValueError as exc:
        return deny(str(exc))
    if target is None:
        return deny("file-write tool input has no identifiable target path")
    try:
        exceptions = load_exceptions(root, config_bytes)
    except (OSError, UnicodeError) as exc:
        return deny(f"containment policy cannot be parsed: {exc}")
    try:
        protected = protected_paths(root, config, policy_root)
    except OSError as exc:
        return deny(f"child repository scan failed: {exc}")

    def contains(parent: Path, key: str) -> bool:
        parent_key = os.path.normcase(str(parent.resolve())).casefold().rstrip("\\/")
        return key == parent_key or key.startswith(parent_key + os.sep.casefold())

    target_key = os.path.normcase(str(target)).casefold()
    if any(contains(path, target_key) for path in protected):
        return deny("self-protect path cannot be modified")
    normalized_target = str(target).replace("/", "\\").casefold()
    if "\\.git\\" in normalized_target or normalized_target.endswith("\\.git"):
        return deny("any repository .git path is self-protected")
    if contains(root, target_key) or any(contains(exception, target_key) for exception in exceptions):
        return 0
    return deny(f"target is outside workspace root: {target}")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - final fail-closed boundary
        raise SystemExit(deny(f"workspace guard failed closed: {type(exc).__name__}: {exc}")) from exc
