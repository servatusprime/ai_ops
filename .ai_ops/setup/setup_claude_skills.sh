#!/bin/sh
# Setup script for Claude Code skills.
# Also generates GitHub Copilot-compatible project skills in .claude/skills on
# supported Copilot surfaces.

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

echo "Setting up ai_ops skills in .claude/skills..."
echo "Compatible surfaces: Claude Code, and GitHub Copilot where .claude/skills is supported."
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

# Both scopes route through the real generator; --install-root lets
# workspace scope use the same full-field renderer as repo scope. The
# generator-unavailable states fail closed; no alternate writer is permitted.
run_export_generator() {
  if [ ! -f "$REPO_ROOT/00_Admin/scripts/generate_workflow_exports.py" ]; then
    return 127
  fi

  py_cmd=""
  if command -v python >/dev/null 2>&1; then
    py_cmd="python"
  elif command -v python3 >/dev/null 2>&1; then
    py_cmd="python3"
  else
    return 127
  fi

  generator_attempted="1"

  if [ "$scope" = "workspace" ]; then
    if [ "$dry_run" = "1" ]; then
      "$py_cmd" "$REPO_ROOT/00_Admin/scripts/generate_workflow_exports.py" \
        --targets claude --scope workspace --install-root "$WORKSPACE_ROOT" --dry-run
    else
      "$py_cmd" "$REPO_ROOT/00_Admin/scripts/generate_workflow_exports.py" \
        --targets claude --scope workspace --install-root "$WORKSPACE_ROOT"
    fi
  else
    if [ "$dry_run" = "1" ]; then
      "$py_cmd" "$REPO_ROOT/00_Admin/scripts/generate_workflow_exports.py" --targets plugin claude --dry-run
    else
      "$py_cmd" "$REPO_ROOT/00_Admin/scripts/generate_workflow_exports.py" --targets plugin claude
    fi
  fi
}

generator_attempted="0"
if run_export_generator; then
  echo ""
  echo "Generated wrapper exports from .ai_ops/workflows via generate_workflow_exports.py."
  echo "Installed skills to $INSTALL_TARGET/."
  echo "Skills are now available as /work, /health, /closeout, etc."
  echo ""
  exit 0
else
  generator_status=$?
  if [ "$generator_attempted" = "1" ] || [ "$generator_status" -ne 127 ]; then
    echo "Generator refused the setup request (exit $generator_status); no fallback writes will be attempted."
    exit "$generator_status"
  fi
fi

echo "Generator unavailable; refusing fallback writes because the generated export is the authoritative source." >&2
exit 127
