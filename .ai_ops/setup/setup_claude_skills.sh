#!/bin/sh
# Setup script for Claude Code skill installation.
# Creates shallow wrapper skills in .claude/skills that point to workflow sources.

set -e

print_usage() {
  cat <<EOF
Usage:
  ./.ai_ops/setup/setup_claude_skills.sh [--workspace|--repo] [--force] [--dry-run] [--yes]

Options:
  -w, --workspace        Install to workspace root .claude/skills/ (cross-repo access)
      --repo             Install to ai_ops repo .claude/skills/ (default)
  -f, --force            Overwrite existing skill wrappers
  -n, --dry-run          Preview actions without writing files
  -y, --yes              Non-interactive mode; skip confirmation prompt
  -h, --help             Show this help

Examples:
  Workspace install (recommended): ./.ai_ops/setup/setup_claude_skills.sh --workspace --force
  Repo install (default):          ./.ai_ops/setup/setup_claude_skills.sh
  Preview only:                    ./.ai_ops/setup/setup_claude_skills.sh --dry-run
EOF
}

scope="repo"
dry_run="0"
assume_yes="0"
force="0"

while [ $# -gt 0 ]; do
  case "$1" in
    -w|--workspace) scope="workspace" ;;
    --repo)         scope="repo" ;;
    -n|--dry-run)   dry_run="1" ;;
    -y|--yes)       assume_yes="1" ;;
    -f|--force)     force="1" ;;
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

# Resolve install target and workflow relative path based on scope
if [ "$scope" = "workspace" ]; then
  WORKSPACE_ROOT="$(CDPATH= cd -- "$REPO_ROOT/.." && pwd)"
  INSTALL_TARGET="$WORKSPACE_ROOT/.claude/skills"
  WORKFLOW_REL="ai_ops/.ai_ops/workflows"
else
  INSTALL_TARGET="$REPO_ROOT/.claude/skills"
  WORKFLOW_REL=".ai_ops/workflows"
fi

WORKFLOW_DIR="$REPO_ROOT/.ai_ops/workflows"

echo "Setting up ai_ops skills for Claude Code..."
echo "Scope:           $scope"
echo "Workflow source: $WORKFLOW_DIR"
echo "Install target:  $INSTALL_TARGET"
if [ "$dry_run" = "1" ]; then
  echo "Dry-run mode enabled (no files will be written)."
fi

if [ ! -d "$WORKFLOW_DIR" ]; then
  echo "Missing workflow source directory."
  echo "Expected: $WORKFLOW_DIR"
  exit 1
fi

if [ "$dry_run" != "1" ]; then
  mkdir -p "$INSTALL_TARGET"
fi

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

if [ -n "$(ls -A "$INSTALL_TARGET" 2>/dev/null)" ] && [ "$assume_yes" != "1" ] && [ "$force" != "1" ]; then
  if [ "$dry_run" = "1" ]; then
    echo "Would prompt: existing skills found in $INSTALL_TARGET/."
  else
    printf "Found existing skills in %s/. Continue and add/update ai_ops skills? (y/N): " "$INSTALL_TARGET"
    read -r response
    case "$response" in
      y|Y) ;;
      *) echo "Cancelled."; exit 0 ;;
    esac
  fi
fi

# Workspace scope bypasses the generator (generator resolves to repo scope only).
if [ "$scope" != "workspace" ]; then
  run_export_generator() {
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

    if [ "$dry_run" = "1" ]; then
      "$py_cmd" "$REPO_ROOT/00_Admin/scripts/generate_workflow_exports.py" --targets plugin claude --dry-run
    else
      "$py_cmd" "$REPO_ROOT/00_Admin/scripts/generate_workflow_exports.py" --targets plugin claude
    fi
  }

  if run_export_generator; then
    echo ""
    echo "Generated wrapper exports from .ai_ops/workflows via generate_workflow_exports.py."
    echo "Installed skills to $INSTALL_TARGET/."
    echo "Skills are now available as /work, /health, /closeout, etc."
    echo ""
    exit 0
  fi

  echo "Generator unavailable; falling back to legacy wrapper creation path."
fi

for file in "$WORKFLOW_DIR"/*.md; do
  skill_name=$(basename "$file" .md)
  skill_dir="$INSTALL_TARGET/$skill_name"

  if [ -e "$skill_dir/SKILL.md" ] && [ "$force" != "1" ]; then
    echo "Skip existing: $skill_dir"
    continue
  fi

  # Extract description from frontmatter (first match only)
  desc=$(grep "^description:" "$file" | head -1 | sed 's/^description:[[:space:]]*//')
  if [ -z "$desc" ]; then
    desc="Run ai_ops workflow $skill_name"
  fi

  if [ "$dry_run" = "1" ]; then
    echo "Would create: $skill_dir/SKILL.md"
    continue
  fi

  mkdir -p "$skill_dir"
  cat > "$skill_dir/SKILL.md" <<EOF
---
name: $skill_name
description: $desc
---

Read \`$WORKFLOW_REL/$skill_name.md\` and follow its instructions.
EOF
  echo "Created: $skill_dir"
done

echo ""
echo "Installed skills to $INSTALL_TARGET/."
echo "Skills are now available as /work, /health, /closeout, etc."
echo ""
