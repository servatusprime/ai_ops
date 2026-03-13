---
title: Guide - Command Workflows
version: 0.7.0
status: active
license: Apache-2.0
created: 2026-01-25
updated: 2026-03-13
last_updated: 2026-03-13
owner: ai_ops
description: Guidance for ai_ops command workflows.
---

<!-- markdownlint-disable MD013 MD036 -->
<!-- markdownlint-disable-next-line MD025 -->
# Guide: Command Workflows

## Purpose

Define how ai_ops slash commands behave and how they map to runbooks,
workflows, and templates.

## Core Principle

ai_ops commands **complement** native AI commands. They provide
structure, governance, and repeatable workflows; they do not replace model
capabilities like editing or reasoning.

**Native AI handles:** Code generation, editing, explanation, conversation, reasoning.

**ai_ops commands handle:** Repo workflows, work orchestration, governance enforcement, customization.

## How Commands Work

Commands are defined in `.ai_ops/workflows/*.md` files. When a user says "run /health"
or types `/health`, the agent should:

1. Locate the corresponding workflow file (`.ai_ops/workflows/health.md`)
2. Read and follow the instructions in that file
3. Execute the behavior appropriate to the current mode (inside vs external repo)

**Note:** Commands appear as slash commands only when installed into a tool's
skill/command folder (tool-specific). Without install, they remain manual.

Terminology mapping:

- **Command** = user-facing invocation (for example `/work`).
- **Skill/wrapper** = tool-specific install form that routes to the same
  workflow source file.

## Command Availability

ai_ops supports two activation modes:

1. **Workspace-level install** (shared across repos in the workspace)
2. **Per-repo install** (commands live inside the target repo)

Direct support targets (setup scripts available):

| Tool | Folder | Format |
| --- | --- | --- |
| Claude Code | `.claude/skills/` (workspace-root recommended), `.claude/commands/` (legacy) | Markdown wrappers |
| Codex CLI | `.agents/skills/` (recommended), `.codex/skills/` (compat mirror) | Markdown wrappers |
| Cursor | `.cursor/commands/` | Markdown |
| Gemini CLI | `.gemini/commands/` | TOML |
| GitHub Copilot | `.github/copilot-instructions.md`, `.claude/skills/`, `.github/skills/` | Instructions + SKILL.md skills |
| Antigravity | `.ai_ops/workflows/` | Native (no install) |

All other tools use manual invocation by referencing `.ai_ops/workflows/*.md`.

GitHub Copilot has no Copilot-specific ai_ops installer today. On supported
Copilot surfaces, the existing `setup_claude_skills.*` lane generates
compatible `SKILL.md` wrappers in `.claude/skills/`.

## Install Safety Rules

When installing wrappers into tool-specific folders:

1. If the target folder contains files, prompt the user before copying.
2. Default behavior is **add-only** (skip existing command files).
3. Never overwrite existing files without explicit user confirmation.
4. Only write inside the tool-specific commands folder (do not touch other files).

## Resources and Templates

Use explicit templates and formats to reduce ambiguity and token waste.

**Command wrapper template**

- `01_Resources/templates/workflows/command_wrapper_template.md`

**Command report formats**

- `/crosscheck`: `01_Resources/templates/workflows/peer_review_template.md`
- `/closeout`: `01_Resources/templates/workflows/work_summary_template.md`
- `/health`: format defined in `00_Admin/runbooks/rb_repo_health_review.md`
- `/harvest`: `01_Resources/templates/documents/harvest_report_template.md`
- `/scratchpad`: `01_Resources/templates/workflows/scratchpad_template.md`

If a repo provides its own template, prefer that over ai_ops defaults.

Lint handling reference:

- `00_Admin/guides/tooling/guide_markdownlint_handling.md`

## Workflow Template Trigger Behavior

Canonical workflow patterns live in:

- `01_Resources/templates/workflows/`

Command workflows do not auto-discover or auto-execute template files.
Templates are consulted only when explicitly referenced by a workbook, runbook,
or requestor.

## Free-Form Notes

Use `customizations.notes.free_form` only for non-operational preferences or context.
Do not treat free-form notes as executable settings or requirements.

## Command Behavior Modes

Commands operate in two modes based on repo context:

### Mode Detection Logic

```text
1. Check for AGENTS.md in current directory
2. If found:
   a. Read workspace topology block (ops_stack_root)
   b. If ops_stack_root == current_repo -> INSIDE MODE (Maintainer)
   c. If ops_stack_root != current_repo -> EXTERNAL MODE (User)
3. If not found:
   a. Check for .ai_ops/workflows/ folder
   b. If present -> INSIDE MODE (legacy/fallback)
   c. If absent -> NO AI_OPS_STACK
```

### Inside Repo

- Full access to ai_ops governance and runbooks
- Authority levels 1-4 apply per policy
- Can modify governance files (with approval)
- Can execute all runbooks

### External Repo

- Commands check the **user's repo** against its own professed rules
- Authority capped at Level 2 (no governance changes to ai_ops)
- User's repo authority determined by user's project policies
- Same command function, different rule source (user's repo vs ai_ops)

**Key insight:** `/health` in an external repo checks if that repo is consistent
with **its own** README, .gitignore, stated conventions--not ai_ops's rules.

## Command Reference

### /work

Start or resume a work session.

| Mode | Behavior |
| --- | --- |
| Inside | Full access to workbooks, workbundles; display active work context |
| External | Full work hierarchy (workbooks/workbundles/workprograms), with lighter thresholds and guardrails |

**Workflow:** `.ai_ops/workflows/work.md`

**Minimum Inputs / Conditions**

- Inside: `AGENTS.md` present or `.ai_ops/workflows/` present.
- External: repo path + confirmation of work vs resource repos; create or confirm workspace roots.

**Estimator and readiness requirements**

- If request scope is vague, `/work` should ask for outcome, boundaries, and
  expected artifacts, then propose likely authority tier and tracking mode.
- On first entry to a governed repo in-session, `/work` should verify sandbox +
  validator baseline path availability before execution starts.

### /crosscheck

Conduct a structured peer review.

| Mode | Behavior |
| --- | --- |
| Inside | Use full peer_review_template.md with workbundle context |
| External | Lightweight review structure (summary, observations, recommendations) |

**Workflow:** `.ai_ops/workflows/crosscheck.md`

**Minimum Inputs / Conditions**

- Inside: review target files + chosen review format (inline or separate file).
- External: review target files + user-provided review artifact or default template.
- Review direction: `top-down` | `bottom-up` | `hybrid` (default by review type).
- Review strictness: `standard` | `strict` (default `strict` for Level 3+ and governance scope).

Direction defaults:

- design, mid_execution: `top-down`
- completion: `bottom-up`
- governance or Level 3+ workbook scope: `hybrid` (required)

Strict-review requirements:

- Findings must include evidence citations (`path:line` or command output).
- Findings must be classified as `code_enforced`, `doc_only`, or `process_gap`.
- Recommendations must be tagged `patch_now`, `proposal_seed`, or `follow_on_workbook`.
- Review output must include a CSCC readiness table and explicit verdict.

**Note:** Named `/crosscheck` to avoid conflict with native PR review commands.

### /health

Run a repo health check--verify the repo is consistent and clean.

| Mode | Behavior |
| --- | --- |
| Inside | Check ai_ops against its policies, structure, and health criteria |
| External | Check user's repo against **its own** stated rules and conventions |

**Health checks (both modes):**

- **Self-consistency:** Does README match actual structure? Are stated conventions followed?
- **Documentation accuracy:** Are dependencies documented correctly?
- **Cruft detection:** Dead files, orphaned references, stale branches
- **Metadata completeness:** Required fields present in config files

**Workflow:** `.ai_ops/workflows/health.md`
**Runbook:** `00_Admin/runbooks/rb_repo_health_review.md`

- **Metrics contract:** `.ai_ops/workflows/health.md` section `Metrics Output Contract`

**Minimum Inputs / Conditions**

- Inside: access to runbook + repo structure.
- External: repo entry files (README, any config files that state conventions).

### /closeout

Finalize a work session with cleanup, lint, commit, and push.

| Mode | Behavior |
| --- | --- |
| Inside | Full turbo workflow: cleanup workbundle, harvest scratchpad, lint, commit, push |
| External | Simplified workflow: cleanup work notes, lint, commit, push |

**Closeout steps (Inside):**

1. Update workbundle status and checkpoint notes
2. Harvest keepers from scratchpad, archive or delete rest
3. If `future_work_registry.yaml` changed, regenerate future work scorecard
4. Run linters (markdownlint, yamllint, etc.)
5. Stage changes with summary
6. Commit with turbo authorization (streamlined, no pause)
7. Push to remote

**Closeout steps (External):**

1. Update any work tracking artifacts
2. Run repo's configured linters (or common fallbacks)
3. Stage changes with summary
4. Commit (confirm before push)
5. Push to remote

**Workflow:** `.ai_ops/workflows/closeout.md`
**Runbook:** `00_Admin/runbooks/rb_commit_push_streamlining_01.md`

**Minimum Inputs / Conditions**

- Inside: active workbundle or staged changes; turbo authorization enabled.
- External: staged or unstaged changes; user confirms push.

### /bootstrap

Initialize agent context.

| Mode | Behavior |
| --- | --- |
| Inside | Full bootstrap with certification; read AGENTS.md then CONTRIBUTING.md |
| External | Simplified bootstrap; orient to repo conventions using available entry files |

**Workflow:** `.ai_ops/workflows/bootstrap.md`
**Runbook:** `00_Admin/runbooks/rb_bootstrap.md`

**Minimum Inputs / Conditions**

- Inside: `AGENTS.md` present.
- External: minimum repo entry files (README, AGENTS/HUMANS if present) + user intent.

### /scratchpad

Create a scratchpad for notes.

| Mode | Behavior |
| --- | --- |
| Inside | Create in active workbundle folder using scratchpad_template.md |
| External | Create in user's project (.notes/ or docs/notes/ or root) |

**Workflow:** `.ai_ops/workflows/scratchpad.md`
**Template:** `01_Resources/templates/workflows/scratchpad_template.md`

**Minimum Inputs / Conditions**

- Inside: active workbundle or explicit scratchpad location.
- External: user-selected location (docs/notes/, .notes/, or repo root).

### /harvest

Consolidate, prune, and summarize work artifacts.

| Mode | Behavior |
| --- | --- |
| Inside | Harvest within active workbundle or user-specified targets |
| External | Harvest within user-specified targets under repo rules |

**Workflow:** `.ai_ops/workflows/harvest.md`

**Minimum Inputs / Conditions**

- One or more target locations.
- Confirm whether scope is limited to the last active work context.
- If `future_work_registry.yaml` is edited during harvest, regenerate
  `future_work_scorecard.md` before completion.

### /customize

Configure agent preferences and user settings.

| Mode | Behavior |
| --- | --- |
| Inside | Full customization with schema access (commit style, file locations, linter prefs) |
| External | Same settings available; stored in user's repo config file |

**Focus areas:** Commit message style, preferred file locations, linter preferences,
notification settings. Rider/crew configurations live under `/profiles`, not `/customize`.

**Workflow:** `.ai_ops/workflows/customize.md`

**Minimum Inputs / Conditions**

- Inside: access to `aiops_config.template.yaml`.
- External: user opts in to local config file; settings adapt to user's repo structure.

### /work_status

Summarize active work context and blockers.

| Mode | Behavior |
| --- | --- |
| Inside | Show program/workbundle/checkpoint context, blockers, next steps |
| External | Show user's work context if tracked; offer to set up if not |

**Minimum Inputs / Conditions**

- Inside: `AGENTS.md` present or active workbook.
- External: any work tracking artifact (workbook, or similar).

**Workflow:** `.ai_ops/workflows/work_status.md`

**Status block requirement**

When context exists, `/work_status` should include:

- active context summary
- cross-session recap
- authority trail snapshot
- one next-step pointer

If authority trail data is missing, `/work_status` should note that and point to
`/work` selfcheck evidence expectations.

### Validator Rule Pointers

Do not add a dedicated `/rules` command in this cycle.

Use existing artifacts:

- Operational entry point:
  `00_Admin/runbooks/rb_repo_validator_01.md`
- Canonical rules source:
  `00_Admin/configs/validator/validator_config.yaml`

### /work_savepoint

Commit + push active work as a savepoint, then end the session. Pass `--no-commit` to end without committing.

| Mode | Behavior |
| --- | --- |
| Inside | Stage, commit (`savepoint:` prefix), push; update compacted context |
| External | Commit + push user work artifact; summarize next steps |

**Minimum Inputs / Conditions**

- Inside: active workbook or workbundle.
- External: active work context to save.

**Workflow:** `.ai_ops/workflows/work_savepoint.md`

### /ai_ops_setup

Install or verify ai_ops wrappers (skills/commands) and write setup receipts.

| Mode | Behavior |
| --- | --- |
| Inside | Confirm surface + install scope; run setup scripts; update setup receipt |
| External | Same behavior when ai_ops stack is present and user requests setup |

**Workflow:** `.ai_ops/workflows/ai_ops_setup.md`

**Minimum Inputs / Conditions**

- Active surface (`codex_cli`, `claude_code`, `cursor`, `gemini_cli`, `other`)
- Installation target (`skills`, `commands`, `both`, `none`)
- Install scope (`workspace`, `repo`, `user`)

## Runbook Scope Guardrail

Only runbooks directly invoked by commands should be updated as part of
command workflow development. Broader runbook refactors should be deferred
to separate workbooks.

## Command Naming Decision

- **Decision:** Keep commands unprefixed (e.g., `/health` not `/aios_health`)
- **Rationale:** Context (AGENTS.md + `.ai_ops/workflows/` presence) disambiguates
- **Fallback:** If conflict detected, agent asks for clarification

## Open Questions and Discussion

### /bootstrap value

**Question:** How useful is `/bootstrap` for external repos?

**Assessment:** Essential for external repos. Agents need to:

- Understand the repo's conventions
- Find entry files (README, AGENTS.md)
- Prepare for work

Without bootstrap, agents start cold with no context.

## Draft Notes

- Keep command names unprefixed unless conflicts are observed.
- If a command name conflicts with a native tool command, ask for clarification.
- Use canonical templates for review and scratchpad by default.
- This guide should be promoted to `00_Admin/guides/ai_operations/` when finalized.
