#!/bin/sh
# Setup script for Claude Code command installation (legacy).
# Copies workflow files into .claude/commands.
#
# NOTE: As of Claude Code v2.1.3, slash commands were merged into the
# skills system. The .claude/commands path still works (backward-compatible)
# but .claude/skills is now the recommended mechanism.
# Prefer setup_claude_skills.sh for new installations.

set -e

echo ""
echo "NOTE: .claude/commands is backward-compatible but skills are now preferred."
echo "      Consider using setup_claude_skills.sh instead."
echo ""

if [ -d ".ai_ops/workflows" ]; then
  WORKFLOW_DIR=".ai_ops/workflows"
else
  echo "Missing workflow source directory; run this from the repo root."
  echo "Expected: .ai_ops/workflows"
  exit 1
fi

mkdir -p .claude/commands

if [ -n "$(ls -A .claude/commands 2>/dev/null)" ]; then
  printf "Found existing files in .claude/commands/. Continue and copy new files? (y/N): "
  read -r response
  case "$response" in
    y|Y) ;;
    *) echo "Cancelled."; exit 0 ;;
  esac
fi

for file in "$WORKFLOW_DIR"/*.md; do
  filename=$(basename "$file")
  target=".claude/commands/$filename"
  if ! head -n 5 "$file" | grep -q "^description:"; then
    echo "Skip missing description frontmatter: $file"
    continue
  fi
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

echo ""
echo "Copied workflows to .claude/commands/."
echo ""
echo "Recommended: use setup_claude_skills.sh for the skills-based approach."
echo "See: https://code.claude.com/docs/en/skills"
echo ""
