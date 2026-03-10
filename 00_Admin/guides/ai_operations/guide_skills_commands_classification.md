---
title: "Reference: Skills and Commands Classification"
id: ref_skills_commands_classification_01
version: 0.1.1
status: active
created: 2026-02-20
last_updated: 2026-03-04
owner: ai_ops
license: Apache-2.0
description: >
  Classifies ai_ops workflows as commands, skills, or both. Compares
  ai_ops capabilities to native Claude Code and Codex features.
  Identifies complementary native commands and potential overlap.
related_refs:
  - 00_Admin/specs/spec_subagent_file.md
---

<!-- markdownlint-disable MD013 -->

# Reference: Skills and Commands Classification

## Compacted Context

ai_ops has 13 workflow files that can be deployed as Claude Code skills
(`.claude/skills/*/SKILL.md`) and Codex skills (`.agents/skills/*/SKILL.md`)
via `/ai_ops_setup`. This document classifies each workflow by its
invocation pattern and compares ai_ops capabilities to native platform
features.

---

## Classification Framework

**Command** -- User types `/command_name` to trigger it. Single-turn or
short procedural execution. Deterministic trigger; the agent does not
auto-invoke commands. In Claude Code, commands live in `commands/` or
`skills/` with `disable-model-invocation: true`.

**Skill** -- Agent auto-discovers and loads when the skill description
matches the task context. Multi-turn capable. The agent decides when the
skill is relevant. In Claude Code, skills live in `skills/` with
`disable-model-invocation: false` (the default).

**Both** -- Deployed as a skill (agent can auto-invoke) AND available as
a command (user can explicitly invoke). Most ai_ops workflows benefit
from both: the user types `/work` to start, but the bootstrap skill
auto-loads when context is missing.

---

## Workflow Classification

Subagent labels (planner/reviewer/closer/linter) are preset names.
Canonical functional roles remain `Coordinator`, `Executor`, `Builder`, `Validator`.

| Workflow | Classification | Subagent Delegation | Canonical Functional Role | Rationale |
| --- | --- | --- | --- | --- |
| `/work` | Both | Primary agent (planner subagent for planning phases, executor for execution) | Coordinator -> Executor | Core workflow. User invokes explicitly; also needs to auto-load when the agent detects governed context. |
| `/bootstrap` | Skill | Planner | Coordinator | Primarily auto-invoked when context is missing. User rarely types `/bootstrap` directly -- `/work` triggers it. |
| `/closeout` | Both | Closer | Executor | User invokes when ready to ship. Primary agent may also invoke after execution completes. |
| `/crosscheck` | Both | Reviewer | Validator | User invokes for explicit review. Primary agent may invoke after changes as a quality gate. |
| `/health` | Both | Reviewer | Validator | User invokes for audits. Primary agent may invoke during quality gates. |
| `/harvest` | Both | Closer | Coordinator -> Executor | User invokes for artifact promotion. Primary agent may invoke as part of closeout. |
| `/customize` | Command | Primary agent (executor subagent for config writes) | Coordinator -> Executor | Always user-initiated. Agent should not auto-invoke config changes. |
| `/profiles` | Command | Primary agent (executor subagent for file regeneration) | Coordinator -> Executor | Always user-initiated. New command for rider/crew management. |
| `/lint` | Both | Linter | Validator | User invokes for standalone validation. Closer and reviewer may invoke as part of their workflows. |
| `/scratchpad` | Command | Executor | Executor | User-initiated note creation. Agent does not auto-create scratchpads. |
| `/work_status` | Command | Planner | Coordinator | User-initiated status check. Single-turn report. |
| `/work_savepoint` | Command | Primary agent | Executor | User-initiated session end. Commits + pushes savepoint, then ends. |
| `/ai_ops_setup` | Command | Primary agent | Coordinator | User-initiated setup. Should never auto-invoke. |

### Plugin Export Implications

Commands-only workflows should have `disable-model-invocation: true` in
their Claude Code skill frontmatter to prevent auto-loading. This saves
context window budget.

| Classification | `disable-model-invocation` | In plugin `commands/` | In plugin `skills/` |
| --- | --- | --- | --- |
| Command only | `true` | Yes | Yes (with auto-invoke disabled) |
| Skill only | `false` | No | Yes |
| Both | `false` | Yes (explicit entry point) | Yes (auto-discoverable) |

---

## New Workflows Introduced by This Workbundle

| Workflow | Classification | File Location | Description |
| --- | --- | --- | --- |
| `/profiles` | Command | `.ai_ops/workflows/profiles.md` (new) | Manage rider archetype profiles, slider adjustment, crew preset selection, derivative file regeneration. |
| `/lint` | Both | `.ai_ops/workflows/lint.md` (new) | Run configured validators against target files. Standalone validation entry point. |

These workflows need SoT files created in `.ai_ops/workflows/` with the
frontmatter schema from WB-01, and corresponding plugin skill/command
entries.

---

## Native Platform Comparison

### Claude Code Native Commands

| Native Feature | ai_ops Equivalent | Relationship |
| --- | --- | --- |
| `/help` | -- | No overlap. Use native. |
| `/compact` | -- | No overlap. Use native. |
| `/clear` | -- | No overlap. Use native. |
| `/agents` | `/profiles` (partial) | Native `/agents` creates/edits subagent files directly. ai_ops `/profiles` manages them through the slider/rider system. Coexist -- ai_ops subagents should be documented as "managed by ai_ops governance" to prevent hand-editing conflicts. |
| `/output-style` | primary agent rider profile (partial) | Native `/output-style` sets session-wide communication style. ai_ops rider profiles set both communication and professional behavior. **Complementary:** `/output-style` handles surface formatting; rider profiles handle behavioral contracts. |
| `/context` | `/work_status` (partial) | Native `/context` shows loaded context. ai_ops `/work_status` shows governed work context. Both useful. |
| `/plugin` | -- | No overlap. Use native for plugin management. |
| Built-in `explore` subagent | `ai-ops-researcher` | Similar function. ai_ops version carries governance context and uses structured return protocol. Users can use either; governed workflows should use `ai-ops-researcher`. |
| Built-in `plan` subagent | `ai-ops-planner` | Similar function. ai_ops version is aware of workbook structure, authority levels, and governance gates. |

### Codex Native Features

| Native Feature | ai_ops Equivalent | Relationship |
| --- | --- | --- |
| Task approval workflow | Governed work lifecycle (`/work` -> `/closeout`) | Codex's approval model is simpler. ai_ops adds authority levels, workbook tracking, and structured review. Complementary when used together. |
| Skill auto-discovery | ai_ops skill descriptions | Same mechanism. ai_ops skills are discovered through the standard `.agents/skills/` path, with optional `.codex/skills/` compatibility mirror. |
| `agents/openai.yaml` UI metadata | ai_ops profile metadata | Codex UI metadata is separate from behavioral profiles. Both can coexist in the export pipeline. |

### Complementary Native Commands

These native commands complement ai_ops workflows and should be documented
as recommended companions:

| Native Command | Complements | How |
| --- | --- | --- |
| `/output-style` | `/profiles` | After setting a rider profile, user can fine-tune surface formatting with native output style. |
| `/compact` | Long `/work` sessions | When a governed work session approaches context limits, use native `/compact` to reduce context. |
| `/agents` | `/profiles` (advanced) | For users who want to hand-edit subagent frontmatter beyond what `/profiles` manages. |
| `/context` | `/work_status` | Quick check of what is loaded vs. what is governed. |

---

## Plugin Folder Setup Recommendation

The ai_ops repo should maintain plugin directory structures for Claude Code
and Codex as part of the base repo. Other tool-specific directories are
created on-demand via `/ai_ops_setup`.

**Always present in repo (maintained by ai_ops):**

```text
ai_ops/plugins/ai-ops-governance/       # Claude Code plugin
    .claude-plugin/plugin.json
    agents/
    commands/
    skills/
    hooks/                               # Reserved for future use
    exports/manifest.yaml               # Export manifest (plugin-only by default)
```

**Created on user request via `/ai_ops_setup`:**

```text
$WORKSPACE_ROOT/.claude/skills/          # Claude project-level skills
$REPO_ROOT/.claude/skills/               # Optional repo-local skills (testing only)
$WORKSPACE_ROOT/.agents/skills/          # Codex workspace install (recommended)
$REPO_ROOT/.agents/skills/               # Codex repo-local skills (optional)
$HOME/.agents/skills/                    # Codex user-scope install
$HOME/.codex/skills/                     # Optional Codex compatibility mirror
$WORKSPACE_ROOT/.cursor/skills/          # Cursor (if supported)
```

This separation ensures the plugin source is always in the ai_ops repo
under version control, while tool-specific discovery surfaces are
generated into the appropriate locations by setup scripts or export
tooling.

---

## Overlap Risk Assessment

| Risk | Mitigation |
| --- | --- |
| User hand-edits plugin subagent files, overwriting rider-generated prose | Document in agents/README.md that these files are managed by `/profiles`. Add a comment header in each agent file: `<!-- Managed by ai_ops /profiles -- manual edits will be overwritten -->`. |
| Native `/agents` command creates a subagent that conflicts with ai_ops subagent names | Use `ai-ops-` prefix on all managed subagents. Native subagents without this prefix coexist without conflict. |
| ai_ops skills consume too much description budget | Set `disable-model-invocation: true` on command-only workflows to reduce auto-load overhead. Keep skill descriptions under 150 chars. |
| Native `/output-style` conflicts with rider relational layer | Document as complementary. `/output-style` is session-level; rider profiles are persistent configuration. If both are set, `/output-style` takes precedence for surface formatting while rider profile governs behavioral instructions. |
