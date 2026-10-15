#!/usr/bin/env python3
"""
Validation operation for customization config inputs.

Usage:
    python op_validate_config.py <config_file>

Returns:
    0 if valid, 1 if invalid with error messages
"""

import ntpath
import os
import re
import shutil
import sys
from pathlib import Path

import yaml

ALLOWED_VALIDATION_EXECUTABLES = {"python", "python3", "py"}
ALLOWED_VALIDATION_EXECUTABLE_TOKENS = ALLOWED_VALIDATION_EXECUTABLES | {
    f"{name}.exe" for name in ALLOWED_VALIDATION_EXECUTABLES
}
PATH_VALUE_FLAGS = {
    "--config",
    "--file",
    "--install-root",
    "--manifest",
    "--output",
    "--path",
    "--repo-root",
    "--target",
    "--workspace-root",
}
SHELL_META_RE = re.compile(r"[&|;<>()`$]")
REPARSE_POINT = 0x400


def _resolved_path(raw: str, root: Path) -> Path:
    candidate = _lexical_path(raw, root)
    return candidate.resolve(strict=False)


def _lexical_path(raw: str, root: Path) -> Path:
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = root / candidate
    return candidate


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root.resolve(strict=True))
    except (ValueError, FileNotFoundError):
        return False
    return True


def _is_reparse(path: Path) -> bool:
    try:
        info = path.lstat()
    except OSError:
        return False
    return path.is_symlink() or bool(getattr(info, "st_file_attributes", 0) & REPARSE_POINT)


def _has_reparse_component(path: Path, root: Path) -> bool:
    trusted = Path(os.path.abspath(os.fspath(root)))
    lexical = Path(os.path.abspath(os.fspath(path)))
    try:
        relative = lexical.relative_to(trusted)
    except ValueError:
        return True
    current = trusted
    for part in relative.parts:
        current = current / part
        if os.path.lexists(os.fspath(current)) and _is_reparse(current):
            return True
    return False


def validate_command_argv(
    command: object,
    *,
    label: str,
    repo_root: Path,
    workspace_root: Path,
) -> list[str]:
    """Validate one configured validator command without executing it."""
    errors: list[str] = []
    if isinstance(command, str):
        return [f"{label} must be an argv list, not a shell command string"]
    if not isinstance(command, list) or not command:
        return [f"{label} must be a non-empty argv list"]
    if any(not isinstance(token, str) or not token.strip() for token in command):
        errors.append(f"{label} must contain only non-empty strings")
        return errors
    if any(SHELL_META_RE.search(token) for token in command):
        errors.append(f"{label} contains shell metacharacters")

    executable = command[0].lower()
    if executable not in ALLOWED_VALIDATION_EXECUTABLE_TOKENS:
        errors.append(
            f"{label} executable must be one of {sorted(ALLOWED_VALIDATION_EXECUTABLES)}"
        )
    else:
        resolved_executable = shutil.which(command[0])
        trusted_runtime = Path(sys.executable).resolve(strict=True)
        if not resolved_executable:
            errors.append(f"{label} executable is not resolvable in the current runtime")
        elif Path(resolved_executable).resolve(strict=True) != trusted_runtime:
            errors.append(
                f"{label} executable must resolve to the validator runtime: {trusted_runtime}"
            )
    if len(command) < 2 or command[1].startswith("-"):
        errors.append(f"{label} must name a Python script as argv[1]")
    else:
        lexical_script_path = _lexical_path(command[1], repo_root)
        script_path = _resolved_path(command[1], repo_root)
        trusted_script_roots = [
            repo_root,
            workspace_root / "ai_ops" / "00_Admin" / "scripts",
        ]
        if not any(_is_within(script_path, trusted_root) for trusted_root in trusted_script_roots):
            errors.append(f"{label} script escapes the workspace: {command[1]}")
        elif any(
            _has_reparse_component(lexical_script_path, trusted_root)
            for trusted_root in trusted_script_roots
            if _is_within(script_path, trusted_root)
        ):
            errors.append(f"{label} script crosses a symlink/reparse point: {command[1]}")

    path_value_indexes: set[int] = set()
    for index, token in enumerate(command[2:], start=2):
        path_flag = next(
            (flag for flag in PATH_VALUE_FLAGS if token == flag or token.startswith(f"{flag}=")),
            None,
        )
        if path_flag is not None:
            if token == path_flag:
                if index + 1 >= len(command):
                    errors.append(f"{label} path flag requires a value: {token}")
                    continue
                value = command[index + 1]
                path_value_indexes.add(index + 1)
            else:
                value = token.split("=", 1)[1]
                if not value:
                    errors.append(f"{label} path flag requires a value: {token}")
                    continue
            lexical_value_path = _lexical_path(value, repo_root)
            value_path = _resolved_path(value, repo_root)
            if not any(
                _is_within(value_path, trusted_root)
                for trusted_root in (repo_root, workspace_root)
            ):
                errors.append(f"{label} path argument escapes the workspace: {value}")
            elif any(
                _has_reparse_component(lexical_value_path, trusted_root)
                for trusted_root in (repo_root, workspace_root)
                if _is_within(value_path, trusted_root)
            ):
                errors.append(f"{label} path argument crosses a symlink/reparse point: {value}")
            continue
        if index in path_value_indexes:
            continue
        if token.startswith("-"):
            # Unknown inline options may carry an unvalidated path or other
            # value. Reject them instead of treating every option as a
            # harmless boolean; recognized path flags were handled above.
            if "=" in token:
                errors.append(f"{label} contains an unrecognized inline option value: {token}")
            continue
        if (
            Path(token).is_absolute()
            or bool(ntpath.splitdrive(token)[0])
            or token in {".", ".."}
            or "/" in token
            or "\\" in token
            or token.startswith("..")
        ):
            errors.append(f"{label} has an unflagged path-like argument: {token}")
    return errors


def validate_config(config_path):
    """
    Validate customization config against expected schema.

    Args:
        config_path: Path to config file (.yaml or .yml)

    Returns:
        tuple: (is_valid, errors_list)
    """
    errors = []

    config_file = Path(config_path)
    # Check file exists
    if not config_file.exists():
        return False, [f"Config file not found: {config_path}"]

    # Load YAML
    try:
        with config_file.open(encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return False, [f"Invalid YAML: {e}"]
    except Exception as e:
        return False, [f"Error reading file: {e}"]

    if not isinstance(config, dict):
        return False, ["config root must be a mapping"]

    workspace_root = Path(__file__).resolve().parents[3]

    # Validate version if present
    if 'version' in config:
        if not isinstance(config['version'], (str, float)):
            errors.append("version must be a string or number")

    # Validate customizations section (aligns with aiops_config.template.yaml)
    if 'customizations' in config:
        custom = config['customizations']
        if not isinstance(custom, dict):
            errors.append("customizations must be a mapping")
            custom = {}

        # Validate clarification_limits if present
        if 'clarification_limits' in custom:
            cl = custom['clarification_limits']
            if 'max_followups' in cl and not isinstance(cl['max_followups'], int):
                errors.append("customizations.clarification_limits.max_followups must be an integer")

        # Validate session_limits if present
        if 'session_limits' in custom:
            sl = custom['session_limits']
            is_num = isinstance(sl.get('max_size_kb'), (int, float))
            if 'max_size_kb' in sl and sl['max_size_kb'] is not None and not is_num:
                errors.append("customizations.session_limits.max_size_kb must be a number or null")

        # Validate bootstrap_preferences if present
        if 'bootstrap_preferences' in custom:
            bp = custom['bootstrap_preferences']
            if 'max_read_depth' in bp and not isinstance(bp['max_read_depth'], int):
                errors.append("customizations.bootstrap_preferences.max_read_depth must be an integer")

    workspace = config.get("workspace", {})
    if workspace is not None and not isinstance(workspace, dict):
        errors.append("workspace must be a mapping")
        workspace = {}
    if workspace is None:
        workspace = {}
    for repo_index, entry in enumerate(workspace.get("work_repos", [])):
        label_prefix = f"workspace.work_repos[{repo_index}]"
        if not isinstance(entry, dict):
            errors.append(f"{label_prefix} must be a mapping")
            continue
        repo_path = entry.get("path")
        if not isinstance(repo_path, str) or not repo_path.strip():
            errors.append(f"{label_prefix}.path must be a non-empty string")
            repo_root = workspace_root
        else:
            lexical_repo_root = _lexical_path(repo_path, workspace_root)
            repo_root = _resolved_path(repo_path, workspace_root)
            if not _is_within(repo_root, workspace_root):
                errors.append(f"{label_prefix}.path escapes the workspace: {repo_path}")
            elif _has_reparse_component(lexical_repo_root, workspace_root):
                errors.append(
                    f"{label_prefix}.path crosses a symlink/reparse point: {repo_path}"
                )
        savepoint = entry.get("savepoint_validation", {})
        if savepoint is None:
            savepoint = {}
        if not isinstance(savepoint, dict):
            errors.append(f"{label_prefix}.savepoint_validation must be a mapping")
            continue
        commands = savepoint.get("minimum_commands", [])
        if not isinstance(commands, list):
            errors.append(f"{label_prefix}.savepoint_validation.minimum_commands must be a list")
            commands = []
        for command_index, command in enumerate(commands):
            errors.extend(
                validate_command_argv(
                    command,
                    label=f"{label_prefix}.savepoint_validation.minimum_commands[{command_index}]",
                    repo_root=repo_root,
                    workspace_root=workspace_root,
                )
            )

    return len(errors) == 0, errors


def main():
    if len(sys.argv) != 2:
        print("Usage: op_validate_config.py <config_file>")
        sys.exit(1)

    config_path = sys.argv[1]
    is_valid, errors = validate_config(config_path)

    if is_valid:
        print(f"[OK] Config valid: {config_path}")
        sys.exit(0)
    else:
        print(f"[FAIL] Config invalid: {config_path}")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)


if __name__ == '__main__':
    main()
