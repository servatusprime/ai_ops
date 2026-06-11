#!/usr/bin/env python3
"""Propagate allow/deny permission rules from settings_global_template.json to
workspace and governed-repo .claude/settings.json files.

Usage:
  python sync_claude_settings.py --check [OPTIONS]
  python sync_claude_settings.py --write [OPTIONS]

Modes:
  --check   Compare target(s) to template allow/deny; report per-target status
            without writing. Exit 0 = no drift. Exit 1 = drift or error.
  --write   Write allow/deny rules from template to target(s), preserving all
            other target keys (e.g. hooks) and repo-local extra allow entries.
            Exit 0 = success. Exit 1 = error.

Target selection (mutually exclusive):
  --target PATH   Single explicit target file.
                  Default: .claude/settings.json relative to --workspace-root.
  --all           Target workspace root settings.json plus all repos listed in
                  workspace.work_repos in .ai_ops/local/config.yaml.
                  Requires PyYAML (pip install pyyaml).

Drift semantics:
  Missing template entries  -> drift (exit 1).
  Extra target-only entries -> repo-local additions (reported, exit 0).

Allow list write behavior:
  All template entries are written first. Repo-local extra allow entries that
  are not in the template are preserved, not removed.
  Deny list: merged union (template entries first).

Global-only keys stripped before applying to workspace/repo targets:
  defaultMode, additionalDirectories, _comment, effortLevel
"""

from __future__ import annotations

import argparse
import json
import logging
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


def setup_logging(*, verbose: bool) -> None:
    """Configure logging level and format."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(message)s")


def resolve(path: str | Path, root: Path) -> Path:
    """Resolve path relative to root unless already absolute."""
    p = Path(path)
    if p.is_absolute():
        return p
    return (root / p).resolve()


def load_json(path: Path) -> dict:
    """Load JSON from path; return empty dict if file does not exist."""
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def extract_permissions(data: dict) -> tuple[list, list]:
    """Return (allow, deny) from the permissions block."""
    perms = data.get("permissions", {})
    allow = [e for e in perms.get("allow", []) if isinstance(e, str)]
    deny = [e for e in perms.get("deny", []) if isinstance(e, str)]
    return allow, deny


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
    template_deny: list,
    target_data: dict,
) -> tuple[str, list[str], list[str]]:
    """Analyse one target. Return (status, drift_lines, local_add_lines).

    drift_lines     -- human-readable missing-entry descriptions (cause exit 1).
    local_add_lines -- extra target entries beyond template (informational only).
    """
    target_perms = target_data.get("permissions", {})
    target_allow = target_perms.get("allow", [])
    target_deny = target_perms.get("deny", [])

    missing_allow = [e for e in template_allow if e not in target_allow]
    extra_allow = [e for e in target_allow if e not in template_allow]
    missing_deny = [e for e in template_deny if e not in target_deny]

    drift_lines: list[str] = []
    if missing_allow:
        drift_lines.append(
            f"  allow missing ({len(missing_allow)}):\n"
            + "\n".join(f"    {e}" for e in missing_allow)
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

    if drift_lines:
        status = STATUS_DRIFT
    elif local_add_lines:
        status = STATUS_LOCAL_ADDS
    else:
        status = STATUS_CLEAN

    return status, drift_lines, local_add_lines


def build_merged(
    template_allow: list,
    template_deny: list,
    existing: dict,
) -> dict:
    """Return merged settings dict without writing to disk.

    Allow list: template entries first, then repo-local extras preserved.
    Deny list: union (template-first).
    Global-only keys stripped.
    """
    result = {k: v for k, v in existing.items() if k not in GLOBAL_ONLY_KEYS}
    existing_perms = existing.get("permissions", {})
    existing_allow = existing_perms.get("allow", [])

    template_set = set(template_allow)
    extra_allows = [e for e in existing_allow if e not in template_set]
    merged_allow = template_allow + extra_allows
    merged_deny = merge_deny(template_deny, existing_perms.get("deny", []))

    perms = {k: v for k, v in existing_perms.items() if k not in ("allow", "deny")}
    perms["allow"] = merged_allow
    perms["deny"] = merged_deny
    result["permissions"] = perms
    return result


def write_target(path: Path, merged: dict) -> None:
    """Write merged settings dict to path as JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(merged, f, indent=2)
        f.write("\n")


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
        resolved = p if p.is_absolute() else (workspace_root / p).resolve()
        repos.append(resolved)
    return repos


def run_check(
    targets: list[tuple[str, Path]],
    template_allow: list,
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
            template_allow, template_deny, target_data
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
    template_deny: list,
) -> int:
    """Run --write against all targets. Return 0 on success, 1 on error."""
    any_error = False
    for label, settings_path in targets:
        LOG.info("Target : %s", label)
        LOG.info("Path   : %s", settings_path)
        existing = load_json(settings_path)
        try:
            merged = build_merged(template_allow, template_deny, existing)
            write_target(settings_path, merged)
        except Exception as exc:  # noqa: BLE001
            LOG.error("Status : %s — %s", STATUS_ERROR, exc)
            any_error = True
            LOG.info("")
            continue

        final_allow = merged.get("permissions", {}).get("allow", [])
        final_deny = merged.get("permissions", {}).get("deny", [])
        stripped = [k for k in existing if k in GLOBAL_ONLY_KEYS]
        LOG.info("Status  : written")
        LOG.info("Allow   : %d entries", len(final_allow))
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
    mode.add_argument("--write", action="store_true", help="Write allow/deny to target(s)")

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
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging.")
    return parser.parse_args()


def main() -> int:
    """Program entrypoint."""
    args = parse_args()
    setup_logging(verbose=args.verbose)

    root = Path(args.workspace_root).resolve()
    template_path = resolve(args.template, root)

    LOG.info("Workspace root : %s", root)
    LOG.info("Template       : %s", template_path)
    LOG.info("")

    if not template_path.exists():
        LOG.error("ERROR: Template not found: %s", template_path)
        return 1

    template_data = load_json(template_path)
    template_allow, template_deny = extract_permissions(template_data)
    targets = resolve_targets(args, root)

    if args.check:
        return run_check(targets, template_allow, template_deny)
    return run_write(targets, template_allow, template_deny)


if __name__ == "__main__":
    raise SystemExit(main())
