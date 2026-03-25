#!/usr/bin/env python
"""
Minimal repo validator for machine-checkable rules defined in validator_config.yaml.
No external dependencies required.
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import shutil
import subprocess
import sys
from typing import Any, Dict, List, Tuple

ALLOWED_STATUS = {"planned", "stub", "active", "completed", "deprecated"}


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def detect_git_root(start_dir: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", start_dir, "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        root = result.stdout.strip()
        if root:
            return os.path.normpath(root)
    except Exception:
        pass
    return os.path.normpath(start_dir)


def resolve_repo_root(repo_root_arg: str | None, default_root: str) -> str:
    if not repo_root_arg:
        return os.path.normpath(default_root)
    candidate = repo_root_arg
    if not os.path.isabs(candidate):
        candidate = os.path.join(default_root, candidate)
    return os.path.normpath(candidate)


def split_front_matter(text: str) -> Tuple[Dict[str, str], str]:
    if not text.startswith("---"):
        return {}, ""
    end_idx = text.find("\n---", 3)
    if end_idx == -1:
        return {}, ""
    fm = text[3:end_idx].strip().splitlines()
    data: Dict[str, str] = {}
    key_re = re.compile(r"^\s*([A-Za-z0-9_]+)\s*:\s*(.*)$")
    for line in fm:
        match = key_re.match(line)
        if not match:
            continue
        key, value = match.group(1), match.group(2).strip().strip('"').strip("'")
        data[key] = value
    return data, text[end_idx + 4 :]


def count_h1(text: str) -> int:
    count = 0
    in_fence = False
    for line in text.splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
        elif not in_fence and line.startswith("# "):
            count += 1
    return count


def expand_patterns(repo_root: str, patterns: List[str]) -> List[str]:
    results: List[str] = []
    for pattern in patterns:
        full = os.path.join(repo_root, pattern)
        matches = glob.glob(full, recursive=True)
        results.extend(matches)
    return sorted(set(results))


def list_tracked_files(root: str) -> List[str]:
    result = subprocess.run(
        ["git", "-c", "core.quotepath=false", "-C", root, "ls-files"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _should_exclude_repo_path(parts: List[str]) -> bool:
    excludes = {
        ".git",
        ".ruff_cache",
        "__pycache__",
        ".mypy_cache",
        ".idea",
        ".vscode",
        "node_modules",
        "99_Trash",
    }
    return any(part in excludes for part in parts)


def build_repo_tree_from_paths(paths: List[str]) -> str:
    lines = ["."]
    root: Dict[str, Any] = {"dirs": {}, "files": set()}

    for rel_path in paths:
        normalized = rel_path.replace("\\", "/").strip("/")
        if not normalized:
            continue
        parts = normalized.split("/")
        if _should_exclude_repo_path(parts):
            continue

        node = root
        for part in parts[:-1]:
            dirs = node["dirs"]
            if part not in dirs:
                dirs[part] = {"dirs": {}, "files": set()}
            node = dirs[part]
        node["files"].add(parts[-1])

    def walk(node: Dict[str, Any], prefix: str = "") -> None:
        entries: List[Tuple[str, bool, Dict[str, Any] | None]] = []
        for name, child in node["dirs"].items():
            entries.append((name, True, child))
        for name in node["files"]:
            entries.append((name, False, None))

        entries.sort(key=lambda item: item[0])
        count = len(entries)
        for idx, (name, is_dir, child) in enumerate(entries):
            last = idx == count - 1
            connector = "+-- " if last else "|-- "
            lines.append(f"{prefix}{connector}{name}{'/' if is_dir else ''}")
            if is_dir and child is not None:
                extension = "    " if last else "|   "
                walk(child, prefix + extension)

    walk(root)
    return "\n".join(lines)


def build_repo_tree(root: str) -> str:
    tracked = list_tracked_files(root)
    if tracked:
        return build_repo_tree_from_paths(tracked)

    excludes = {
        ".git",
        ".ruff_cache",
        "__pycache__",
        ".mypy_cache",
        ".idea",
        ".vscode",
        "node_modules",
        "99_Trash",
    }
    lines = ["."]

    def walk(path: str, prefix: str = "") -> None:
        entries = []
        for name in sorted(os.listdir(path)):
            if name in excludes:
                continue
            full = os.path.join(path, name)
            entries.append((name, os.path.isdir(full)))
        count = len(entries)
        for idx, (name, is_dir) in enumerate(entries):
            last = idx == count - 1
            connector = "+-- " if last else "|-- "
            lines.append(f"{prefix}{connector}{name}{'/' if is_dir else ''}")
            if is_dir:
                extension = "    " if last else "|   "
                walk(os.path.join(path, name), prefix + extension)

    walk(root)
    return "\n".join(lines)


def check_markdownlint(paths: List[str], errors: List[str], command: str, repo_root: str) -> None:
    cmd_parts: List[str]
    npx_fallback: List[str] | None = None
    if command == "markdownlint":
        node_bin = shutil.which("node")
        appdata = os.environ.get("APPDATA") or ""
        cli_path = os.path.join(appdata, "npm", "node_modules", "markdownlint-cli", "markdownlint.js")
        if node_bin and os.path.exists(cli_path):
            cmd_parts = [node_bin, cli_path]
        elif shutil.which(command):
            cmd_parts = [command]
            npx_bin = shutil.which("npx") or shutil.which("npx.cmd")
            if npx_bin:
                npx_fallback = [npx_bin, "markdownlint-cli"]
        else:
            npx_bin = shutil.which("npx") or shutil.which("npx.cmd")
            if npx_bin:
                cmd_parts = [npx_bin, "markdownlint-cli"]
            else:
                errors.append(f"VS015: {command} not found in PATH")
                return
    elif shutil.which(command):
        cmd_parts = [command]
    else:
        errors.append(f"VS015: {command} not found in PATH")
        return
    if not paths:
        errors.append("VS015: no paths configured for markdownlint")
        return

    def is_cmd_too_long(message: str) -> bool:
        return "command line is too long" in message.lower()

    def run_markdownlint(selected_paths: List[str]) -> subprocess.CompletedProcess[str] | None:
        env = None
        if not os.environ.get("NPM_CONFIG_CACHE"):
            cache_root = os.path.join(repo_root, ".cache", "npm")
            os.makedirs(cache_root, exist_ok=True)
            env = os.environ.copy()
            env["NPM_CONFIG_CACHE"] = cache_root
        try:
            return subprocess.run(
                [*cmd_parts, *selected_paths],
                capture_output=True,
                text=True,
                check=False,
                env=env,
                cwd=repo_root,
            )
        except OSError as exc:
            if getattr(exc, "winerror", None) == 206 or is_cmd_too_long(str(exc)):
                return subprocess.CompletedProcess(
                    args=[*cmd_parts, *selected_paths],
                    returncode=1,
                    stdout="",
                    stderr="command line is too long",
                )
            if npx_fallback is not None:
                try:
                    return subprocess.run(
                        [*npx_fallback, *selected_paths],
                        capture_output=True,
                        text=True,
                        check=False,
                        env=env,
                        cwd=repo_root,
                    )
                except OSError:
                    errors.append(f"VS015: failed to execute {cmd_parts[0]}: {exc}")
                    return None
            errors.append(f"VS015: failed to execute {cmd_parts[0]}: {exc}")
            return None

    result = run_markdownlint(paths)
    if result is None:
        return
    if result.returncode != 0:
        detail = result.stdout.strip() or result.stderr.strip()
        if detail and is_cmd_too_long(detail):
            max_cmd_len = 7000
            base_len = sum(len(part) + 1 for part in cmd_parts)
            chunk: List[str] = []
            chunk_len = base_len
            for path in paths:
                path_len = len(path) + 1
                if chunk and (chunk_len + path_len > max_cmd_len):
                    chunk_result = run_markdownlint(chunk)
                    if chunk_result is None:
                        return
                    if chunk_result.returncode != 0:
                        chunk_detail = chunk_result.stdout.strip() or chunk_result.stderr.strip()
                        message = chunk_detail if chunk_detail else "markdownlint returned non-zero exit code"
                        errors.append(f"VS015: markdownlint failed: {message}")
                        return
                    chunk = [path]
                    chunk_len = base_len + path_len
                else:
                    chunk.append(path)
                    chunk_len += path_len
            if chunk:
                chunk_result = run_markdownlint(chunk)
                if chunk_result is None:
                    return
                if chunk_result.returncode != 0:
                    chunk_detail = chunk_result.stdout.strip() or chunk_result.stderr.strip()
                    message = chunk_detail if chunk_detail else "markdownlint returned non-zero exit code"
                    errors.append(f"VS015: markdownlint failed: {message}")
                    return
            return
        message = detail if detail else "markdownlint returned non-zero exit code"
        errors.append(f"VS015: markdownlint failed: {message}")


def check_repo_structure_consistency(structure_root: str, map_paths: List[str], errors: List[str]) -> None:
    expected = build_repo_tree(structure_root).replace("\r\n", "\n")
    for path in map_paths:
        if not os.path.exists(path):
            errors.append(f"VS016: map file missing {path}")
            continue
        actual = read_text(path).replace("\r\n", "\n")
        if actual != expected:
            errors.append(f"VS016: repo structure map out of date: {path}")


def resolve_repo_structure_paths(repo_root: str, configured_paths: List[str]) -> List[str]:
    """Resolve repo map paths for monorepo and split-repo modes.

    Canonical target is <repo_root>/repo_structure.txt.
    Compatibility target (legacy monorepo layout) is <repo_root>/../repo_structure.txt.
    When canonical exists, prefer it exclusively to avoid validating stale fallback maps.
    """
    resolved: List[str] = []
    seen: set[str] = set()
    base_paths = configured_paths or ["repo_structure.txt"]

    for rel in base_paths:
        joined = os.path.normpath(os.path.join(repo_root, rel))
        candidates = [joined]

        if os.path.basename(rel) == "repo_structure.txt":
            canonical = os.path.normpath(os.path.join(repo_root, "repo_structure.txt"))
            fallback = os.path.normpath(os.path.join(repo_root, "..", "repo_structure.txt"))
            candidates = [canonical] if os.path.exists(canonical) else [canonical, fallback]

        for path in candidates:
            if path not in seen:
                resolved.append(path)
                seen.add(path)
    return resolved


def check_ambiguous_terms(files: List[str], patterns: List[str], warnings: List[str], rule_id: str) -> None:
    compiled = [re.compile(pat, flags=re.IGNORECASE) for pat in patterns]
    for path in files:
        text = read_text(path)
        for pattern in compiled:
            if pattern.search(text):
                warnings.append(f"{rule_id}: {path} contains ambiguous term '{pattern.pattern}'")


def check_forbidden_patterns(
    files: List[str],
    patterns: List[str],
    errors: List[str],
    warnings: List[str],
    severity: str,
    rule_id: str,
) -> None:
    compiled = [re.compile(pat, flags=re.IGNORECASE) for pat in patterns]
    for path in files:
        text = read_text(path)
        for pattern in compiled:
            if pattern.search(text):
                record_issue(
                    errors,
                    warnings,
                    severity,
                    f"{rule_id}: forbidden pattern '{pattern.pattern}' found in {path}",
                )


def read_local_work_repo_names(repo_root: str) -> List[str]:
    config_path = os.path.join(repo_root, ".ai_ops", "local", "config.yaml")
    if not os.path.exists(config_path):
        return []

    names: set[str] = set()
    text = read_text(config_path)
    for match in re.finditer(r"^\s*-\s*path:\s*([^\s#]+)", text, flags=re.MULTILINE):
        raw = match.group(1).strip().strip('"').strip("'")
        raw = raw.rstrip("/\\")
        candidate = os.path.basename(raw)
        if candidate:
            names.add(candidate)
    return sorted(names)


def record_issue(errors: List[str], warnings: List[str], severity: str, message: str) -> None:
    if severity == "warning":
        warnings.append(message)
    else:
        errors.append(message)


def parse_config(path: str) -> Dict[str, Any]:
    """
    Minimal parser for validator_config.yaml. Supports top-level keys, lists, and
    nested dicts with two-space indentation.
    """
    lines = read_text(path).splitlines()
    data: Dict[str, Any] = {}
    current_rule: Dict[str, Any] | None = None
    current_param_key: str | None = None
    in_rules = False
    in_paths = False
    in_params = False
    in_include_paths = False

    def add_rule():
        nonlocal current_rule
        if current_rule is not None:
            data.setdefault("rules", []).append(current_rule)
        current_rule = {}

    for raw in lines:
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        if raw.startswith("version:"):
            data["version"] = raw.split(":", 1)[1].strip()
            continue
        if raw.startswith("validator_id:"):
            data["validator_id"] = raw.split(":", 1)[1].strip()
            continue
        if raw.startswith("description:"):
            data["description"] = raw.split(":", 1)[1].strip()
            continue
        if raw.startswith("inputs:"):
            data["inputs"] = {}
            continue
        if raw.strip().startswith("repo_root:"):
            data.setdefault("inputs", {})["repo_root"] = raw.split(":", 1)[1].strip()
            continue
        if raw.strip().startswith("include_paths:"):
            in_include_paths = True
            data.setdefault("inputs", {})["include_paths"] = []
            continue
        if in_include_paths and raw.strip().startswith("- "):
            data["inputs"]["include_paths"].append(raw.strip()[2:].strip())
            continue
        if raw.startswith("rules:"):
            in_include_paths = False
            in_rules = True
            data["rules"] = []
            continue

        if in_rules and raw.strip().startswith("- id:"):
            add_rule()
            current_rule["id"] = raw.split(":", 1)[1].strip()
            in_paths = False
            in_params = False
            continue

        if current_rule is None:
            continue

        if raw.strip().startswith("enabled:"):
            current_rule["enabled"] = raw.split(":", 1)[1].strip().lower() == "true"
            continue
        if raw.strip().startswith("paths:"):
            in_paths = True
            in_params = False
            current_rule["paths"] = []
            continue
        if in_paths and raw.strip().startswith("- "):
            current_rule["paths"].append(raw.strip()[2:].strip())
            continue
        if raw.strip().startswith("params:"):
            in_params = True
            in_paths = False
            current_rule["params"] = {}
            current_param_key = None
            continue
        if in_params and raw.strip().startswith("- ") and current_param_key:
            item = raw.strip()[2:].strip().strip("'").strip('"')
            current_rule["params"].setdefault(current_param_key, []).append(item)
            continue
        if in_params and ":" in raw:
            key, val = raw.strip().split(":", 1)
            val = val.strip().strip("'").strip('"')
            if val == "":
                current_rule["params"][key] = []
                current_param_key = key
            else:
                current_rule["params"][key] = val
                current_param_key = None
            continue

    add_rule()
    return data


def check_front_matter(files: List[str], errors: List[str]) -> None:
    for path in files:
        text = read_text(path)
        if not text.startswith("---"):
            errors.append(f"VS001: {path} missing front matter delimiter")
            continue
        if "\n---" not in text[3:]:
            errors.append(f"VS001: {path} front matter not closed")


def check_single_h1(files: List[str], errors: List[str]) -> None:
    for path in files:
        text = read_text(path)
        h1_count = count_h1(text)
        if h1_count != 1:
            errors.append(f"VS002: {path} has {h1_count} H1 headings")


def check_status_values(files: List[str], errors: List[str]) -> None:
    for path in files:
        text = read_text(path)
        fm, _ = split_front_matter(text)
        status = fm.get("status")
        if not status:
            errors.append(f"VS003: {path} missing status in front matter")
            continue
        if status not in ALLOWED_STATUS:
            errors.append(f"VS003: {path} has invalid status '{status}'")


def check_required_fields(files: List[str], required: List[str], errors: List[str], rule_id: str) -> None:
    for path in files:
        text = read_text(path)
        fm, _ = split_front_matter(text)
        for key in required:
            if key not in fm:
                errors.append(f"{rule_id}: {path} missing front matter key '{key}'")


def check_required_fields_warn(
    files: List[str],
    required: List[str],
    warnings: List[str],
    rule_id: str,
    new_only: bool = False,
    repo_root: str = "",
) -> None:
    """Check required frontmatter fields; emit warnings (not errors). Supports new_only mode."""
    candidates = list(files)
    if new_only and repo_root:
        new_paths = set(_list_new_git_paths(repo_root))
        candidates = [p for p in candidates if p in new_paths]
    for path in candidates:
        text = read_text(path)
        fm, _ = split_front_matter(text)
        for key in required:
            if key not in fm:
                warnings.append(f"{rule_id}: {path} missing front matter key '{key}'")


def check_status_field_values(
    files: List[str],
    allowed: set,
    errors: List[str],
    rule_id: str,
) -> None:
    """VS030: Check that status field value is in the allowed set. Emit error if invalid."""
    allowed_sorted = sorted(allowed)
    for path in files:
        text = read_text(path)
        fm, _ = split_front_matter(text)
        status = fm.get("status")
        if status is None:
            continue  # Missing status is caught by VS006/VS003; not this rule's concern
        if status not in allowed:
            errors.append(
                f"{rule_id}: {path} has invalid status '{status}'."
                f" Allowed values: {allowed_sorted}"
            )


def check_workflow_routing_contract(
    files: List[str],
    errors: List[str],
    warnings: List[str],
    severity: str,
    rule_id: str,
    required_sections: List[str],
    required_content: List[str],
) -> None:
    """VS031: Check that workflow files contain required routing contract section and wording."""
    all_required = required_sections + required_content
    for path in files:
        text = read_text(path)
        for item in all_required:
            if item not in text:
                record_issue(
                    errors,
                    warnings,
                    severity,
                    f"{rule_id}: {path} missing required routing contract string: '{item}'",
                )


def check_active_status_has_purpose(
    files: List[str],
    warnings: List[str],
    rule_id: str,
) -> None:
    """VS032: Flag status:active files that are missing a ## Purpose heading."""
    purpose_re = re.compile(r"^##\s+Purpose\b", re.MULTILINE)
    for path in files:
        text = read_text(path)
        fm, body = split_front_matter(text)
        status = fm.get("status")
        if status != "active":
            continue
        if not purpose_re.search(body):
            warnings.append(
                f"{rule_id}: {path} has status:active but is missing a '## Purpose' heading"
            )


def check_prefix_in_dir(dir_path: str, prefix: str, warnings: List[str], rule_id: str) -> None:
    if not os.path.isdir(dir_path):
        warnings.append(f"{rule_id}: directory missing {dir_path}")
        return
    for entry in os.listdir(dir_path):
        if entry.lower() == "README.md".lower():
            continue
        if entry.startswith("."):
            continue
        full = os.path.join(dir_path, entry)
        if os.path.isdir(full):
            continue
        if entry.endswith(".md") and not entry.startswith(prefix):
            warnings.append(f"{rule_id}: {entry} does not use prefix '{prefix}'")


def check_workbook_prefix(base_dir: str, warnings: List[str]) -> None:
    for root, _, files in os.walk(base_dir):
        if (
            "wp_" in os.path.basename(root)
            or "wb_" in os.path.basename(root)
            or "templates" in root
            or "backlog" in root
            or "outputs" in root
        ):
            continue
        for name in files:
            if not name.endswith(".md"):
                continue
            if name.lower() == "README.md".lower():
                continue
            if not name.startswith("wb_"):
                warnings.append(f"VS008: {os.path.join(root, name)} missing wb_ prefix")


def check_module_yaml_id(paths: List[str], errors: List[str]) -> None:
    for path in paths:
        text = read_text(path)
        module_dir = os.path.basename(os.path.dirname(os.path.dirname(path)))
        match = re.search(r"^\s*id:\s*([A-Za-z0-9_]+)\s*$", text, flags=re.MULTILINE)
        if not match:
            errors.append(f"VS009: {path} missing id")
        elif match.group(1) != module_dir:
            errors.append(f"VS009: {path} id '{match.group(1)}' does not match folder '{module_dir}'")


def check_module_yaml_status(paths: List[str], errors: List[str]) -> None:
    for path in paths:
        text = read_text(path)
        statuses = re.findall(r"^\s*status:\s*([A-Za-z0-9_]+)\s*$", text, flags=re.MULTILINE)
        for status in statuses:
            if status not in ALLOWED_STATUS:
                errors.append(f"VS010: {path} has invalid status '{status}'")


def check_required_paths(paths: List[str], issues: List[str], rule_id: str) -> None:
    for path in paths:
        if not os.path.exists(path):
            issues.append(f"{rule_id}: missing required path {path}")


def check_future_work_registry(path: str, warnings: List[str]) -> None:
    if not os.path.exists(path):
        warnings.append("VS012: future_work_registry.yaml missing")
        return
    text = read_text(path)
    entries = re.split(r"^\s*-\s+id:\s*", text, flags=re.MULTILINE)
    for entry in entries[1:]:
        block = "id: " + entry
        for key in ["source_workbook", "scope", "priority", "created"]:
            if re.search(rf"^\s*{key}\s*:", block, flags=re.MULTILINE) is None:
                warnings.append(f"VS012: entry missing '{key}'")
                break
    log_path = os.path.join(os.path.dirname(path), "..", "logs", "log_workbook_run.md")
    log_path = os.path.normpath(log_path)
    if os.path.exists(log_path):
        log_text = read_text(log_path)
        for match in re.findall(r"source_workbook:\s*([^\n]+)", text):
            if match in log_text:
                warnings.append(f"VS012: source_workbook completed in run log: {match}")


def check_registry_paths(
    paths: List[str],
    path_keys: List[str],
    errors: List[str],
    warnings: List[str],
    severity: str,
    repo_root: str,
) -> None:
    key_pattern = "|".join(re.escape(key) for key in path_keys)
    path_re = re.compile(rf"^\s*({key_pattern})\s*:\s*(\S+)\s*$", flags=re.MULTILINE)
    for path in paths:
        text = read_text(path)
        for match in path_re.findall(text):
            entry_path = match[1]
            if entry_path.startswith("http"):
                continue
            full_path = os.path.normpath(os.path.join(repo_root, entry_path))
            if not os.path.exists(full_path):
                record_issue(errors, warnings, severity, f"VS018: registry path missing: {entry_path} ({path})")


def check_program_completeness(
    workprogram_glob: str,
    runprogram_globs: List[str],
    required_workprogram_files: List[str],
    required_runprogram_files: List[str],
    errors: List[str],
    warnings: List[str],
    severity: str,
    repo_root: str,
) -> None:
    workprogram_pattern = (
        workprogram_glob if os.path.isabs(workprogram_glob) else os.path.join(repo_root, workprogram_glob)
    )
    workprograms = glob.glob(workprogram_pattern)
    for program in workprograms:
        for pattern in required_workprogram_files:
            matches = glob.glob(os.path.join(program, pattern))
            if not matches:
                record_issue(
                    errors,
                    warnings,
                    severity,
                    f"VS019: workprogram missing {pattern} in {program}",
                )

    for run_glob in runprogram_globs:
        run_pattern = run_glob if os.path.isabs(run_glob) else os.path.join(repo_root, run_glob)
        for program in glob.glob(run_pattern):
            for pattern in required_runprogram_files:
                matches = glob.glob(os.path.join(program, pattern))
                if not matches:
                    record_issue(
                        errors,
                        warnings,
                        severity,
                        f"VS019: runprogram missing {pattern} in {program}",
                    )


def check_guide_index(
    guide_index: str,
    guide_glob: str,
    errors: List[str],
    warnings: List[str],
    severity: str,
    repo_root: str,
) -> None:
    index_path = guide_index if os.path.isabs(guide_index) else os.path.join(repo_root, guide_index)
    glob_pattern = guide_glob if os.path.isabs(guide_glob) else os.path.join(repo_root, guide_glob)
    if not os.path.exists(index_path):
        record_issue(errors, warnings, severity, f"VS020: guide index missing {guide_index}")
        return
    index_text = read_text(index_path)
    for path in glob.glob(glob_pattern, recursive=True):
        if os.path.basename(path).lower() == "README.md".lower():
            continue
        fm, _ = split_front_matter(read_text(path))
        if fm.get("status") == "deprecated":
            continue
        if os.path.basename(path) not in index_text:
            record_issue(errors, warnings, severity, f"VS020: guide not indexed: {path}")


def check_log_marker(path: str, marker: str, errors: List[str], warnings: List[str], severity: str) -> None:
    if not os.path.exists(path):
        record_issue(errors, warnings, severity, f"VS021: log missing {path}")
        return
    text = read_text(path)
    if marker not in text:
        record_issue(errors, warnings, severity, f"VS021: log missing marker '{marker}' ({path})")


def check_ascii_only(paths: List[str], errors: List[str], warnings: List[str], severity: str) -> None:
    for path in paths:
        text = read_text(path)
        if re.search(r"[^\x00-\x7F]", text):
            record_issue(errors, warnings, severity, f"VS022: non-ASCII content detected: {path}")


def _extract_yaml_list(text: str, key: str) -> List[str]:
    values: List[str] = []
    lines = text.splitlines()
    in_block = False
    block_indent = 0

    for line in lines:
        if not in_block:
            match = re.match(rf"^(\s*){re.escape(key)}\s*:\s*$", line)
            if match:
                in_block = True
                block_indent = len(match.group(1))
            continue

        if not line.strip():
            continue
        line_indent = len(line) - len(line.lstrip(" "))
        if line_indent <= block_indent and not line.lstrip().startswith("- "):
            break

        item_match = re.match(r"^\s*-\s+(.+?)\s*$", line)
        if item_match:
            value = item_match.group(1).strip().strip('"').strip("'")
            values.append(value)

    return values


def _resolve_ref_path(source_file: str, ref: str, repo_root: str) -> str:
    if os.path.isabs(ref):
        return os.path.normpath(ref)
    if ref.startswith("./") or ref.startswith("../"):
        return os.path.normpath(os.path.join(os.path.dirname(source_file), ref))
    return os.path.normpath(os.path.join(repo_root, ref))


def _is_skippable_ref(ref: str) -> bool:
    if not ref:
        return True
    if any(token in ref for token in ("<", ">")):
        return True
    if ref.startswith(("http://", "https://", "mailto:", "#")):
        return True
    if ref.startswith("`") and ref.endswith("`"):
        return True
    return False


def check_reference_paths_exist(
    paths: List[str],
    errors: List[str],
    warnings: List[str],
    severity: str,
    check_markdown_links: bool,
    check_related_lists: bool,
    repo_root: str,
) -> None:
    markdown_link_re = re.compile(r"\[[^\]]+\]\(([^)]+)\)")

    for path in paths:
        text = read_text(path)
        refs: List[Tuple[str, str]] = []

        if check_related_lists:
            for key in ("related", "related_refs"):
                for ref in _extract_yaml_list(text, key):
                    refs.append((key, ref))

        if check_markdown_links:
            for link in markdown_link_re.findall(text):
                refs.append(("markdown_link", link))

        for ref_type, ref in refs:
            normalized_ref = ref.split("#", 1)[0].strip()
            if _is_skippable_ref(normalized_ref):
                continue
            resolved = _resolve_ref_path(path, normalized_ref, repo_root)
            if not os.path.exists(resolved):
                record_issue(
                    errors,
                    warnings,
                    severity,
                    f"VS023: missing {ref_type} reference '{normalized_ref}' in {path}",
                )


def check_required_sections(
    paths: List[str],
    required_sections: List[str],
    errors: List[str],
    warnings: List[str],
    severity: str,
    rule_id: str,
) -> None:
    for path in paths:
        text = read_text(path)
        for section in required_sections:
            if section not in text:
                record_issue(
                    errors,
                    warnings,
                    severity,
                    f"{rule_id}: required section '{section}' missing in {path}",
                )


def check_workbook_command_path_base_consistency(
    paths: List[str],
    errors: List[str],
    warnings: List[str],
    severity: str,
) -> None:
    # Guard against mixing repo-prefixed and repo-root-relative paths in one command block.
    command_langs = {"", "powershell", "pwsh", "shell", "bash", "sh", "cmd"}
    repo_prefixed_re = re.compile(
        r"(^|[\s\"'])([A-Za-z0-9][A-Za-z0-9_.-]*)/(?:00_Admin|01_Resources|02_Modules|03_Modules|90_Sandbox|99_Trash|\.ai_ops|\.agent)/"
    )
    root_relative_re = re.compile(
        r"(^|[\s\"'])((?:00_Admin|01_Resources|02_Modules|03_Modules|90_Sandbox|99_Trash|\.ai_ops|\.agent)/)"
    )
    block_re = re.compile(r"```([^\n`]*)\n(.*?)\n```", flags=re.DOTALL)

    for path in paths:
        text = read_text(path)
        for block_idx, match in enumerate(block_re.finditer(text), start=1):
            info = match.group(1).strip().lower()
            if info not in command_langs:
                continue

            block = match.group(2)
            has_prefixed = False
            has_relative = False

            for raw_line in block.splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if repo_prefixed_re.search(line):
                    has_prefixed = True
                if root_relative_re.search(line):
                    has_relative = True

            if has_prefixed and has_relative:
                record_issue(
                    errors,
                    warnings,
                    severity,
                    f"VS026: mixed command path bases in fenced block {block_idx} ({path})",
                )


def _list_new_git_paths(repo_root: str) -> List[str]:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return []

    if result.returncode != 0:
        return []

    new_paths: List[str] = []
    for raw_line in result.stdout.splitlines():
        line = raw_line.rstrip()
        if len(line) < 4:
            continue
        status = line[:2]
        rel_path = line[3:]
        if "->" in rel_path:
            rel_path = rel_path.split("->", 1)[1].strip()

        is_untracked = status == "??"
        is_added = status.startswith("A") or status.endswith("A")
        if not (is_untracked or is_added):
            continue

        full_path = os.path.normpath(os.path.join(repo_root, rel_path))
        new_paths.append(full_path)

    return sorted(set(new_paths))


def check_unreferenced_new_artifacts(
    paths: List[str],
    reference_globs: List[str],
    exclude_globs: List[str],
    new_only: bool,
    errors: List[str],
    warnings: List[str],
    severity: str,
    repo_root: str,
) -> None:
    if not paths:
        return

    candidates = sorted(set(paths))
    if new_only:
        new_paths = set(_list_new_git_paths(repo_root))
        candidates = [path for path in candidates if path in new_paths]
        if not candidates:
            return

    excluded: set[str] = set()
    for pattern in exclude_globs:
        excluded.update(expand_patterns(repo_root, [pattern]))

    filtered_candidates = [path for path in candidates if path not in excluded and os.path.isfile(path)]
    if not filtered_candidates:
        return

    reference_paths = expand_patterns(repo_root, reference_globs)
    reference_paths = [path for path in reference_paths if os.path.isfile(path)]
    if not reference_paths:
        return

    reference_texts: Dict[str, str] = {}
    for ref_path in reference_paths:
        try:
            reference_texts[ref_path] = read_text(ref_path)
        except OSError:
            continue

    for candidate in filtered_candidates:
        rel_candidate = os.path.relpath(candidate, repo_root).replace("\\", "/")
        name_candidate = os.path.basename(candidate)
        found = False

        for ref_path, text in reference_texts.items():
            if ref_path == candidate:
                continue
            if rel_candidate in text or name_candidate in text:
                found = True
                break

        if not found:
            record_issue(
                errors,
                warnings,
                severity,
                f"VS025: new artifact is not referenced by docs/indexes: {rel_candidate}",
            )


def check_related_paths(files: List[str], warnings: List[str]) -> None:
    for path in files:
        text = read_text(path)
        if "related:" not in text:
            continue
        fm, _ = split_front_matter(text)
        if not fm:
            continue
        related_lines = []
        in_related = False
        for line in text.splitlines():
            if re.match(r"^\s*related\s*:", line):
                in_related = True
                continue
            if in_related:
                if re.match(r"^\s*-\s+", line):
                    related_lines.append(line.strip()[2:].strip())
                elif line.strip() and not line.startswith(" "):
                    break
        for rel in related_lines:
            if (
                "/" in rel
                or rel.startswith("./")
                or rel.startswith("../")
                or rel.startswith("00_Admin")
                or rel.startswith("01_Resources")
            ):
                continue
            warnings.append(f"VS014: {path} related path not repo-relative: {rel}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default=None,
        help=(
            "Validator config path. Relative paths resolve against --repo-root. "
            "If omitted, uses 00_Admin/configs/validator/validator_config.yaml "
            "relative to this script."
        ),
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help=(
            "Repo root used to resolve configured paths. Defaults to the ai_ops "
            "repo root inferred from this script location (with git-root fallback)."
        ),
    )
    parser.add_argument(
        "--structure-root",
        default=None,
        help="Root path used for repo structure map validation (VS016). Defaults to git root.",
    )
    args = parser.parse_args()

    cwd = os.getcwd()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_repo_root = os.path.normpath(os.path.join(script_dir, "..", ".."))
    default_config_probe = os.path.join(
        default_repo_root,
        "00_Admin",
        "configs",
        "validator",
        "validator_config.yaml",
    )
    if not os.path.exists(default_config_probe):
        default_repo_root = detect_git_root(script_dir)
    repo_root = resolve_repo_root(args.repo_root, default_repo_root)
    if args.config:
        if os.path.isabs(args.config):
            config_path = args.config
        else:
            config_from_cwd = os.path.normpath(os.path.join(cwd, args.config))
            config_from_repo = os.path.normpath(os.path.join(repo_root, args.config))
            config_path = config_from_cwd if os.path.exists(config_from_cwd) else config_from_repo
    else:
        config_path = os.path.normpath(
            os.path.join(script_dir, "..", "configs", "validator", "validator_config.yaml")
        )
    if not os.path.exists(config_path):
        print(f"Config not found: {config_path}")
        return 1

    config = parse_config(config_path)
    rules = config.get("rules", [])
    if not rules:
        print(f"Validator config parse failure: no rules parsed from {config_path}")
        return 1

    errors: List[str] = []
    warnings: List[str] = []
    structure_root = (
        os.path.normpath(args.structure_root)
        if args.structure_root
        else detect_git_root(repo_root)
    )

    for rule in rules:
        if not rule.get("enabled", True):
            continue
        rule_id = rule.get("id")
        paths = expand_patterns(repo_root, rule.get("paths", []))

        if rule_id == "VS001":
            check_front_matter(paths, errors)
        elif rule_id == "VS002":
            check_single_h1(paths, errors)
        elif rule_id == "VS003":
            check_status_values(paths, errors)
        elif rule_id == "VS004":
            check_required_fields(paths, rule.get("params", {}).get("required_fields", []), errors, rule_id)
        elif rule_id == "VS005":
            check_required_fields(paths, rule.get("params", {}).get("required_fields", []), errors, rule_id)
        elif rule_id == "VS006":
            check_required_fields(paths, rule.get("params", {}).get("required_fields", []), errors, rule_id)
        elif rule_id == "VS007":
            check_prefix_in_dir(os.path.join(repo_root, "00_Admin/runbooks"), "rb_", warnings, rule_id)
        elif rule_id == "VS008":
            check_workbook_prefix(os.path.join(repo_root, "90_Sandbox/ai_workbooks"), warnings)
        elif rule_id == "VS009":
            check_module_yaml_id(paths, errors)
        elif rule_id == "VS010":
            check_module_yaml_status(paths, errors)
        elif rule_id == "VS011":
            check_required_paths(paths, errors, rule_id)
        elif rule_id == "VS012":
            check_future_work_registry(paths[0] if paths else "", warnings)
        elif rule_id == "VS013":
            repo_map_paths = resolve_repo_structure_paths(repo_root, rule.get("paths", []))
            existing = [path for path in repo_map_paths if os.path.exists(path)]
            if not existing:
                warnings.append(
                    f"VS013: missing required path (checked any-of): {', '.join(repo_map_paths)}"
                )
        elif rule_id == "VS014":
            check_related_paths(paths, warnings)
        elif rule_id == "VS015":
            command = rule.get("params", {}).get("command", "markdownlint")
            check_markdownlint(paths, errors, command, repo_root)
        elif rule_id == "VS016":
            repo_map_paths = resolve_repo_structure_paths(repo_root, rule.get("paths", []))
            existing = [path for path in repo_map_paths if os.path.exists(path)]
            if not existing:
                errors.append(
                    f"VS016: map file missing (checked any-of): {', '.join(repo_map_paths)}"
                )
            else:
                check_repo_structure_consistency(structure_root, existing, errors)
        elif rule_id == "VS017":
            patterns = rule.get("params", {}).get("forbidden_terms", [])
            if patterns:
                check_ambiguous_terms(paths, patterns, warnings, rule_id)
        elif rule_id == "VS018":
            severity = rule.get("params", {}).get("severity", "error")
            path_keys = rule.get("params", {}).get("path_keys", [])
            if path_keys:
                check_registry_paths(paths, path_keys, errors, warnings, severity, repo_root)
        elif rule_id == "VS019":
            severity = rule.get("params", {}).get("severity", "error")
            workprogram_glob = rule.get("params", {}).get("workprogram_glob", "")
            runprogram_globs = rule.get("params", {}).get("runprogram_globs", [])
            required_workprogram_files = rule.get("params", {}).get("required_workprogram_files", [])
            required_runprogram_files = rule.get("params", {}).get("required_runprogram_files", [])
            if workprogram_glob:
                check_program_completeness(
                    workprogram_glob,
                    runprogram_globs,
                    required_workprogram_files,
                    required_runprogram_files,
                    errors,
                    warnings,
                    severity,
                    repo_root,
                )
        elif rule_id == "VS020":
            severity = rule.get("params", {}).get("severity", "error")
            guide_index = rule.get("params", {}).get("guide_index", "")
            guide_glob = rule.get("params", {}).get("guide_glob", "")
            if guide_index and guide_glob:
                check_guide_index(guide_index, guide_glob, errors, warnings, severity, repo_root)
        elif rule_id == "VS021":
            severity = rule.get("params", {}).get("severity", "error")
            marker = rule.get("params", {}).get("required_marker", "")
            if marker and paths:
                check_log_marker(paths[0], marker, errors, warnings, severity)
        elif rule_id == "VS022":
            severity = rule.get("params", {}).get("severity", "error")
            check_ascii_only(paths, errors, warnings, severity)
        elif rule_id == "VS023":
            params = rule.get("params", {})
            severity = params.get("severity", "error")
            check_markdown_links = str(params.get("check_markdown_links", "true")).lower() == "true"
            check_related_lists = str(params.get("check_related_lists", "true")).lower() == "true"
            check_reference_paths_exist(
                paths,
                errors,
                warnings,
                severity,
                check_markdown_links,
                check_related_lists,
                repo_root,
            )
        elif rule_id == "VS024":
            params = rule.get("params", {})
            severity = params.get("severity", "error")
            required_sections = params.get("required_sections", [])
            if required_sections:
                check_required_sections(paths, required_sections, errors, warnings, severity, rule_id)
        elif rule_id == "VS027":
            params = rule.get("params", {})
            severity = params.get("severity", "error")
            required_sections = params.get("required_sections", [])
            if required_sections:
                check_required_sections(paths, required_sections, errors, warnings, severity, rule_id)
        elif rule_id == "VS025":
            params = rule.get("params", {})
            severity = params.get("severity", "warning")
            reference_paths = params.get("reference_paths", [])
            exclude_globs = params.get("exclude_globs", [])
            new_only = str(params.get("new_only", "true")).lower() == "true"
            if reference_paths:
                check_unreferenced_new_artifacts(
                    paths,
                    reference_paths,
                    exclude_globs,
                    new_only,
                    errors,
                    warnings,
                    severity,
                    repo_root,
                )
        elif rule_id == "VS026":
            params = rule.get("params", {})
            severity = params.get("severity", "warning")
            check_workbook_command_path_base_consistency(paths, errors, warnings, severity)
        elif rule_id == "VS029":
            params = rule.get("params", {})
            new_only = str(params.get("new_only", "true")).lower() == "true"
            required_fields = params.get("required_fields", [])
            if required_fields:
                check_required_fields_warn(paths, required_fields, warnings, rule_id, new_only, repo_root)
        elif rule_id == "VS030":
            params = rule.get("params", {})
            allowed = set(params.get("allowed_status", list(ALLOWED_STATUS)))
            check_status_field_values(paths, allowed, errors, rule_id)
        elif rule_id == "VS031":
            params = rule.get("params", {})
            severity = params.get("severity", "error")
            req_sections = params.get("required_sections", [])
            req_content = params.get("required_content", [])
            check_workflow_routing_contract(
                paths, errors, warnings, severity, rule_id, req_sections, req_content
            )
        elif rule_id == "VS028":
            params = rule.get("params", {})
            severity = params.get("severity", "error")
            patterns = list(params.get("forbidden_patterns", []))
            allow_repo_names = set(params.get("allow_repo_names", ["ai_ops"]))
            # Compute workspace root dynamically so absolute-path patterns work
            # for any user's machine, not just the repo author's workspace.
            _ws_norm = os.path.normpath(os.path.dirname(os.path.normpath(repo_root)))
            _ws_fwd = _ws_norm.replace("\\", "/")
            _ws_fwd_esc = re.escape(_ws_fwd)
            _ws_bwd_esc = re.escape(_ws_norm)  # normpath uses os.sep; re.escape handles backslashes
            for repo_name in read_local_work_repo_names(repo_root):
                if repo_name in allow_repo_names:
                    continue
                escaped = re.escape(repo_name)
                patterns.extend(
                    [
                        rf"\b{escaped}\b",
                        rf"\.\./{escaped}\b",
                        rf"\.\.\\{escaped}\b",
                        rf"{_ws_fwd_esc}/{escaped}\b",
                        rf"{_ws_bwd_esc}{re.escape(os.sep)}{escaped}\b",
                    ]
                )
            patterns = list(dict.fromkeys(patterns))
            if patterns:
                check_forbidden_patterns(paths, patterns, errors, warnings, severity, rule_id)
        elif rule_id == "VS032":
            check_active_status_has_purpose(paths, warnings, rule_id)

    if errors:
        print("Validator errors:")
        for err in errors:
            print(f"- {err}")
    if warnings:
        print("Validator warnings:")
        for warn in warnings:
            print(f"- {warn}")

    if errors:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
