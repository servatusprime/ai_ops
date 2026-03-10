---
name: ai_ops_setup
description: Run ai_ops setup scripts for skills/commands
kind: workflow
version: 0.1.2
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
    short-description: Run ai_ops setup scripts for skills and command wrappers.
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

## Intent

Run the appropriate ai_ops setup scripts for the user's tool(s).

## Setup Contract (Mandatory)

`/ai_ops_setup` is the only lane that writes setup completion receipts.

- Required contract version is read from `00_Admin/configs/setup_contract.yaml` `required_version`.
- Local receipt path is read from `00_Admin/configs/setup_contract.yaml` `receipt_path` (default: `.ai_ops/local/setup/state.yaml`).
- Local operator state is stored under `.ai_ops/local/**` and must not be committed.
- Compatibility read for legacy local inputs is allowed during migration:
  - `.ai_ops/config.yaml`
  - `.ai_ops/profiles/active_crew.yaml`

## Modality Confirmation (Mandatory)

Before any setup actions, capture explicit confirmation:

| Field                 | Values                                                              | Required |
| --------------------- | ------------------------------------------------------------------- | -------- |
| `active_surface`      | `codex_cli` \| `claude_code` \| `cursor` \| `gemini_cli` \| `other` | Yes      |
| `installation_target` | `skills` \| `commands` \| `both` \| `none`                          | Yes      |
| `install_scope`       | `workspace` \| `repo` \| `user`                                     | Yes      |
| `governed_validation_policy` | `ai_ops` \| `repo_native`                                     | Yes      |

**Rules:**

1. Do NOT assume installation target. Default is `none` until user confirms.
2. If user says "just set up" without specifying, ask explicitly.
3. Record confirmation in session context before proceeding.
4. If `installation_target` is `none`, skip all install scripts and confirm no action taken.
5. If `install_scope` is not specified, default to `workspace` and confirm with user.
6. If `governed_validation_policy` is not specified, default to `ai_ops` and confirm with user.

**Install scope behavior:**

| Scope       | Install Root                                            | Workflow Pointer            | Script Flag   |
| ----------- | ------------------------------------------------------- | --------------------------- | ------------- |
| `workspace` | `<workspace_root>/.agents/skills/` or `.claude/skills/` | `ai_ops/.ai_ops/workflows/` | `--workspace` |
| `repo`      | `ai_ops/.agents/skills/` or `ai_ops/.claude/skills/`    | `.ai_ops/workflows/`        | (default)     |
| `user`      | `$HOME/.agents/skills/` or `$HOME/.claude/skills/`      | `ai_ops/.ai_ops/workflows/` | `--user`      |

Workspace scope is recommended for multi-repo workspaces where agents run from workspace root, not repo root.

## Inputs

- Target tool(s): Claude, Codex, Cursor, Gemini
- OS: Windows or Mac/Linux
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
5. Check existing installation state for the selected surface and scope:
   - If wrappers already exist at the target scope root, report "already installed" and offer `--force` overwrite or
     stop.
6. Run the matching script(s) from `.ai_ops/setup/` with the resolved scope flag:
   - Claude skills: `setup_claude_skills.bat|.sh [--workspace|--user]`
   - Codex skills: `setup_codex_skills.bat|.sh [--workspace|-w]`
   - Commands: `setup_claude.bat|.sh`, `setup_cursor.bat|.sh`, `setup_gemini.bat|.sh`
   - Echo resolved install root and workflow pointer before executing.
7. For Claude installs, ensure plugin skeleton folders exist:
   - `plugins/ai-ops-governance/agents/`
   - `plugins/ai-ops-governance/commands/`
   - `plugins/ai-ops-governance/.claude-plugin/`
8. For Codex installs, use primary skills path by default:
   - primary: `.agents/skills/` (or `$HOME/.agents/skills/`)
   - compatibility mirror (`.codex/skills/` or `$HOME/.codex/skills/`) is on-demand only when explicitly requested.
9. Report results and note where files were installed.
10. Ensure local setup-state surfaces exist:

- `.ai_ops/local/config.yaml` (when local overrides are created),
- `.ai_ops/local/profiles/active_crew.yaml` (when profile state exists),
- `.ai_ops/local/setup/state.yaml` (setup receipt).

11. Write/update setup receipt with:

- required setup contract version,
- installed surface summary,
- timestamp.

12. Report whether setup-gated lanes are now ready:

- `/work`
- `/customize`
- `/profiles`

13. Recommend post-setup model declaration:

- "Run `/customize` to declare available models and default reasoning tier in `.ai_ops/local/config.yaml`."
- "Run `/profiles` if you want behavior tuning per model family after declaration."

## No-Install Fallback

If wrappers are not installed (or user selects `none`), commands remain usable by invoking workflow source files
directly (for example: `ai_ops/.ai_ops/workflows/work.md`).

## Outputs

- Skills/commands installed for the requested tools.
- Short confirmation of install targets.
- Post-setup recommendation to declare model capabilities in `/customize`.
- Confirmation of governed validation policy written to `.ai_ops/local/config.yaml`.

## Setup Maintenance Hooks

- **Platform discovery:** `active_surface` is required input and maps to `.ai_ops/local/config.yaml` `modality` semantics.
- **Adapter generation:** setup wrappers are generated from `.ai_ops/workflows/*.md` source contracts.
- **Format/version sync:** when wrapper formats change, update `.ai_ops/setup/README.md` metadata in the same patch.

## Working with Native Commands

Use native assistant commands for session-scoped mechanics (model selection, output formatting, local IDE helpers) when
available.

Use ai_ops workflow commands for governed execution contracts, authority gates, artifact handling, and
validation/reporting behavior.

If overlap exists, native commands handle session mechanics while this workflow remains the source of truth for governed
process behavior.

## Risks and Limits

- `/ai_ops_setup` is setup-only; do not use it for general remediation edits.
- Do not assume install target or scope; capture modality confirmation first.
- Do not write setup receipts outside `.ai_ops/local/**`.
- Do not assume command folders exist; if missing, read
  `.ai_ops/workflows/ai_ops_setup.md` manually.

## Resources

- `.ai_ops/setup/README.md`
