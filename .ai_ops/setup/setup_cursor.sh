#!/bin/sh
# Setup script for Cursor command installation.
# This copies workflow files into .cursor/commands.

set -e

echo "Setting up ai_ops for Cursor..."

mkdir -p .cursor/commands

if [ -n "$(ls -A .cursor/commands 2>/dev/null)" ]; then
  printf "Found existing files in .cursor/commands/. Continue and copy new files? (y/N): "
  read -r response
  case "$response" in
    y|Y) ;;
    *) echo "Cancelled."; exit 0 ;;
  esac
fi

if [ -d ".ai_ops/workflows" ]; then
  WORKFLOW_DIR=".ai_ops/workflows"
else
  echo "Missing workflow source directory."
  echo "Expected: .ai_ops/workflows"
  exit 1
fi

for file in "$WORKFLOW_DIR"/*.md; do
  filename=$(basename "$file")
  target=".cursor/commands/$filename"
  if [ -e "$target" ]; then
    echo "Skip existing: $target"
    continue
  fi
  cp "$file" "$target"
done

# Create .ai_ops/local/work_state.yaml if it doesn't already exist (idempotent)
LOCAL_DIR=".ai_ops/local"
WORK_STATE_FILE="$LOCAL_DIR/work_state.yaml"
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

echo "Copied workflows to .cursor/commands/."

