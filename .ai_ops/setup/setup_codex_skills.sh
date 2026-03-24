#!/bin/sh
# Setup script for Codex skill installation.
# Installs generated wrappers from tracked ai_ops workflow sources.
# Runtime skill folders are downstream install surfaces, not source-of-truth.

set -e

print_usage() {
  cat <<EOF
Usage:
  ./.ai_ops/setup/setup_codex_skills.sh [--workspace|--repo|--user] [--compat] [-f|--force] [--dry-run]

Options:
  -w, --workspace        Install to workspace root .agents/skills/ (cross-repo access)
      --repo             Install to ai_ops repo .agents/skills/ (default)
      --user             Install to \$HOME/.agents/skills/
      --compat           Also install compatibility mirror to .codex/skills
  -f, --force            Overwrite existing skill wrappers
  -n, --dry-run          Preview actions without writing files
  -h, --help             Show this help

Examples:
  Workspace install (recommended): ./.ai_ops/setup/setup_codex_skills.sh --workspace --force
  Repo install (default):          ./.ai_ops/setup/setup_codex_skills.sh
  User install:                    ./.ai_ops/setup/setup_codex_skills.sh --user
  Include compat mirror:           ./.ai_ops/setup/setup_codex_skills.sh --compat
  Overwrite existing:              ./.ai_ops/setup/setup_codex_skills.sh --repo --force
  Preview only:                    ./.ai_ops/setup/setup_codex_skills.sh --dry-run

Managed-skill rule:
  Define retained ai_ops behavior in tracked repo sources first, then rerun
  /ai_ops_setup or this script. Do not hand-maintain installed .agents/skills/
  as the source-of-truth.
EOF
}

scope="repo"
force="0"
install_compat="0"
dry_run="0"

while [ $# -gt 0 ]; do
  case "$1" in
    -w|--workspace) scope="workspace" ;;
    --repo)         scope="repo" ;;
    --user)         scope="user" ;;
    --compat)       install_compat="1" ;;
    -f|--force)     force="1" ;;
    -n|--dry-run)   dry_run="1" ;;
    -h|--help)      print_usage; exit 0 ;;
    *)
      echo "Unknown option: $1"
      print_usage
      exit 1
      ;;
  esac
  shift
done

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
REPO_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)"
WORKFLOW_DIR="$REPO_ROOT/.ai_ops/workflows"

# Resolve install target and workflow relative path based on scope
if [ "$scope" = "workspace" ]; then
  WORKSPACE_ROOT="$(CDPATH= cd -- "$REPO_ROOT/.." && pwd)"
  PRIMARY_SKILLS_DIR="$WORKSPACE_ROOT/.agents/skills"
  COMPAT_SKILLS_DIR="$WORKSPACE_ROOT/.codex/skills"
  WORKFLOW_REL="ai_ops/.ai_ops/workflows"
elif [ "$scope" = "user" ]; then
  if [ -z "$HOME" ]; then
    echo "HOME is not set; cannot install user-scoped skills."
    exit 1
  fi
  PRIMARY_SKILLS_DIR="$HOME/.agents/skills"
  COMPAT_SKILLS_DIR="$HOME/.codex/skills"
  WORKFLOW_REL=".ai_ops/workflows"
else
  PRIMARY_SKILLS_DIR="$REPO_ROOT/.agents/skills"
  COMPAT_SKILLS_DIR="$REPO_ROOT/.codex/skills"
  WORKFLOW_REL=".ai_ops/workflows"
fi

if [ ! -d "$WORKFLOW_DIR" ]; then
  echo "Missing workflow source directory."
  echo "Expected: $WORKFLOW_DIR"
  exit 1
fi

if ! ls "$WORKFLOW_DIR"/*.md >/dev/null 2>&1; then
  echo "No workflow markdown files found in $WORKFLOW_DIR."
  exit 1
fi

echo "Setting up ai_ops skills..."
echo "Scope:           $scope"
echo "Workflow source: $WORKFLOW_DIR"
echo "Install target:  $PRIMARY_SKILLS_DIR"
echo "Managed-skill rule: tracked repo sources are authoritative; installed runtime wrappers are downstream outputs."
if [ "$dry_run" = "1" ]; then
  echo "Dry-run mode enabled (no files will be written)."
fi

install_into_dir() {
  target_root="$1"
  if [ "$dry_run" = "1" ]; then
    echo "[dry-run] Would target install root: $target_root"
  else
    mkdir -p "$target_root"
  fi

  for file in "$WORKFLOW_DIR"/*.md; do
    name=$(basename "$file" .md)
    skill_name="$name"
    target_dir="$target_root/$skill_name"

    if [ -e "$target_dir/SKILL.md" ] && [ "$force" != "1" ]; then
      echo "Skip existing: $target_dir"
      continue
    fi

    # Extract description from workflow frontmatter (first match only)
    desc=$(grep "^description:" "$file" | head -1 | sed 's/^description:[[:space:]]*//')
    if [ -z "$desc" ]; then
      desc="Run ai_ops workflow $name"
    fi

    if [ "$dry_run" = "1" ]; then
      echo "[dry-run] Would create: $target_dir/SKILL.md"
      echo "[dry-run] Would create: $target_dir/agents/openai.yaml"
      continue
    fi

    mkdir -p "$target_dir"
    cat > "$target_dir/SKILL.md" <<EOF
---
name: $skill_name
description: $desc
metadata:
  short-description: $desc
---

# $skill_name

Read \`$WORKFLOW_REL/$name.md\` and follow its instructions.
EOF

    mkdir -p "$target_dir/agents"
    cat > "$target_dir/agents/openai.yaml" <<EOF
interface:
  display_name: "$skill_name"
  short_description: "$desc"
EOF
    echo "Installed: $target_dir"
  done
}

run_codex_export_generator() {
  if [ ! -f "$REPO_ROOT/00_Admin/scripts/generate_workflow_exports.py" ]; then
    return 1
  fi

  py_cmd=""
  if command -v python >/dev/null 2>&1; then
    py_cmd="python"
  elif command -v python3 >/dev/null 2>&1; then
    py_cmd="python3"
  else
    return 1
  fi

  if [ "$install_compat" = "1" ]; then
    if [ "$dry_run" = "1" ]; then
      "$py_cmd" "$REPO_ROOT/00_Admin/scripts/generate_workflow_exports.py" --targets plugin claude codex --codex-compat --dry-run
    else
      "$py_cmd" "$REPO_ROOT/00_Admin/scripts/generate_workflow_exports.py" --targets plugin claude codex --codex-compat
    fi
  else
    if [ "$dry_run" = "1" ]; then
      "$py_cmd" "$REPO_ROOT/00_Admin/scripts/generate_workflow_exports.py" --targets plugin claude codex --dry-run
    else
      "$py_cmd" "$REPO_ROOT/00_Admin/scripts/generate_workflow_exports.py" --targets plugin claude codex
    fi
  fi
}

# Create .ai_ops/local/work_state.yaml if it doesn't already exist (idempotent)
LOCAL_DIR="$REPO_ROOT/.ai_ops/local"
WORK_STATE_FILE="$LOCAL_DIR/work_state.yaml"
if [ "$dry_run" = "1" ]; then
  if [ ! -f "$WORK_STATE_FILE" ]; then
    echo "[dry-run] Would create: $WORK_STATE_FILE"
  fi
else
  if [ ! -f "$WORK_STATE_FILE" ]; then
    mkdir -p "$LOCAL_DIR"
    cat > "$WORK_STATE_FILE" << 'WSEOF'
# ai_ops work state — machine-local, gitignored.
# Written by /work and /closeout. Never commit.
schema_version: "1.0.0"
work_context:
  active_artifacts: []
  updated_at: null
  checkpoints: []
telemetry:
  last_bootstrap_mode: null
  last_context_refresh: null
WSEOF
    echo "Created .ai_ops/local/work_state.yaml (empty initial state)."
  fi
fi

# Workspace scope bypasses the generator (generator resolves to repo scope only).
if [ "$scope" != "workspace" ] && [ "$force" = "1" ] && run_codex_export_generator; then
  echo "Generated Codex wrappers via generate_workflow_exports.py."
  echo "Primary install target: $PRIMARY_SKILLS_DIR"
  if [ "$install_compat" = "1" ]; then
    echo "Compatibility install target: $COMPAT_SKILLS_DIR"
  else
    echo "Compatibility install skipped (on-demand). Use --compat to enable."
  fi
  echo ""
  echo "Usage quick reference:"
  echo "  Workspace install (recommended): ./.ai_ops/setup/setup_codex_skills.sh --workspace --force"
  echo "  Repo install (default):          ./.ai_ops/setup/setup_codex_skills.sh"
  echo "  User install:                    ./.ai_ops/setup/setup_codex_skills.sh --user"
  echo "  Include compat mirror:           ./.ai_ops/setup/setup_codex_skills.sh --compat"
  echo "  Overwrite existing:              ./.ai_ops/setup/setup_codex_skills.sh --repo --force"
  echo "  Preview only:                    ./.ai_ops/setup/setup_codex_skills.sh --dry-run"
  echo ""
  echo "In Codex VS Code chat, type '\$' to browse skills or run '/skills'."
  exit 0
fi

install_into_dir "$PRIMARY_SKILLS_DIR"
echo "Primary install target: $PRIMARY_SKILLS_DIR"

if [ "$install_compat" = "1" ]; then
  install_into_dir "$COMPAT_SKILLS_DIR"
  echo "Compatibility install target: $COMPAT_SKILLS_DIR"
else
  echo "Compatibility install skipped (on-demand). Use --compat to enable."
fi

echo ""
echo "Usage quick reference:"
echo "  Workspace install (recommended): ./.ai_ops/setup/setup_codex_skills.sh --workspace --force"
echo "  Repo install (default):          ./.ai_ops/setup/setup_codex_skills.sh"
echo "  User install:                    ./.ai_ops/setup/setup_codex_skills.sh --user"
echo "  Include compat mirror:           ./.ai_ops/setup/setup_codex_skills.sh --compat"
echo "  Overwrite existing:              ./.ai_ops/setup/setup_codex_skills.sh --repo --force"
echo "  Preview only:                    ./.ai_ops/setup/setup_codex_skills.sh --dry-run"
echo ""
echo "In Codex VS Code chat, type '\$' to browse skills or run '/skills'."
