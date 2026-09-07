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

# Which manifest target each output "kind" belongs to. Used to merge a
# target-subset run's manifest with the previous manifest's entries for
# targets NOT regenerated this run, instead of dropping them -- a
# target-subset run must not silently disarm the drift check for surfaces
# it did not touch.
KIND_TO_TARGET: Dict[str, str] = {
    "plugin_command": "plugin",
    "plugin_skill": "plugin",
    "claude_skill": "claude",
    "codex_skill_primary": "codex",
    "codex_skill_primary_openai_yaml": "codex",
    "codex_skill_compat": "codex",
    "codex_skill_compat_openai_yaml": "codex",
}

# Canonical pointer basis per install scope.
# repo: wrappers installed inside the repo root (e.g. ai_ops/.claude/skills/)
# workspace: wrappers installed at workspace root (e.g. <workspace_root>/.claude/skills/)
SCOPE_WORKFLOW_RELS: Dict[str, str] = {
    "repo": ".ai_ops/workflows",
    "workspace": "ai_ops/.ai_ops/workflows",
}



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
    disable_model_invocation: object = None,
    model: object = None,
    context: object = None,
    agent: object = None,
    codex_short_description: object = None,
) -> str:
    workflow_ref = workflow_name or name
    frontmatter: Dict[str, object] = {
        "name": name,
        "description": description,
    }
    if disable_model_invocation is True:
        frontmatter["disable-model-invocation"] = True
    if isinstance(model, str) and model.strip() and model.lower() != "null":
        frontmatter["model"] = model
    if isinstance(context, str) and context.strip().lower() == "fork":
        frontmatter["context"] = "fork"
        if isinstance(agent, str) and agent.strip() and agent.lower() != "null":
            frontmatter["agent"] = agent
    # Codex-only: metadata.short-description, required and schema-validated
    # at the source (REQUIRED_CODEX_METADATA_KEYS). Never set for
    # Claude-surface calls.
    if isinstance(codex_short_description, str) and codex_short_description.strip():
        frontmatter["metadata"] = {"short-description": codex_short_description}
    rendered_frontmatter = to_frontmatter(frontmatter)
    return (
        f"{rendered_frontmatter}\n"
        f"# {name}\n\n"
        f"Read `{workflow_rel}/{workflow_ref}.md` and follow its instructions.\n"
    )


def render_openai_yaml(
    display_name: str,
    short_description: str,
    allow_implicit_invocation: object = None,
) -> str:
    ensure_yaml()
    data: Dict[str, object] = {
        "interface": {
            "display_name": display_name,
            "short_description": short_description,
        }
    }
    # allow_implicit_invocation lives here per Codex's documented contract
    # (learn.chatgpt.com/docs/build-skills): Codex puts this policy field
    # in agents/openai.yaml, not SKILL.md frontmatter, unlike Claude's
    # disable-model-invocation.
    if isinstance(allow_implicit_invocation, bool):
        data["policy"] = {"allow_implicit_invocation": allow_implicit_invocation}
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=False)


def render_command_wrapper(
    name: str,
    description: str,
    argument_hint: object,
    allowed_tools: object,
    workflow_rel: str = ".ai_ops/workflows",
    disable_model_invocation: object = None,
    model: object = None,
) -> str:
    frontmatter: Dict[str, object] = {"description": description}
    if isinstance(argument_hint, str) and argument_hint.strip():
        frontmatter["argument-hint"] = argument_hint
    if isinstance(allowed_tools, str) and allowed_tools.strip() and allowed_tools.lower() != "null":
        frontmatter["allowed-tools"] = allowed_tools
    if disable_model_invocation is True:
        frontmatter["disable-model-invocation"] = True
    if isinstance(model, str) and model.strip() and model.lower() != "null":
        frontmatter["model"] = model

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
        "--print-manifest",
        action="store_true",
        help=(
            "Print the freshly-computed manifest as YAML to stdout, delimited by "
            "'---MANIFEST-BEGIN---'/'---MANIFEST-END---' markers. Intended for "
            "--dry-run use by check_workflow_exports_drift.py, which needs the "
            "manifest this run WOULD produce (independently re-rendered from current "
            "source) rather than trusting the manifest.yaml already on disk."
        ),
    )
    parser.add_argument(
        "--codex-compat",
        action="store_true",
        help="Also generate codex compatibility mirror (.codex/skills) when codex target is enabled.",
    )
    parser.add_argument(
        "--scope",
        choices=["repo", "workspace", "user"],
        default="repo",
        help=(
            "Install scope that determines the workflow pointer path written into wrappers. "
            "'repo' (default): pointer is '.ai_ops/workflows/<name>.md' (wrappers inside repo root). "
            "'workspace': pointer is 'ai_ops/.ai_ops/workflows/<name>.md' (wrappers at workspace root). "
            "'user': pointer is an absolute path to this repo's own .ai_ops/workflows -- there is "
            "no fixed relative path from a user-global install root (e.g. $HOME) to the repo. "
            "Pair with '--install-root <user_root>'."
        ),
    )
    parser.add_argument(
        "--install-root",
        type=str,
        default=None,
        help=(
            "Override the OUTPUT root for the claude/codex skill surfaces only "
            "(plugin outputs and the manifest always stay repo-root-relative). "
            "Independent of --scope, which only controls the pointer-basis "
            "string written into wrapper content. Use with '--scope workspace "
            "--install-root <workspace_root>' to write real, full-field "
            "wrappers directly to a workspace root instead of the repo tree, "
            "so the setup scripts need no separate per-file fallback for "
            "workspace-scope installs. When set to a path outside "
            "the repo, claude/codex skill outputs are written but excluded "
            "from the drift-checked manifest, which tracks repo-local "
            "generation only."
        ),
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    install_root = Path(args.install_root).resolve() if args.install_root else repo_root
    manifest_scoped_write = install_root == repo_root
    if args.scope == "user":
        workflow_rel = (repo_root / WORKFLOW_PRIMARY_REL).as_posix()
    else:
        workflow_rel = SCOPE_WORKFLOW_RELS[args.scope]
    workflow_dir = resolve_workflow_dir(repo_root)
    if not workflow_dir.exists():
        print(f"[FAIL] Missing workflow directory: {workflow_dir}")
        return 1

    workflow_paths = sorted(workflow_dir.glob("*.md"))
    if not workflow_paths:
        print(f"[FAIL] No workflow files found under {workflow_dir}")
        return 1

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
        disable_model_invocation = claude_meta.get("disable-model-invocation")
        claude_model = claude_meta.get("model")
        # context/agent are Claude Code skill-only fields (isolated forked-
        # subagent execution); not propagated to the Codex skill render --
        # no Codex analog is documented.
        claude_context = claude_meta.get("context")
        claude_agent = claude_meta.get("agent")
        codex_meta = frontmatter.get("codex", {})
        if not isinstance(codex_meta, dict):
            codex_meta = {}
        codex_interface = codex_meta.get("interface", {})
        if not isinstance(codex_interface, dict):
            codex_interface = {}
        codex_metadata = codex_meta.get("metadata", {})
        if not isinstance(codex_metadata, dict):
            codex_metadata = {}
        codex_short_description = codex_metadata.get("short-description")
        codex_policy = codex_meta.get("policy", {})
        if not isinstance(codex_policy, dict):
            codex_policy = {}
        codex_allow_implicit_invocation = codex_policy.get("allow_implicit_invocation")

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
                disable_model_invocation=disable_model_invocation,
                model=claude_model,
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
                disable_model_invocation=disable_model_invocation,
                model=claude_model,
                context=claude_context,
                agent=claude_agent,
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
            claude_skill_path = install_root / CLAUDE_SKILLS_REL / name / "SKILL.md"
            claude_skill_content = render_skill_wrapper(
                name=name,
                description=description,
                workflow_rel=workflow_rel,
                disable_model_invocation=disable_model_invocation,
                model=claude_model,
                context=claude_context,
                agent=claude_agent,
            )
            if "claude" in generation_targets:
                write_text(claude_skill_path, claude_skill_content, args.dry_run)
                write_count += 1
            if manifest_scoped_write:
                item_outputs.append(
                    {
                        "path": claude_skill_path.relative_to(repo_root).as_posix(),
                        "kind": "claude_skill",
                        "sha256_12": sha12(claude_skill_content),
                    }
                )

        if "codex" in manifest_targets:
            codex_skill_content = render_skill_wrapper(
                name=name,
                description=description,
                workflow_rel=workflow_rel,
                codex_short_description=codex_short_description or description,
            )
            # agents/openai.yaml companion: parity with the per-file fallback
            # writer in setup_codex_skills.sh, which also produced this
            # alongside SKILL.md. Carries the interface metadata Codex's
            # IDE/CLI skill listing may read, plus allow_implicit_invocation
            # -- structurally, the field Codex's own documented contract
            # ties the guide's Command/Skill classification to on this
            # surface (live enforcement unverified; no Codex runtime
            # exercised).
            codex_display_name = codex_interface.get("display_name") or name
            codex_short_desc = codex_interface.get("short_description") or description
            codex_openai_yaml_content = render_openai_yaml(
                codex_display_name,
                codex_short_desc,
                allow_implicit_invocation=codex_allow_implicit_invocation,
            )

            codex_primary_path = install_root / CODEX_PRIMARY_SKILLS_REL / name / "SKILL.md"
            codex_primary_yaml_path = codex_primary_path.parent / "agents" / "openai.yaml"
            if "codex" in generation_targets:
                write_text(codex_primary_path, codex_skill_content, args.dry_run)
                write_count += 1
                write_text(codex_primary_yaml_path, codex_openai_yaml_content, args.dry_run)
                write_count += 1
            if manifest_scoped_write:
                item_outputs.append(
                    {
                        "path": codex_primary_path.relative_to(repo_root).as_posix(),
                        "kind": "codex_skill_primary",
                        "sha256_12": sha12(codex_skill_content),
                    }
                )
                item_outputs.append(
                    {
                        "path": codex_primary_yaml_path.relative_to(repo_root).as_posix(),
                        "kind": "codex_skill_primary_openai_yaml",
                        "sha256_12": sha12(codex_openai_yaml_content),
                    }
                )

            if args.codex_compat:
                codex_compat_path = install_root / CODEX_COMPAT_SKILLS_REL / name / "SKILL.md"
                codex_compat_yaml_path = codex_compat_path.parent / "agents" / "openai.yaml"
                if "codex" in generation_targets:
                    write_text(codex_compat_path, codex_skill_content, args.dry_run)
                    write_count += 1
                    write_text(codex_compat_yaml_path, codex_openai_yaml_content, args.dry_run)
                    write_count += 1
                if manifest_scoped_write:
                    item_outputs.append(
                        {
                            "path": codex_compat_path.relative_to(repo_root).as_posix(),
                            "kind": "codex_skill_compat",
                            "sha256_12": sha12(codex_skill_content),
                        }
                    )
                    item_outputs.append(
                        {
                            "path": codex_compat_yaml_path.relative_to(repo_root).as_posix(),
                            "kind": "codex_skill_compat_openai_yaml",
                            "sha256_12": sha12(codex_openai_yaml_content),
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

    # Merge-preserve targets this run did not regenerate: a target-subset
    # run (e.g. the Claude setup scripts' default `--targets plugin
    # claude`) must not silently drop the previous manifest's entries for
    # targets it did not touch -- those output files still exist on disk,
    # untouched, and dropping their manifest record would disarm the
    # drift checker for that surface without regenerating anything.
    preserved_targets: set = set()
    old_manifest_path = repo_root / EXPORT_MANIFEST_PRIMARY_REL
    if manifest_scoped_write and old_manifest_path.exists():
        try:
            old_manifest_text = old_manifest_path.read_text(encoding="utf-8")
            ensure_yaml()
            old_manifest = yaml.safe_load(old_manifest_text) or {}
            old_workflows = {
                item.get("workflow"): item
                for item in old_manifest.get("workflows", [])
                if isinstance(item, dict)
            }
            for item in manifest_items:
                old_item = old_workflows.get(item["workflow"])
                if not isinstance(old_item, dict):
                    continue
                old_outputs = old_item.get("outputs", [])
                if not isinstance(old_outputs, list):
                    continue
                existing_paths = {o.get("path") for o in item["outputs"]}
                for old_output in old_outputs:
                    if not isinstance(old_output, dict):
                        continue
                    kind = old_output.get("kind")
                    target = KIND_TO_TARGET.get(kind)
                    if target is None or target in manifest_targets:
                        # Either an unrecognized kind (do not silently carry
                        # forward something this code cannot classify), or a
                        # target this run regenerated (its fresh entries are
                        # already authoritative, and are already in
                        # item["outputs"] -- do not duplicate).
                        continue
                    if old_output.get("path") in existing_paths:
                        continue
                    item["outputs"].append(old_output)
                    preserved_targets.add(target)
        except (OSError, yaml.YAMLError):  # pragma: no cover -- corrupt/unreadable prior manifest
            pass

    manifest_output_count = sum(len(item.get("outputs", [])) for item in manifest_items)
    manifest = {
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
        "targets": sorted(manifest_targets | preserved_targets),
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
    if manifest_scoped_write:
        write_text(manifest_path, manifest_content, args.dry_run)
    # else: an --install-root run targeting outside the repo (a workspace-
    # scope install) never writes the repo's tracked manifest -- doing so
    # would overwrite it with a partial view scoped to whatever --targets
    # this particular install happened to pass, corrupting drift checks
    # for the real repo-scope generation.

    if args.print_manifest:
        print("---MANIFEST-BEGIN---")
        print(manifest_content, end="")
        print("---MANIFEST-END---")

    print("[OK] Workflow export generation complete.")
    print(f"Scope: {args.scope} (pointer basis: {workflow_rel})")
    print(f"Install root: {install_root}")
    print(f"Manifest targets: {sorted(manifest_targets)}")
    print(f"Generation targets: {sorted(generation_targets)}")
    print(f"Workflows processed: {len(workflow_paths)}")
    print(f"Outputs generated: {write_count}")
    if manifest_scoped_write:
        print(f"Manifest: {manifest_path.relative_to(repo_root)} (updated)")
    else:
        print(f"Manifest: {manifest_path.relative_to(repo_root)} (NOT touched -- external install root)")
    if args.dry_run:
        print("Dry run: no files written.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
