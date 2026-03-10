#!/bin/sh
# Setup script for Gemini CLI and Antigravity command discovery.
# This creates .toml command files in .gemini/commands and lightweight
# markdown wrappers in .agents/workflows from workflow files.

set -e

echo "Setting up ai_ops for Gemini CLI and Antigravity..."

mkdir -p .gemini/commands

if [ -n "$(ls -A .gemini/commands 2>/dev/null)" ]; then
  printf "Found existing files in .gemini/commands/. Continue and copy new files? (y/N): "
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
WORKFLOW_REL="${WORKFLOW_DIR#./}"

if [ -d "../.agents" ]; then
  AGENTS_ROOT="../.agents"
  WORKFLOW_POINTER_BASE="ai_ops/.ai_ops/workflows"
else
  AGENTS_ROOT=".agents"
  WORKFLOW_POINTER_BASE=".ai_ops/workflows"
fi
AGENTS_WORKFLOW_DIR="$AGENTS_ROOT/workflows"
mkdir -p "$AGENTS_WORKFLOW_DIR"

for file in "$WORKFLOW_DIR"/*.md; do
  filename=$(basename "$file" .md)
  target=".gemini/commands/$filename.toml"
  if [ -e "$target" ]; then
    echo "Skip existing: $target"
    continue
  fi
  cat > "$target" <<EOF
name = "$filename"
description = "ai_ops $filename command"
prompt = "Read $WORKFLOW_REL/$filename.md and follow the instructions."
EOF
  echo "Created $target"

  wrapper_target="$AGENTS_WORKFLOW_DIR/$filename.md"
  if [ -e "$wrapper_target" ]; then
    echo "Skip existing: $wrapper_target"
  else
    cat > "$wrapper_target" <<EOF
---
description: ai_ops $filename command wrapper for Antigravity/Gemini discovery.
---

# /$filename

Read $WORKFLOW_POINTER_BASE/$filename.md and follow the instructions.
EOF
    echo "Created $wrapper_target"
  fi
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
