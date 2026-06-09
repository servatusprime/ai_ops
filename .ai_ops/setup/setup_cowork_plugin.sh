#!/bin/sh
# setup_cowork_plugin.sh
# Package ai_ops skills into a Cowork .plugin file.
#
# Usage:
#   ./setup_cowork_plugin.sh [--workspace | --repo] [--output <path>] [--dry-run] [--help]
#
# Options:
#   --workspace   Package skills from <workspace_root>/.claude/skills/  (default)
#   --repo        Package skills from <repo_root>/.claude/skills/
#   --output      Output path for .plugin file (default: <workspace_root>/ai-ops-skills.plugin)
#   --dry-run     Print resolved paths and skill count; do not write output file
#   --help        Show this help
#
# Exit codes:
#   0  Success (or dry-run complete)
#   1  Error (zero skills found, manifest missing, Python unavailable)
#
# Manifest source: <repo_root>/.claude-plugin/plugin.json (tracked)

set -e

print_usage() {
  cat <<EOF
Usage:
  ./setup_cowork_plugin.sh [--workspace|--repo] [--output <path>] [--dry-run] [--help]

Options:
  -w, --workspace   Package skills from <workspace_root>/.claude/skills/  (default)
      --repo        Package skills from <repo_root>/.claude/skills/
  -o, --output      Output path for .plugin file
                    (default: <workspace_root>/ai-ops-skills.plugin)
  -n, --dry-run     Print resolved paths and skill count; do not write output file
  -h, --help        Show this help

Exit 0 = success, Exit 1 = error
EOF
}

scope="workspace"
dry_run="0"
output_path=""

while [ $# -gt 0 ]; do
  case "$1" in
    -w|--workspace) scope="workspace" ;;
    --repo)         scope="repo" ;;
    -n|--dry-run)   dry_run="1" ;;
    -o|--output)    output_path="$2"; shift ;;
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
WORKSPACE_ROOT="$(CDPATH= cd -- "$REPO_ROOT/.." && pwd)"

# Resolve skills source
if [ "$scope" = "workspace" ]; then
  SKILLS_ROOT="$WORKSPACE_ROOT/.claude/skills"
else
  SKILLS_ROOT="$REPO_ROOT/.claude/skills"
fi

MANIFEST_PATH="$REPO_ROOT/.claude-plugin/plugin.json"

if [ -z "$output_path" ]; then
  output_path="$WORKSPACE_ROOT/ai-ops-skills.plugin"
fi

echo "Workspace root  : $WORKSPACE_ROOT"
echo "Repo root       : $REPO_ROOT"
echo "Scope           : $scope"
echo "Skills root     : $SKILLS_ROOT"
echo "Manifest        : $MANIFEST_PATH"
echo "Output          : $output_path"
if [ "$dry_run" = "1" ]; then
  echo "Dry-run mode: no files will be written."
fi
echo ""

# Check manifest
if [ ! -f "$MANIFEST_PATH" ]; then
  echo "ERROR: Manifest not found: $MANIFEST_PATH"
  echo "Create it at .claude-plugin/plugin.json in the ai_ops repo root."
  exit 1
fi

# Check skills directory
if [ ! -d "$SKILLS_ROOT" ]; then
  echo "ERROR: Skills directory not found: $SKILLS_ROOT"
  exit 1
fi

# Count skills
skill_count=0
for d in "$SKILLS_ROOT"/*/; do
  if [ -f "${d}SKILL.md" ]; then
    skill_count=$((skill_count + 1))
  fi
done

echo "Skills found: $skill_count"

if [ "$skill_count" -eq 0 ]; then
  echo "ERROR: No skill directories containing SKILL.md found in $SKILLS_ROOT"
  exit 1
fi

if [ "$dry_run" = "1" ]; then
  echo "[dry-run] Would create plugin file at: $output_path"
  exit 0
fi

# Locate Python
PY=""
if command -v python >/dev/null 2>&1; then
  PY="python"
elif command -v python3 >/dev/null 2>&1; then
  PY="python3"
fi

if [ -z "$PY" ]; then
  echo "ERROR: Python not found. Install Python and retry."
  exit 1
fi

# Package the plugin using Python
"$PY" - "$SKILLS_ROOT" "$MANIFEST_PATH" "$output_path" <<'PYEOF'
import zipfile, json, pathlib, sys

skills_root = pathlib.Path(sys.argv[1])
manifest_path = pathlib.Path(sys.argv[2])
output_path = sys.argv[3]

manifest = json.loads(manifest_path.read_text('utf-8'))
skills = sorted([
    d.name for d in skills_root.iterdir()
    if d.is_dir() and (d / 'SKILL.md').exists()
])

if not skills:
    print('ERROR: No skills found', file=sys.stderr)
    sys.exit(1)

with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    zf.writestr(
        '.claude-plugin/plugin.json',
        json.dumps(manifest, indent=2) + '\n'
    )
    for s in skills:
        zf.write(str(skills_root / s / 'SKILL.md'), f'skills/{s}/SKILL.md')
    readme = (
        f"# {manifest.get('name', 'plugin')} Plugin\n\n"
        f"{manifest.get('description', '')}\n\n"
        f"Skills: {', '.join(skills)}\n"
    )
    zf.writestr('README.md', readme)

print(f"Created: {output_path}")
print(f"  Skills packaged ({len(skills)}): {', '.join(skills)}")
PYEOF
