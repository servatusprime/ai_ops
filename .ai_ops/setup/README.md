---
title: AI Assistant Setup
version: 0.7.3
status: active
created: 2026-01-25
updated: 2026-03-19
owner: ai_ops
---

<!-- markdownlint-disable MD013 -->
<!-- markdownlint-disable-next-line MD025 -->
# AI Assistant Setup

## Purpose

Instructions for using ai_ops commands with various AI tools.

## How ai_ops Commands Work

ai_ops commands are defined in `.ai_ops/workflows/*.md` files. When
installed into tool-specific skill/command folders, they appear as slash commands
(where supported). Without install, you can invoke them by telling the agent:

- "run /health" or "execute /health"
- "follow the /closeout workflow"
- "read .ai_ops/workflows/health.md and follow it"

The agent reads the workflow file and follows its instructions.

Retained governance stays upstream in tracked repo sources such as
`.ai_ops/workflows/*.md`, approved setup docs, and approved export lanes.
Tool-specific folders such as `.agents/skills/` and `.claude/skills/` are
downstream install surfaces only. If a retained skill or command needs to
change, update the upstream source and rerun `/ai_ops_setup` rather than
hand-maintaining the installed runtime copy.

## Using Commands with Any AI Tool

### Method 1: Natural Language (Recommended)

Simply tell the agent what you want:

```text
User: "run /health"
Agent: [Reads .ai_ops/workflows/health.md and follows instructions]
```

### Method 2: Explicit File Reference

If the agent doesn't recognize the command:

```text
User: "read .ai_ops/workflows/health.md and follow those instructions"
```

## Modality Confirmation (Required)

Before running any setup script, confirm:

| Field | Values | Default |
| --- | --- | --- |
| `active_surface` | `codex_cli` \| `claude_code` \| `claude_app` \| `github_copilot` \| `cursor` \| `gemini_cli` \| `other` | (ask) |
| `installation_target` | `skills` \| `commands` \| `both` \| `none` | `none` |
| `governed_validation_policy` | `ai_ops` \| `repo_native` | `ai_ops` |

**Default is no-install.** Setup scripts only run after explicit confirmation of
`installation_target`. This prevents accidental file creation in tool-specific folders.

If you want to use ai_ops commands without installing them, set `installation_target: none`
and invoke commands via natural language (Method 1 above).

For new governed repos, start `aiops.yaml` from:
`01_Resources/templates/documents/aiops_manifest_template.yaml`.

## Directory Naming Contract

- `.ai_ops/` is repository source-of-truth for workflow contracts and setup scripts.
- `.agents/` is the Codex runtime install target for generated skills.
- `.codex/` is an optional Codex compatibility mirror, generated only on demand.
- Tool-native install folders are downstream wrapper destinations only. Do not
  treat them as the retained authoring surface for ai_ops behavior.

## Choose Install Scope

### Option A: Workspace-level install (recommended)

- Commands are available across repos inside the workspace.
- Use when ai_ops is your shared ops stack serving multiple repos.
- Skill pointers use workspace-root-relative paths: `ai_ops/.ai_ops/workflows/<name>.md`
- Install target: `<workspace_root>/.claude/skills/` and `<workspace_root>/.agents/skills/`
  (`.claude/skills/` is also a Copilot-supported project-skill location on compatible surfaces)
- Flag: `--workspace` (or `-w`)

```bat
.ai_ops\setup\setup_claude_skills.bat --workspace --force
.ai_ops\setup\setup_codex_skills.bat  --workspace --force
```

### Option B: Per-repo install

- Commands are available only within the `ai_ops` repo directory.
- Use when you want ai_ops to be opt-in per project.
- Skill pointers use repo-root-relative paths: `.ai_ops/workflows/<name>.md`
- Install target: `<repo_root>/.claude/skills/` and `<repo_root>/.agents/skills/`
  (`.claude/skills/` is also a Copilot-supported project-skill location on compatible surfaces)
  (optional for repo-local testing; repo-root `.claude/` is not required by
  export drift checks when manifest targets are plugin-only)
- Flag: `--repo` (default)

## Pre-Write Verification (Maintainer Lane)

When setup/export plumbing is modified, run setup scripts in dry-run mode before
write-mode execution. This lane is for maintainers validating changes, not a
mandatory step for every user setup run.

- Claude skills:
  - `./.ai_ops/setup/setup_claude_skills.sh --dry-run`
  - `.ai_ops\\setup\\setup_claude_skills.bat --dry-run`
- Codex skills:
  - `./.ai_ops/setup/setup_codex_skills.sh --dry-run`
  - `.ai_ops\\setup\\setup_codex_skills.bat --dry-run`

If a shell surface is unavailable on the current host (for example bash on a
Windows-only environment), record the blocked lane and run the same script lane
on the available shell (help + dry-run) so behavior coverage is still explicit.

## Tool-Specific Notes

### Claude Code

Claude Code can read workflow files directly. Say "run /health" or reference
the workflow file explicitly.

**Recommended: Skills-based install**:

- `setup_claude_skills.sh` (Unix/macOS)
- `setup_claude_skills.bat` (Windows)

These create wrapper skills in `.claude/skills/<name>/SKILL.md`. Skills are the
canonical mechanism for Claude Code since v2.1.3 when commands were merged into
the skills system.
These scripts may also ensure `plugins/ai-ops-governance/` skeleton directories
exist for plugin-managed wrapper assets. This is a no-op when the directories
already exist.

**Legacy: Commands-based install** (backward-compatible):

- `setup_claude.sh` (Unix/macOS)
- `setup_claude.bat` (Windows)

These copy workflow files into `.claude/commands/`. This path still works but
skills are preferred for new installations.

### Claude App (web + desktop)

Claude app surfaces do not scan project skill or command folders. Use natural
language or an explicit workflow-file reference, for example:

- "run /crosscheck"
- "read `.ai_ops/workflows/crosscheck.md` and follow it"

For `claude_app`, set `installation_target: none`. There is no install-script
lane for this surface. Use it as an instructions-only lane with Filesystem MCP
when repo access is needed.

Treat `claude_app` as an artifact-driven surface, not a runtime-discovery
surface. The workbook/runbook carries the execution topology and delegation
contract; `claude_app` should not be assumed to provide installed skill
discovery, plugin-profile routing, or runtime-enforced delegation guardrails.

#### Claude App Capability Matrix

| Workflow shape | `claude_app` fit | Operator note |
| --- | --- | --- |
| Read-only review, planning, or artifact interpretation | Good fit | Use direct workflow reference plus the target artifact/file set. |
| Artifact-driven single-agent execution with a bounded workbook/runbook | Limited fit | Keep the task brief, context pack, and acceptance criteria explicit in the artifact. |
| `/ai_ops_setup` for `claude_app` itself | Limited fit | Use it to confirm modality and instructions-only posture; no install script lane applies. |
| Delegation-heavy or multi-agent execution | Poor fit | Do not assume native subagent routing, installed skill discovery, or runtime-enforced delegation controls. |
| Plugin-dependent or native-agent-export workflows | Poor fit | Prefer Claude Code, plugin surfaces, or later native export lanes when the workflow depends on those capabilities. |

For `claude_app`, the lead agent or operator should package the minimum viable
execution payload explicitly:

- workflow reference
- task brief
- required context pack
- any intended delegation limits or no-delegation rule
- expected return/checkpoint shape

### Codex (CLI + VS Code Extension)

Codex uses the `.agents/skills/` directory for custom skills. There is no
`.codex/commands/` mechanism.

**Setup scripts (skills)**:

- `setup_codex_skills.sh` (Unix/macOS)
- `setup_codex_skills.bat` (Windows)

These install wrapper skills into `.agents/skills/` by default (repo scope) so
both the Codex CLI and VS Code extension can discover them. Use `--user` to
install into `$HOME/.agents/skills/`. Restart your Codex client (human action)
after installing skills so the new wrappers are re-indexed.

Compatibility mirror (`.codex/skills/`) is available on-demand via
`--compat` (repo or user scope), and is not installed by default.
See `00_Admin/runbooks/rb_codex_compat_mirror_01.md` for explicit commands.

If you prototype a local-only Codex skill under `.agents/skills/`, treat that
runtime artifact as evidence only until the retained behavior is modeled in
tracked repo sources and surfaced through `/ai_ops_setup`.

Legacy `setup_codex.sh` / `setup_codex.bat` scripts were removed because they
targeted `.codex/commands/`, which is not a valid Codex mechanism. Use
`setup_codex_skills.*` only.

### Cursor

Cursor supports custom slash commands via `.cursor/commands/*.md` (since v1.6).
You can also reference workflow files in chat or use @ to include them in context.

> **Note:** Cursor also has a separate `.cursor/rules/` mechanism for always-on
> project rules/constraints. Commands and rules serve different purposes.

**Setup scripts**:

- `setup_cursor.sh` (Unix/macOS)
- `setup_cursor.bat` (Windows)

These copy workflow files into `.cursor/commands/`.

### Gemini CLI

**Setup scripts**:

- `setup_gemini.sh` (Unix/macOS)
- `setup_gemini.bat` (Windows)

These create `.toml` command files in `.gemini/commands/` that reference
the workflow files. Supports project-scoped (`.gemini/commands/`) and
user-scoped (`~/.gemini/commands/`) locations.

Gemini setup scripts also create lightweight markdown wrappers in
`.agents/workflows/` (workspace-root if `../.agents/` exists, otherwise
repo-local `.agents/workflows/`) so Antigravity-style discovery lanes that scan
`.agents/workflows/*.md` can surface the same commands.

TOML in this lane is wrapper transport only. Profile value editing remains
YAML-based through `/profiles` (`.ai_ops/profiles/active_crew.yaml`) for all
surfaces, including Claude and Codex.

### GitHub Copilot Chat

Reference workflow files in Copilot Chat or include them via workspace context.
Copilot reads `.github/copilot-instructions.md` for repo-level custom
instructions. Supported Copilot surfaces can also load project skills from
`.github/skills/` or `.claude/skills/`.

ai_ops does not currently ship a dedicated `setup_copilot_*` script because the
existing `setup_claude_skills.*` lane already generates compatible `SKILL.md`
wrappers in `.claude/skills/`. If you prefer a no-install path, instructions-only
use still works.

### Antigravity

Antigravity natively detects `.ai_ops/workflows/*.md` files as slash commands.
No install script is required for native `.ai_ops/workflows/` detection.
If your Antigravity environment is configured to scan `.agents/workflows/`
instead, run `setup_gemini.sh` / `setup_gemini.bat` to generate wrappers there.
See `setup_antigravity.md` for details.

### Aider / Cline

Include workflow files in context using their respective mechanisms.

## Available Commands

| Command | Workflow File | Purpose |
| --- | --- | --- |
| /work | work.md | Start/resume work session |
| /work_status | work_status.md | Show active context and blockers |
| /work_savepoint | work_savepoint.md | Commit + push savepoint, then end session |
| /harvest | harvest.md | Consolidate/prune artifacts |
| /crosscheck | crosscheck.md | Conduct structured peer review |
| /health | health.md | Repo health check |
| /closeout | closeout.md | Lint/commit/push with cleanup |
| /lint | lint.md | Run configured validators/linters |
| /bootstrap | bootstrap.md | Initialize agent context |
| /scratchpad | scratchpad.md | Create scratchpad |
| /customize | customize.md | Configure preferences |
| /profiles | profiles.md | Manage rider/crew behavior contracts |

All workflow files are in `.ai_ops/workflows/`.

## Direct Support Targets

| Tool | Mechanism | Folder/File | Status |
| --- | --- | --- | --- |
| Claude Code (skills) | Skills | `.claude/skills/` | Recommended (workspace-root) |
| Claude Code (commands) | Commands | `.claude/commands/` | Legacy (backward-compatible) |
| Claude App (web/desktop) | Direct workflow reference | none | Supported (instructions-only; no install; artifact-driven) |
| Codex (skills, repo scope) | Skills | `.agents/skills/` | Recommended |
| Codex (skills, user scope) | Skills | `$HOME/.agents/skills/` | Recommended |
| Cursor | Commands | `.cursor/commands/` | Setup scripts |
| Gemini CLI | Commands | `.gemini/commands/` | Setup scripts |
| Gemini/Antigravity compatibility | Wrappers | `.agents/workflows/` | Generated by Gemini setup scripts |
| Antigravity | Native | `.ai_ops/workflows/` | No install needed |
| GitHub Copilot | Instructions + Skills | `.github/copilot-instructions.md`, `.claude/skills/` (via `setup_claude_skills.*`), `.github/skills/` (manual/optional) | Supported on compatible surfaces |

## Notes

- These files are authoritative for command setup.
- Command behavior differs based on mode: Direct (working on ai_ops itself),
  Governed (external repo using ai_ops governance), or Standalone.
- See `00_Admin/guides/ai_operations/guide_command_workflows.md` for detailed behavior differences.
- Install scripts prompt before copying if target folders already contain files.
- Existing command files are skipped by default (non-destructive).
- Overwrite requires explicit user confirmation.
- Surface-specific profile adapter behavior (Codex, Claude, Gemini) is defined
  in `.ai_ops/workflows/profiles.md`, not in setup docs.
- For deterministic wrapper regeneration from SoT workflows, run:
  `python 00_Admin/scripts/generate_workflow_exports.py`.
- Model availability is not reliably auto-detected by setup scripts; declare
  available models/default reasoning via `/customize`, then use `/profiles` for
  model-family behavior tuning when needed.

## Setup Smoke Matrix

The setup smoke matrix is maintained in runbook
`00_Admin/runbooks/rb_setup_smoke_matrix_01.md`.

## Canonical Release-Quality Gate

Run one command path to execute validator, export drift, lint, and profile
regeneration dry-run checks:

`python 00_Admin/scripts/run_release_quality_gate.py`

Use `--dry-run` to preview commands without executing:

`python 00_Admin/scripts/run_release_quality_gate.py --dry-run`

## Adapter Format Versioning

When setup wrapper format changes (SKILL.md schema, command wrapper structure,
or compatibility path strategy), update this README metadata (`version` and
`updated`) in the same patch and note impacted scripts in the change summary.
