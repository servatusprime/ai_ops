#!/usr/bin/env python3
"""Propagate allow/ask/deny permission rules from settings_global_template.json to
workspace and governed-repo .claude/settings.json files.

Usage:
  python sync_claude_settings.py --check [OPTIONS]
  python sync_claude_settings.py --write [OPTIONS]

Modes:
  --check   Compare target(s) to template allow/ask/deny; report per-target status
            without writing. Exit 0 = no drift. Exit 1 = drift or error.
  --write   Write allow/ask/deny rules from template to target(s), preserving all
            other target keys (e.g. hooks) and safe repo-local extra allow entries.
            Ask-gated Git mutation/network additions are always removed. Use --strict
            when the target must contain only template permissions.
            Exit 0 = success. Exit 1 = error.

Target selection (mutually exclusive):
  --target PATH   Single explicit target file.
                  Default: .claude/settings.json relative to --workspace-root.
  --all           Target workspace root settings.json plus all repos listed in
                  workspace.work_repos in .ai_ops/local/config.yaml.
                  Requires PyYAML (pip install pyyaml).

Drift semantics:
  Missing template entries  -> drift (exit 1).
  Extra target-only entries -> repo-local additions (reported, exit 0) unless
  they overlap a template ask rule, which is drift (exit 1).

Allow list write behavior:
  All template entries are written first. Repo-local extra allow entries that
  are not in the template are preserved, not removed.
  Ask and deny lists: merged unions (template entries first).

Global-only keys stripped before applying to workspace/repo targets:
  defaultMode, additionalDirectories, _comment, effortLevel
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import tempfile
from pathlib import Path

LOG = logging.getLogger(__name__)

GLOBAL_ONLY_KEYS: set[str] = {
    "defaultMode",
    "additionalDirectories",
    "_comment",
    "effortLevel",
}

DEFAULT_TEMPLATE = Path(
    "ai_ops/01_Resources/templates/config/settings_global_template.json"
)
DEFAULT_TARGET = Path(".claude/settings.json")
DEFAULT_CONFIG = Path("ai_ops/.ai_ops/local/config.yaml")

STATUS_CLEAN = "clean"            # all template entries present, no extra allows
STATUS_LOCAL_ADDS = "local_adds"  # all template entries present, has extra allows
STATUS_DRIFT = "drift"            # missing template entries
STATUS_SKIPPED = "skipped"        # target file does not exist (--check only)
STATUS_ERROR = "error"            # unhandled read/write failure
REPARSE_POINT = 0x400
PROMPT_REQUIRED_ALLOW_RE = re.compile(
    r"(?:git\s+(?:-C\b|.*\b(?:push|commit|reset|checkout|clean|rm|fetch|pull|"
    r"clone|ls-remote|submodule|remote|send-pack|receive-pack|upload-pack|"
    r"http-fetch|http-push)\b)|git-remote\*|"
    r"Bash\((?:gh|curl|powershell|pwsh)(?=[\s:)])|^PowerShell(?:\(|$))",
    re.IGNORECASE,
)


def is_reparse(path: Path) -> bool:
    try:
        info = path.lstat()
    except OSError:
        return False
    return path.is_symlink() or bool(getattr(info, "st_file_attributes", 0) & REPARSE_POINT)


def assert_no_reparse_components(path: Path, root: Path, label: str) -> None:
    """Inspect lexical components so resolving a link cannot hide its parent."""
    trusted = Path(os.path.abspath(os.fspath(root)))
    lexical = Path(os.path.abspath(os.fspath(path)))
    try:
        relative = lexical.relative_to(trusted)
    except ValueError as exc:
        raise ValueError(f"{label} escapes workspace root: {path}") from exc
    current = trusted
    for part in relative.parts:
        current = current / part
        if current.exists() and is_reparse(current):
            raise ValueError(f"{label} crosses a symlink/reparse point: {path}")


def resolve_trusted(path: str | Path, root: Path, *, label: str, must_exist: bool = False) -> Path:
    """Resolve a target while refusing workspace escapes and reparse paths."""
    trusted = root.resolve(strict=True)
    candidate = Path(path)
    lexical = candidate if candidate.is_absolute() else trusted / candidate
    resolved = lexical.resolve(strict=False)
    try:
        resolved.relative_to(trusted)
    except ValueError as exc:
        raise ValueError(f"{label} escapes workspace root: {path}") from exc
    if must_exist and not resolved.exists():
        raise FileNotFoundError(f"{label} does not exist: {resolved}")
    assert_no_reparse_components(lexical, trusted, label)
    return resolved


def setup_logging(*, verbose: bool) -> None:
    """Configure logging level and format."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(message)s")


def resolve(path: str | Path, root: Path) -> Path:
    """Resolve path relative to root unless already absolute."""
    return resolve_trusted(path, root, label="configured path")


def load_json(path: Path) -> dict:
    """Load JSON from path; return empty dict if file does not exist."""
    if not path.exists():
        return {}
    if is_reparse(path):
        raise ValueError(f"refusing to read symlink/reparse settings file: {path}")
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"settings file must contain a JSON object: {path}")
    return data


def extract_permissions(data: dict) -> tuple[list, list, list]:
    """Return (allow, ask, deny) from the permissions block."""
    perms = data.get("permissions", {})
    allow = [e for e in perms.get("allow", []) if isinstance(e, str)]
    ask = [e for e in perms.get("ask", []) if isinstance(e, str)]
    deny = [e for e in perms.get("deny", []) if isinstance(e, str)]
    return allow, ask, deny


def merge_deny(template_deny: list, target_deny: list) -> list:
    """Union: template entries first, then target-only additions."""
    seen: set[str] = set(template_deny)
    result = list(template_deny)
    for entry in target_deny:
        if entry not in seen:
            result.append(entry)
            seen.add(entry)
    return result


def check_target(
    template_allow: list,
    template_ask: list,
    template_deny: list,
    target_data: dict,
) -> tuple[str, list[str], list[str]]:
    """Analyse one target. Return (status, drift_lines, local_add_lines).

    drift_lines     -- human-readable missing-entry descriptions (cause exit 1).
    local_add_lines -- extra target entries beyond template (informational only).
    """
    target_perms = target_data.get("permissions", {})
    target_allow = target_perms.get("allow", [])
    target_ask = target_perms.get("ask", [])
    target_deny = target_perms.get("deny", [])

    missing_allow = [e for e in template_allow if e not in target_allow]
    missing_ask = [e for e in template_ask if e not in target_ask]
    extra_allow = [e for e in target_allow if e not in template_allow]
    missing_deny = [e for e in template_deny if e not in target_deny]

    drift_lines: list[str] = []
    if missing_allow:
        drift_lines.append(
            f"  allow missing ({len(missing_allow)}):\n"
            + "\n".join(f"    {e}" for e in missing_allow)
        )
    if missing_ask:
        drift_lines.append(
            f"  ask missing ({len(missing_ask)}):\n"
            + "\n".join(f"    {e}" for e in missing_ask)
        )
    if missing_deny:
        drift_lines.append(
            f"  deny missing ({len(missing_deny)}):\n"
            + "\n".join(f"    {e}" for e in missing_deny)
        )

    local_add_lines: list[str] = []
    if extra_allow:
        local_add_lines.append(
            f"  allow local additions ({len(extra_allow)}):\n"
            + "\n".join(f"    {e}" for e in extra_allow)
        )

    dangerous = [
        entry for entry in extra_allow
        if PROMPT_REQUIRED_ALLOW_RE.search(str(entry))
    ]
    if dangerous:
        drift_lines.append(
            f"  ask-overlap local additions ({len(dangerous)}):\n"
            + "\n".join(f"    {e}" for e in dangerous)
        )

    if drift_lines:
        status = STATUS_DRIFT
    elif local_add_lines:
        status = STATUS_LOCAL_ADDS
    else:
        status = STATUS_CLEAN

    return status, drift_lines, local_add_lines


def build_merged(
    template_allow: list,
    template_ask: list,
    template_deny: list,
    existing: dict,
    *,
    strict: bool = False,
) -> dict:
    """Return merged settings dict without writing to disk.

    Allow list: template entries first, then safe repo-local extras preserved.
    Ask and deny lists: unions (template-first), retaining restrictive local rules.
    Global-only keys stripped.
    """
    result = {k: v for k, v in existing.items() if k not in GLOBAL_ONLY_KEYS}
    existing_perms = existing.get("permissions", {})
    existing_allow = existing_perms.get("allow", [])
    existing_ask = existing_perms.get("ask", [])

    template_set = set(template_allow)
    extra_allows = [
        e for e in existing_allow
        if e not in template_set and not PROMPT_REQUIRED_ALLOW_RE.search(str(e))
    ]
    if strict:
        extra_allows = []
    merged_allow = template_allow + extra_allows
    merged_ask = list(dict.fromkeys(template_ask + [
        e for e in existing_ask if isinstance(e, str) and e not in template_ask
    ]))
    merged_deny = merge_deny(template_deny, existing_perms.get("deny", []))

    perms = {k: v for k, v in existing_perms.items() if k not in ("allow", "ask", "deny")}
    perms["allow"] = merged_allow
    perms["ask"] = merged_ask
    perms["deny"] = merged_deny
    result["permissions"] = perms
    return result


def write_target(path: Path, merged: dict) -> None:
    """Atomically replace a trusted settings file with JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and is_reparse(path):
        raise ValueError(f"refusing to replace symlink/reparse settings file: {path}")
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", prefix=f".{path.name}.", suffix=".tmp",
            dir=path.parent, delete=False
        ) as handle:
            temp_name = handle.name
            json.dump(merged, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        Path(temp_name).replace(path)
    except Exception:
        if temp_name:
            Path(temp_name).unlink(missing_ok=True)
        raise


def load_work_repos(config_path: Path, workspace_root: Path) -> list[Path]:
    """Return resolved repo root paths from workspace.work_repos in config.yaml."""
    try:
        import yaml  # type: ignore[import]
    except ImportError:
        LOG.error("PyYAML required for --all mode. Install: pip install pyyaml")
        return []

    if not config_path.exists():
        LOG.warning("Config not found: %s — no work_repos loaded.", config_path)
        return []

    with config_path.open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    repos: list[Path] = []
    for entry in cfg.get("workspace", {}).get("work_repos", []):
        rel = entry.get("path", "")
        if not rel:
            continue
        p = Path(rel)
        try:
            resolved = resolve_trusted(p, workspace_root, label="work repo", must_exist=True)
        except (ValueError, FileNotFoundError) as exc:
            raise ValueError(f"untrusted work repo {rel!r}: {exc}") from exc
        repos.append(resolved)
    return repos


def run_check(
    targets: list[tuple[str, Path]],
    template_allow: list,
    template_ask: list,
    template_deny: list,
) -> int:
    """Run --check against all targets. Return 0 if no drift, 1 if drift or error."""
    any_drift = False
    for label, settings_path in targets:
        LOG.info("Target : %s", label)
        LOG.info("Path   : %s", settings_path)
        if not settings_path.exists():
            LOG.info("Status : %s (file not found)", STATUS_SKIPPED)
            LOG.info("")
            continue
        try:
            target_data = load_json(settings_path)
        except Exception as exc:  # noqa: BLE001
            LOG.error("Status : %s — %s", STATUS_ERROR, exc)
            any_drift = True
            LOG.info("")
            continue

        status, drift_lines, local_add_lines = check_target(
            template_allow, template_ask, template_deny, target_data
        )
        LOG.info("Status : %s", status)
        for line in drift_lines:
            LOG.info("%s", line)
        for line in local_add_lines:
            LOG.info("%s", line)
        if status == STATUS_DRIFT:
            any_drift = True
        LOG.info("")

    return 1 if any_drift else 0


def run_write(
    targets: list[tuple[str, Path]],
    template_allow: list,
    template_ask: list,
    template_deny: list,
    *,
    strict: bool = False,
) -> int:
    """Run --write against all targets. Return 0 on success, 1 on error."""
    any_error = False
    for label, settings_path in targets:
        LOG.info("Target : %s", label)
        LOG.info("Path   : %s", settings_path)
        existing = load_json(settings_path)
        try:
            merged = build_merged(
                template_allow, template_ask, template_deny, existing, strict=strict
            )
            write_target(settings_path, merged)
        except Exception as exc:  # noqa: BLE001
            LOG.error("Status : %s — %s", STATUS_ERROR, exc)
            any_error = True
            LOG.info("")
            continue

        final_allow = merged.get("permissions", {}).get("allow", [])
        final_ask = merged.get("permissions", {}).get("ask", [])
        final_deny = merged.get("permissions", {}).get("deny", [])
        stripped = [k for k in existing if k in GLOBAL_ONLY_KEYS]
        LOG.info("Status  : written")
        LOG.info("Allow   : %d entries", len(final_allow))
        LOG.info("Ask     : %d entries", len(final_ask))
        LOG.info("Deny    : %d entries", len(final_deny))
        if stripped:
            LOG.info("Stripped: %s", ", ".join(stripped))
        LOG.info("")

    return 1 if any_error else 0


def resolve_targets(
    args: argparse.Namespace,
    root: Path,
) -> list[tuple[str, Path]]:
    """Return list of (label, settings_path) for all targets."""
    if args.all:
        config_path = resolve(args.config, root)
        LOG.debug("Config : %s", config_path)
        work_repos = load_work_repos(config_path, root)
        targets: list[tuple[str, Path]] = [
            ("workspace", resolve(DEFAULT_TARGET, root))
        ]
        for repo_root in work_repos:
            try:
                label = str(repo_root.relative_to(root))
            except ValueError:
                label = str(repo_root)
            targets.append((label, repo_root / ".claude" / "settings.json"))
        return targets

    return [("target", resolve(args.target, root))]


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Report drift without writing")
    mode.add_argument("--write", action="store_true", help="Write allow/ask/deny to target(s)")

    target_grp = parser.add_mutually_exclusive_group()
    target_grp.add_argument(
        "--target",
        default=str(DEFAULT_TARGET),
        metavar="PATH",
        help=f"Single target settings file (default: {DEFAULT_TARGET})",
    )
    target_grp.add_argument(
        "--all",
        action="store_true",
        help="Target workspace + all work_repos from config (requires PyYAML)",
    )
    parser.add_argument(
        "--workspace-root",
        default=".",
        metavar="PATH",
        help="Workspace root (default: current directory)",
    )
    parser.add_argument(
        "--template",
        default=str(DEFAULT_TEMPLATE),
        metavar="PATH",
        help=f"Template file (default: {DEFAULT_TEMPLATE})",
    )
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG),
        metavar="PATH",
        help=f"ai_ops local config for work_repos (default: {DEFAULT_CONFIG})",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Drop all target-only allow entries during --write (otherwise safe local additions remain).",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging.")
    return parser.parse_args()


def main() -> int:
    """Program entrypoint."""
    args = parse_args()
    setup_logging(verbose=args.verbose)

    root = Path(args.workspace_root).resolve()
    try:
        template_path = resolve(args.template, root)
    except (ValueError, FileNotFoundError) as exc:
        LOG.error("ERROR: %s", exc)
        return 1

    LOG.info("Workspace root : %s", root)
    LOG.info("Template       : %s", template_path)
    LOG.info("")

    if not template_path.exists():
        LOG.error("ERROR: Template not found: %s", template_path)
        return 1

    try:
        template_data = load_json(template_path)
        template_allow, template_ask, template_deny = extract_permissions(template_data)
        targets = resolve_targets(args, root)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        LOG.error("ERROR: %s", exc)
        return 1

    if args.check:
        return run_check(targets, template_allow, template_ask, template_deny)
    return run_write(
        targets, template_allow, template_ask, template_deny, strict=args.strict
    )


if __name__ == "__main__":
    raise SystemExit(main())
