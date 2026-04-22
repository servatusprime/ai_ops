---
name: ai_ops_setup
description: Run ai_ops setup scripts for skills, commands, and supported instruction surfaces
kind: workflow
version: 0.1.6
status: active
owner: ai_ops
license: Apache-2.0
claude:
  argument-hint: null
  disable-model-invocation: false
  user-invocable: true
  allowed-tools: null
  model: null
  context: null
  agent: null
codex:
  metadata:
    short-description: Run ai_ops setup scripts for supported skills, commands, and instruction surfaces.
  interface:
    display_name: ai_ops_setup
    short_description: Install or verify ai_ops setup wrappers.
  policy:
    allow_implicit_invocation: true
exports:
  claude_plugin:
    enabled: true
    skill_name: ai_ops_setup
  codex:
    enabled: true
    skill_name: ai_ops_setup
  claude_project:
    enabled: true
    skill_name: ai_ops_setup
---

<!-- markdownlint-disable MD013 MD025 MD041 -->

# /ai_ops_setup

## Purpose

Run the appropriate ai_ops setup scripts for the user's tool(s), or confirm the
instructions-only lane when that is the correct surface behavior.

## Setup Contract (Mandatory)

`/ai_ops_setup` is the only lane that writes setup completion receipts.

- Required contract version is read from `00_Admin/configs/setup_contract.yaml` `required_version`.
- Local receipt path is read from `00_Admin/configs/setup_contract.yaml` `receipt_path` (default: `.ai_ops/local/setup/state.yaml`).
- Local operator state is stored under `.ai_ops/local/**` and must not be committed.
- Retained ai_ops behavior must be governed in tracked repo sources first
  (`.ai_ops/workflows/`, approved setup docs, and approved export lanes).
- Tool runtime folders such as `.agents/skills/`, `.claude/skills/`, and
  `.claude/commands/` are downstream install surfaces, not source-of-truth
  authoring surfaces.
- If a user wants a retained skill/command behavior change, transition to
  `/work` and update upstream sources before reinstalling.
- Compatibility read for legacy local inputs is allowed during migration:
  - `.ai_ops/config.yaml`
  - `.ai_ops/profiles/active_crew.yaml`

## Modality Confirmation (Mandatory)

Before any setup actions, capture explicit confirmation:

| Field | Values | Required |
| --- | --- | --- |
| `active_surface` | `codex_cli` \| `claude_code` \| `claude_app` \| `remote_control` \| `github_copilot` \| `cursor` \| `gemini_cli` \| `other` | Yes |
| `installation_target` | `skills` \| `commands` \| `both` \| `none` | Yes |
| `install_scope` | `workspace` \| `repo` \| `user` | Yes |
| `governed_validation_policy` | `ai_ops` \| `repo_native` | Yes |

**Rules:**

1. Do NOT assume installation target. Default is `none` until user confirms.
2. If user says "just set up" without specifying, ask explicitly.
3. Record confirmation in session context before proceeding.
4. If `installation_target` is `none`, skip all install scripts and confirm no action taken.
5. If `install_scope` is not specified, default to `workspace` and confirm with user.
6. If `governed_validation_policy` is not specified, default to `ai_ops` and confirm with user.
7. If `active_surface` is `claude_app`, `installation_target` must be `none`.
   This is an instructions-only lane with direct workflow references.
8. If `active_surface` is `github_copilot`, `commands` is not a valid ai_ops
   install lane. Use instructions-only (`none`) or project skills (`skills`).
9. If `active_surface` is `github_copilot`, interpret `skills` as project
   skills in `.claude/skills/` via `setup_claude_skills.*`, plus tracked repo
   instructions in `.github/copilot-instructions.md`.
10. If the selected script lane does not support the requested `install_scope`,
   stop and ask for a supported scope before writing anything.
11. If `active_surface` is `remote_control`, treat as `claude_code` for all
    install purposes. `remote_control` is a surface extension -- one local
    Claude Code session reachable from multiple devices (terminal, browser,
    phone). Topology and lane contracts are unchanged from `claude_code`.

**Install scope behavior:**

| Scope | Install Root | Workflow Pointer | Script Flag |
| --- | --- | --- | --- |
| `workspace` | `<workspace_root>/.agents/skills/`, `.claude/skills/`, or surface-native command folders | `ai_ops/.ai_ops/workflows/` | `--workspace` when supported |
| `repo` | `ai_ops/.agents/skills/`, `ai_ops/.claude/skills/`, or repo-local command folders | `.ai_ops/workflows/` | surface default |
| `user` | `$HOME/.agents/skills/` or another surface-native user folder when supported | `ai_ops/.ai_ops/workflows/` | `--user` when supported |

Workspace scope is recommended for multi-repo workspaces where agents run from
workspace root, not repo root.

Current ai_ops support notes:

- Codex skills support `workspace`, `repo`, and `user`.
- Claude skills support `workspace` and `repo`.
- Claude app (`claude.ai` / Claude desktop) is instructions-only: use
  `installation_target: none`; no install script lane applies.
- For `claude_app`, ai_ops should treat topology and delegation as
  artifact-carried operator guidance rather than runtime-enforced behavior:
  do not assume installed skill discovery, plugin-profile routing, or native
  subagent delegation controls on this surface.
- GitHub Copilot skills follow the current Claude skill lane
  (`setup_claude_skills.*`) and therefore support `workspace` and `repo`.
- GitHub Copilot repo instructions (`.github/copilot-instructions.md`) are
  tracked project files, not install-script outputs.

## Workspace Topology

Detect workspace topology before resolving any install paths. All three configs are
supported. Workspace root detection must precede every path and `work_repos` calculation.

| Config | Description | Workspace Root | ai_ops Location | `work_repos` Basis |
| --- | --- | --- | --- | --- |
| **A — ai_ops as workspace root** | ai_ops is the mono-repo workspace root; no parent workspace directory | ai_ops repo root | `.` (same as workspace root) | Not applicable (no external repos in this mode) |
| **B — ai_ops nested in workspace** | ai_ops is one repo inside a larger workspace; other target repos sit alongside it | Parent directory above ai_ops | `<workspace_root>/ai_ops/` | Paths relative to workspace root (e.g. `my_project/`) |
| **C — ai_ops standalone, external workspace** | ai_ops is a standalone repo but the tool's workspace root is a different directory (e.g. IDE opened at a parent folder) | Tool's active workspace root | Absolute or relative path from workspace root to ai_ops | Same as Config B: relative to workspace root |

**Detection procedure:**

1. Ask the user: "Is ai_ops the root of your workspace, or is it nested inside a larger directory?"
   - If unsure, check whether the parent directory of ai_ops contains other repos or is the IDE's opened workspace.
2. Capture `workspace_root`:
   - Config A: `workspace_root` = ai_ops repo root.
   - Config B: `workspace_root` = parent directory above ai_ops.
   - Config C: `workspace_root` = tool's active workspace root (may differ from ai_ops parent).
3. Resolve all install paths relative to `workspace_root`.
4. For `work_repos` entries in `.ai_ops/local/config.yaml`:
   - Config A: no external `work_repos` entries needed (only one repo).
   - Config B/C: paths are relative to `workspace_root`. Example:

     ```yaml
     workspace:
       work_repos:
         - path: ai_ops/         # Config B: ai_ops itself (for direct mode)
           sandbox_dir: 90_Sandbox
           savepoint_validation:
             minimum_commands: []
         - path: my_project/     # Config B: a target repo alongside ai_ops
           sandbox_dir: 90_Sandbox
           savepoint_validation:
             minimum_commands: []
     ```

Local files (`.ai_ops/local/**`) are always relative to the ai_ops repo root regardless of topology.
Only install target paths and `work_repos` shift between configs.

## Inputs

- Target tool(s): Claude, Codex, GitHub Copilot, Cursor, Gemini
- OS: Windows or Mac/Linux
- Workspace topology: Config A (ai_ops = workspace root), Config B (nested), or Config C (standalone)
- Desired installs: skills, commands, or both (must be explicitly confirmed)

## Model Availability Note

`/ai_ops_setup` can reliably confirm runtime surface and install scope, but cannot reliably auto-detect all model
tiers/providers available to a user across vendors and account plans.

Model availability should be treated as user-declared configuration captured via `/customize` (recommended) and
optionally tuned via `/profiles`.

## Context Routing Hook

Use `00_Admin/configs/context_routing.yaml` as the canonical onboarding
contract.

1. Apply `commands._defaults.guard_profile` and
   `commands.ai_ops_setup.guard_profile`.
2. Resolve onboarding tier in order: `fresh_bootstrap`,
   `resume_same_scope`, `recenter` (fallback `fresh_bootstrap` when state is
   unknown).
3. Enforce BRG-01:
   if bootstrap requirements are missing or unverifiable, apply
   `fresh_bootstrap` tier (read `AGENTS.md`) before lane steps.
4. Load `always_read`; expand `read_on_demand` only when needed.
5. Emit route metadata: `bootstrap_path`, `resume_basis`, and `reads_applied`.
6. If requested action requires canonical remediation edits outside setup
   scope, transition to `/work`.

## Steps

1. **Confirm modality** (mandatory gate):
   - Ask: "Which tool are you using?" -> captures `active_surface`
   - Ask: "Install skills, commands, both, or none?" -> captures `installation_target`
   - Ask: "For governed repos, use ai_ops validators/linters or repo-native tooling?" -> captures `governed_validation_policy`
   - If `installation_target` is `none`, stop and confirm no install performed.
2. Detect OS or ask if not detectable.
3. If `AGENTS.md` is missing in the target repo, point the user to the onboarding guide in `HUMANS.md`.
4. If `.ai_ops/local/config.yaml` exists, update `customizations.validation_policy.governed_mode` with the confirmed
   `governed_validation_policy`. If it does not exist, create it from the template and apply the value after
   confirmation.
5. **Configure target/external repos** (governed workflow prerequisite):
   - Ask: "Do you have external repos you want ai_ops to govern (for `/work_savepoint`, `/closeout`, and `/lint` in
     Governed or External mode)?"
   - If yes: for each target repo, add an entry to `workspace.work_repos` in `.ai_ops/local/config.yaml`:
     - `path:` — relative to `workspace_root` (see Workspace Topology section for Config A/B/C).
       Absolute paths are also accepted for repos outside the workspace. At runtime,
       relative paths are joined with the workspace root before comparing to the resolved
       `<target_repo>`; absolute paths are compared directly.
     - `sandbox_dir:` — subdirectory used for work artifacts (default: `90_Sandbox`).
     - `savepoint_validation.minimum_commands:` — validator commands to run before savepoint. Default `[]`; populate
       when repo-native validators are identified via `/customize` or manual edit.
   - Example entry for a target repo alongside ai_ops in the same workspace:

     ```yaml
     workspace:
       work_repos:
         - path: ai_ops/
           sandbox_dir: 90_Sandbox
           savepoint_validation:
             minimum_commands: []
         - path: my_project/
           sandbox_dir: 90_Sandbox
           savepoint_validation:
             minimum_commands: []
     ```

   - If no external repos are known at setup time, skip and add entries manually later,
     or re-invoke `/ai_ops_setup` at any time to add new repos to `work_repos`.
   - If `governed_validation_policy` is `repo_native`, `work_repos` entries are still used for repo-root resolution
     at runtime; `minimum_commands` is ignored (validators are auto-detected from the repo's native tooling).
6. Check existing installation state for the selected surface and scope:
   - If wrappers already exist at the target scope root, report "already installed" and offer `--force` overwrite or
     stop.
7. Run the matching script(s) from `.ai_ops/setup/` with the resolved scope flag:
   - Claude skills: `setup_claude_skills.bat|.sh [--workspace|--repo]`
   - Claude app: no install script; confirm direct workflow-reference lane
     and Filesystem access when repo files are needed
   - Codex skills: `setup_codex_skills.bat|.sh [--workspace|--repo|--user]`
   - GitHub Copilot skills: reuse `setup_claude_skills.bat|.sh [--workspace|--repo]`
     on surfaces that support project skills from `.claude/skills/`
   - GitHub Copilot instructions: no install script; verify
     `.github/copilot-instructions.md` exists and confirm instructions-only lane
   - Commands: `setup_claude.bat|.sh`, `setup_cursor.bat|.sh`, `setup_gemini.bat|.sh`
   - Echo resolved install root and workflow pointer before executing.
8. For Claude installs, ensure plugin skeleton folders exist:
   - `plugins/ai-ops-governance/agents/`
   - `plugins/ai-ops-governance/commands/`
   - `plugins/ai-ops-governance/.claude-plugin/`
9. For Codex installs, use primary skills path by default:
   - primary: `.agents/skills/` (or `$HOME/.agents/skills/`)
   - compatibility mirror (`.codex/skills/` or `$HOME/.codex/skills/`) is on-demand only when explicitly requested.
10. If retained ai_ops behavior needs to persist, confirm the source edit
    belongs in tracked repo surfaces and not in the installed runtime folder.
11. Report results and note where files were installed.
12. Ensure local setup-state surfaces exist:

- `.ai_ops/local/config.yaml` (when local overrides are created),
- `.ai_ops/local/profiles/active_crew.yaml` (when profile state exists),
- `.ai_ops/local/setup/state.yaml` (setup receipt).

1. Write/update setup receipt with:

- required setup contract version,
- installed surface summary,
- timestamp.

1. Report whether setup-gated lanes are now ready:

- `/work`
- `/customize`
- `/profiles`

1. Recommend post-setup model declaration:

- "Run `/customize` to declare available models and default reasoning tier in `.ai_ops/local/config.yaml`."
- "Run `/profiles` if you want behavior tuning per model family after declaration."

2. Recommend hooks configuration (structural governance enforcement):

- "Copy the hooks template from `01_Resources/templates/config/hooks_template.json`
  into `.claude/settings.local.json` at your workspace root. Hooks provide
  structural (non-LLM) enforcement of governance rules: PostToolUse markdown lint,
  PreToolUse Level 4 path guard, and SessionStart context injection."

3. New machine onboarding — global `~/.claude/` configuration:

- "Apply the global settings template from `01_Resources/templates/config/settings_global_template.json`
  to `~/.claude/settings.json`. This replaces accumulated one-off rules with
  category-level permissions and a deny list for sensitive paths."
- "Create `~/.claude/CLAUDE.md` with user preferences (language, shell, commit gate rules)."
- "Note: CLAUDE.md files at workspace root, `ai_ops/` root, and governed repo roots are
  committed artifacts installed at clone time. They do not require setup provisioning."

## No-Install Fallback

If wrappers are not installed (or user selects `none`), commands remain usable by invoking workflow source files
directly (for example: `ai_ops/.ai_ops/workflows/work.md`).

For `claude_app`, this no-install fallback is the normal lane rather than an
exception.

When `active_surface` is `claude_app`, the operator or lead agent must carry
the execution contract in the artifact itself: workflow reference, task brief,
context pack, and any intended delegation limits. Do not treat this surface as
providing ai_ops-installed routing or runtime-enforced delegation guardrails.

## Setup Maintenance Hooks

- **Platform discovery:** `active_surface` is required input and maps to `.ai_ops/local/config.yaml` `modality` semantics.
- **Adapter generation:** setup wrappers are generated from `.ai_ops/workflows/*.md` source contracts.
- **Format/version sync:** when wrapper formats change, update `.ai_ops/setup/README.md` metadata in the same patch.

## Outputs

- Skills/commands installed for the requested tools.
- Or instructions-only path confirmed when install scripts are not required.
- Short confirmation of install targets.
- Post-setup recommendation to declare model capabilities in `/customize`.
- Post-setup recommendation to configure hooks from `01_Resources/templates/config/hooks_template.json`.
- New machine onboarding note: apply global settings and `~/.claude/CLAUDE.md` from templates.
- Note that CLAUDE.md files at repo roots are committed artifacts — no setup provisioning needed.
- Confirmation of governed validation policy written to `.ai_ops/local/config.yaml`.

## Risks and Limits

- `/ai_ops_setup` is setup-only; do not use it for general remediation edits.
- Do not assume install target or scope; capture modality confirmation first.
- GitHub Copilot currently has no Copilot-specific ai_ops installer; use the
  tracked instructions file and, when desired, the Claude skill lane for
  `.claude/skills/` compatibility.
- Do not write setup receipts outside `.ai_ops/local/**`.
- Do not assume command folders exist; if missing, read
  `.ai_ops/workflows/ai_ops_setup.md` manually.

## Resources

- `.ai_ops/setup/README.md`

## Working with Native Commands

Use native assistant commands for session-scoped mechanics (model selection, output formatting, local IDE helpers) when
available.

Use ai_ops workflow commands for governed execution contracts, authority gates, artifact handling, and
validation/reporting behavior.

If overlap exists, native commands handle session mechanics while this workflow remains the source of truth for governed
process behavior.
