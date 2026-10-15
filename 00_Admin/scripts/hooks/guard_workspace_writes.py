#!/usr/bin/env python
"""Claude PreToolUse adapter for the shared workspace-containment policy."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]


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


def load_policy(config: Path, root: Path) -> tuple[list[Path], list[Path]]:
    exceptions: list[Path] = []
    signatures: list[Path] = []
    state = ""
    for raw in config.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("harness_exceptions:"):
            state = "exceptions"
        elif line.startswith("escape_root_signatures:"):
            state = "signatures"
        elif line.startswith("path:") and state == "exceptions":
            exceptions.append(expand(line.split(":", 1)[1].strip().strip("\"'"), root))
        elif line.startswith("-") and state == "signatures":
            signatures.append(expand(line[1:].strip().strip("\"'"), root))
    return exceptions, signatures


def target_from_input(payload: dict[str, Any], root: Path) -> Path | None:
    values = payload.get("tool_input") or payload.get("input") or {}
    if not isinstance(values, dict):
        return None
    for key in ("file_path", "path", "target_file", "filePath", "notebook_path"):
        value = values.get(key)
        if isinstance(value, str) and value.strip():
            candidate = Path(os.path.expandvars(value.strip()))
            return (root / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", type=Path, default=ROOT)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--config-sha256")
    args = parser.parse_args()
    root = args.workspace_root.resolve()
    config = (args.config or root / "00_Admin/configs/workspace_containment.yaml").resolve()
    policy_root = (
        config.parents[2]
        if config.parent.name == "configs" and config.parent.parent.name == "00_Admin"
        else root
    )
    if not config.exists():
        return deny(f"containment policy is missing: {config}")
    if args.config_sha256:
        digest = hashlib.sha256(config.read_bytes()).hexdigest()
        if digest.lower() != args.config_sha256.lower():
            return deny("containment policy digest mismatch")
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return deny("hook input is not valid JSON")
    if not isinstance(payload, dict):
        return deny("hook input is not an object")
    target = target_from_input(payload, root)
    if target is None:
        return deny("file-write tool input has no identifiable target path")
    try:
        exceptions, _ = load_policy(config, root)
    except (OSError, UnicodeError) as exc:
        return deny(f"containment policy cannot be parsed: {exc}")
    target_key = os.path.normcase(str(target)).casefold()
    protected = [
        Path(__file__).resolve(),
        config,
        root / ".claude",
        root / ".git" / "hooks",
        root / "ai_ops" / ".claude",
        root / "ai_ops" / ".claude" / "settings.local.json",
        policy_root / ".claude",
        policy_root / ".git" / "hooks",
        policy_root / "00_Admin" / "configs" / "workspace_containment.yaml",
        policy_root / "00_Admin" / "configs" / "closeout_security_tiers.yaml",
        policy_root / "00_Admin" / "scripts" / "hooks" / "guard_workspace_writes.py",
        policy_root / "00_Admin" / "scripts" / "hooks" / "validate_closeout_security_head.py",
        policy_root / "00_Admin" / "scripts" / "validate_closeout_security_receipt.py",
    ]
    if target_key == os.path.normcase(str(Path(__file__).resolve())).casefold():
        return deny("self-protect path cannot be modified")
    def is_protected(path: Path) -> bool:
        key = os.path.normcase(str(path.resolve())).casefold().rstrip("\\/")
        return target_key == key or target_key.startswith(key + os.sep.casefold())

    if any(is_protected(path) for path in protected[1:]):
        return deny("self-protect path cannot be modified")
    root_key = os.path.normcase(str(root)).casefold().rstrip("\\/")
    if target_key == root_key or target_key.startswith(root_key + os.sep.casefold()):
        return 0
    scratchpad = payload.get("scratchpad_dir")
    if isinstance(scratchpad, str) and scratchpad.strip():
        scratchpad_path = Path(os.path.expandvars(scratchpad)).expanduser().resolve()
        scratchpad_key = os.path.normcase(str(scratchpad_path)).casefold().rstrip("\\/")
        if target_key == scratchpad_key or target_key.startswith(scratchpad_key + os.sep.casefold()):
            return 0
    for exception in exceptions:
        key = os.path.normcase(str(exception.resolve())).casefold().rstrip("\\/")
        if target_key == key or target_key.startswith(key + os.sep.casefold()):
            return 0
    return deny(f"target is outside workspace root: {target}")


if __name__ == "__main__":
    raise SystemExit(main())
