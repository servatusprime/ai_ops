#!/usr/bin/env python3
"""Generate wrapper exports from .ai_ops/workflows source-of-truth files.

Outputs:
- plugins/ai-ops-governance/commands/*.md
- plugins/ai-ops-governance/skills/*/SKILL.md (kebab-case skill names)
- .claude/skills/*/SKILL.md (only when `--targets` includes `claude`)
- .ai_ops/exports/manifest.yaml
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None


WORKFLOW_PRIMARY_REL = Path(".ai_ops/workflows")
PLUGIN_COMMANDS_REL = Path("plugins/ai-ops-governance/commands")
PLUGIN_SKILLS_REL = Path("plugins/ai-ops-governance/skills")
CLAUDE_SKILLS_REL = Path(".claude/skills")
CODEX_PRIMARY_SKILLS_REL = Path(".agents/skills")
CODEX_COMPAT_SKILLS_REL = Path(".codex/skills")
EXPORT_MANIFEST_PRIMARY_REL = Path(".ai_ops/exports/manifest.yaml")

# Canonical pointer basis per install scope.
# repo: wrappers installed inside the repo root (e.g. ai_ops/.claude/skills/)
# workspace: wrappers installed at workspace root (e.g. <workspace_root>/.claude/skills/)
SCOPE_WORKFLOW_RELS: Dict[str, str] = {
    "repo": ".ai_ops/workflows",
    "workspace": "ai_ops/.ai_ops/workflows",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_yaml() -> None:
    if yaml is None:
        raise RuntimeError("PyYAML is required. Install with: pip install pyyaml")


def sha12(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]


def read_frontmatter(path: Path) -> Tuple[Dict, str]:
    ensure_yaml()
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n(.*)$", text, flags=re.DOTALL)
    if not match:
        raise ValueError(f"Missing frontmatter in workflow: {path}")
    frontmatter_text, body = match.groups()
    data = yaml.safe_load(frontmatter_text) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Frontmatter must be a mapping: {path}")
    return data, body


def normalize_description(value: object, fallback_name: str) -> str:
    if isinstance(value, str):
        compact = " ".join(value.split())
        if compact:
            return compact
    return f"Execute the /{fallback_name} workflow."


def to_kebab(name: str) -> str:
    return name.replace("_", "-")


def to_frontmatter(data: Dict) -> str:
    ensure_yaml()
    rendered = yaml.safe_dump(data, sort_keys=False, allow_unicode=False).strip()
    return f"---\n{rendered}\n---\n"


def render_skill_wrapper(
    name: str,
    description: str,
    workflow_name: str | None = None,
    workflow_rel: str = ".ai_ops/workflows",
) -> str:
    workflow_ref = workflow_name or name
    frontmatter = to_frontmatter(
        {
            "name": name,
            "description": description,
        }
    )
    return (
        f"{frontmatter}\n"
        f"# {name}\n\n"
        f"Read `{workflow_rel}/{workflow_ref}.md` and follow its instructions.\n"
    )


def render_command_wrapper(
    name: str,
    description: str,
    argument_hint: object,
    allowed_tools: object,
    workflow_rel: str = ".ai_ops/workflows",
) -> str:
    frontmatter: Dict[str, object] = {"description": description}
    if isinstance(argument_hint, str) and argument_hint.strip():
        frontmatter["argument-hint"] = argument_hint
    if isinstance(allowed_tools, str) and allowed_tools.strip() and allowed_tools.lower() != "null":
        frontmatter["allowed-tools"] = allowed_tools

    rendered_frontmatter = to_frontmatter(frontmatter)
    return (
        f"{rendered_frontmatter}\n"
        f"# /{name}\n\n"
        f"Read `{workflow_rel}/{name}.md` and follow its instructions.\n"
    )


def write_text(path: Path, content: str, dry_run: bool) -> None:
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content.strip() + "\n")


def resolve_workflow_dir(repo_root: Path) -> Path:
    return repo_root / WORKFLOW_PRIMARY_REL


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate command/skill wrappers from .ai_ops/workflows source files."
    )
    parser.add_argument(
        "--targets",
        nargs="+",
        choices=["plugin", "claude", "codex"],
        default=["plugin"],
        help="Export targets to generate.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview actions without writing files.",
    )
    parser.add_argument(
        "--codex-compat",
        action="store_true",
        help="Also generate codex compatibility mirror (.codex/skills) when codex target is enabled.",
    )
    parser.add_argument(
        "--scope",
        choices=["repo", "workspace"],
        default="repo",
        help=(
            "Install scope that determines the workflow pointer path written into wrappers. "
            "'repo' (default): pointer is '.ai_ops/workflows/<name>.md' (wrappers inside repo root). "
            "'workspace': pointer is 'ai_ops/.ai_ops/workflows/<name>.md' (wrappers at workspace root)."
        ),
    )
    args = parser.parse_args()
    workflow_rel = SCOPE_WORKFLOW_RELS[args.scope]

    repo_root = Path(__file__).resolve().parents[2]
    workflow_dir = resolve_workflow_dir(repo_root)
    if not workflow_dir.exists():
        print(f"[FAIL] Missing workflow directory: {workflow_dir}")
        return 1

    workflow_paths = sorted(workflow_dir.glob("*.md"))
    if not workflow_paths:
        print(f"[FAIL] No workflow files found under {workflow_dir}")
        return 1

    generated_at = now_iso()
    generation_targets = set(args.targets)
    # Manifest targets define which outputs are required by drift checks.
    # Default to plugin-only so user-specific surfaces (e.g. repo-root .claude)
    # are not required in the repo unless explicitly generated.
    manifest_targets = {"plugin"}
    if "claude" in generation_targets:
        manifest_targets.add("claude")
    if "codex" in generation_targets:
        manifest_targets.add("codex")

    manifest_items: List[Dict] = []
    write_count = 0

    for workflow_path in workflow_paths:
        name = workflow_path.stem
        frontmatter, _ = read_frontmatter(workflow_path)
        description = normalize_description(frontmatter.get("description"), name)
        claude_meta = frontmatter.get("claude", {})
        if not isinstance(claude_meta, dict):
            claude_meta = {}
        argument_hint = claude_meta.get("argument-hint")
        allowed_tools = claude_meta.get("allowed-tools")

        source_rel = workflow_path.relative_to(repo_root).as_posix()
        item_outputs: List[Dict[str, str]] = []

        if "plugin" in manifest_targets:
            command_path = repo_root / PLUGIN_COMMANDS_REL / f"{name}.md"
            command_content = render_command_wrapper(
                name=name,
                description=description,
                argument_hint=argument_hint,
                allowed_tools=allowed_tools,
                workflow_rel=workflow_rel,
            )
            if "plugin" in generation_targets:
                write_text(command_path, command_content, args.dry_run)
                write_count += 1
            item_outputs.append(
                {
                    "path": command_path.relative_to(repo_root).as_posix(),
                    "kind": "plugin_command",
                    "sha256_12": sha12(command_content),
                }
            )

            plugin_skill_name = to_kebab(name)
            plugin_skill_path = repo_root / PLUGIN_SKILLS_REL / plugin_skill_name / "SKILL.md"
            plugin_skill_content = render_skill_wrapper(
                name=plugin_skill_name,
                description=description,
                workflow_name=name,
                workflow_rel=workflow_rel,
            )
            if "plugin" in generation_targets:
                write_text(plugin_skill_path, plugin_skill_content, args.dry_run)
                write_count += 1
            item_outputs.append(
                {
                    "path": plugin_skill_path.relative_to(repo_root).as_posix(),
                    "kind": "plugin_skill",
                    "sha256_12": sha12(plugin_skill_content),
                }
            )

        if "claude" in manifest_targets:
            claude_skill_path = repo_root / CLAUDE_SKILLS_REL / name / "SKILL.md"
            claude_skill_content = render_skill_wrapper(
                name=name, description=description, workflow_rel=workflow_rel
            )
            if "claude" in generation_targets:
                write_text(claude_skill_path, claude_skill_content, args.dry_run)
                write_count += 1
            item_outputs.append(
                {
                    "path": claude_skill_path.relative_to(repo_root).as_posix(),
                    "kind": "claude_skill",
                    "sha256_12": sha12(claude_skill_content),
                }
            )

        if "codex" in manifest_targets:
            codex_skill_content = render_skill_wrapper(
                name=name, description=description, workflow_rel=workflow_rel
            )

            codex_primary_path = repo_root / CODEX_PRIMARY_SKILLS_REL / name / "SKILL.md"
            if "codex" in generation_targets:
                write_text(codex_primary_path, codex_skill_content, args.dry_run)
                write_count += 1
            item_outputs.append(
                {
                    "path": codex_primary_path.relative_to(repo_root).as_posix(),
                    "kind": "codex_skill_primary",
                    "sha256_12": sha12(codex_skill_content),
                }
            )

            if args.codex_compat:
                codex_compat_path = repo_root / CODEX_COMPAT_SKILLS_REL / name / "SKILL.md"
                if "codex" in generation_targets:
                    write_text(codex_compat_path, codex_skill_content, args.dry_run)
                    write_count += 1
                item_outputs.append(
                    {
                        "path": codex_compat_path.relative_to(repo_root).as_posix(),
                        "kind": "codex_skill_compat",
                        "sha256_12": sha12(codex_skill_content),
                    }
                )

        manifest_items.append(
            {
                "workflow": name,
                "source": source_rel,
                "source_sha256_12": sha12(workflow_path.read_text(encoding="utf-8")),
                "description": description,
                "outputs": item_outputs,
            }
        )

    manifest_output_count = sum(len(item.get("outputs", [])) for item in manifest_items)
    manifest = {
        "generated_at": generated_at,
        "generator": "00_Admin/scripts/generate_workflow_exports.py",
        "source_root": workflow_dir.relative_to(repo_root).as_posix(),
        "scope": args.scope,
        "workflow_pointer_basis": workflow_rel,
        "naming_policies": {
            "source_workflows": "snake_case filenames (authoritative)",
            "plugin_skills": {
                "naming": "kebab-case directory/name",
                "reason": "Claude skills contract requires lowercase letters, numbers, and hyphens.",
            },
            "plugin_commands": "snake_case passthrough from workflow filename",
            "claude_project_skills": "snake_case passthrough from workflow filename",
            "codex_skills": "snake_case passthrough from workflow filename",
        },
        "targets": sorted(manifest_targets),
        "generation_targets": sorted(generation_targets),
        "workflow_count": len(workflow_paths),
        "output_count": write_count,
        "manifest_output_count": manifest_output_count,
        "workflows": manifest_items,
    }

    ensure_yaml()
    manifest_content = yaml.safe_dump(
        manifest,
        sort_keys=False,
        allow_unicode=False,
    )
    manifest_path = repo_root / EXPORT_MANIFEST_PRIMARY_REL
    write_text(manifest_path, manifest_content, args.dry_run)

    print("[OK] Workflow export generation complete.")
    print(f"Scope: {args.scope} (pointer basis: {workflow_rel})")
    print(f"Manifest targets: {sorted(manifest_targets)}")
    print(f"Generation targets: {sorted(generation_targets)}")
    print(f"Workflows processed: {len(workflow_paths)}")
    print(f"Outputs generated: {write_count}")
    print(f"Manifest: {manifest_path.relative_to(repo_root)}")
    if args.dry_run:
        print("Dry run: no files written.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
