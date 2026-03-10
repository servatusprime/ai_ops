---
title: "Reference: Native Command Comparative Analysis"
id: ref_native_command_comparison_01
version: 0.1.1
status: active
license: Apache-2.0
created: 2026-02-21
last_updated: 2026-03-04
owner: ai_ops
description: >
  Inventory and comparison of built-in commands across Claude Code, Codex
  CLI, Codex IDE Extension, and Gemini CLI. Maps native capabilities to
  ai_ops commands. Identifies complementary relationships, overlaps, and
  gaps.
related_refs:
  - 00_Admin/guides/ai_operations/guide_skills_commands_classification.md
---

<!-- markdownlint-disable MD013 MD033 -->

# Reference: Native Command Comparative Analysis

## Compacted Context

Users of ai_ops may work with any of the major AI coding agents -- Claude
Code, Codex (CLI and VS Code extension), or Gemini CLI. Each ships with
built-in slash commands. ai_ops commands need to complement these native
commands, avoid conflicts, and provide guidance on how they interact.

This analysis also addresses multi-account users who switch between agents
across sessions. ai_ops governance should produce consistent outcomes
regardless of which agent is executing.

---

## Native Command Inventories

### Claude Code Built-in Commands (~30+)

Source: code.claude.com/docs, verified 2026-02-21.

**Session management:**

| Command | Function |
| --- | --- |
| `/help` | List all commands |
| `/clear` | Clear conversation, start fresh |
| `/compact` | Compress context, preserve key info |
| `/context` | Show context window usage |
| `/status` | View system status |
| `/cost` | Show token usage and costs |
| `/export` | Export conversation to file |

**Configuration:**

| Command | Function |
| --- | --- |
| `/model` | Switch between Claude models (Sonnet, Opus, Haiku) |
| `/permissions` | Manage tool permissions |
| `/output-style` | Change communication style |
| `/memory` | Edit CLAUDE.md |
| `/config` | Open configuration |
| `/hooks` | Manage lifecycle hooks |

**Agent and tools:**

| Command | Function |
| --- | --- |
| `/agents` | Manage subagents (view, create, edit, delete) |
| `/plugin` | Manage plugins (install, list, marketplace) |
| `/mcp` | Manage MCP server connections |
| `/review` | Trigger code review |
| `/init` | Initialize project (creates CLAUDE.md) |
| `/install-github-app` | Install GitHub PR review app |

**Navigation:**

| Command | Function |
| --- | --- |
| `/resume` | Continue previous session |
| `/add-dir` | Add directories to context |
| `/doctor` | Run diagnostics |
| `/bug` | Report a bug |
| `/changelog` | View release notes |

**Built-in subagents:** Plan, Explore, general-purpose Task.

---

### Codex CLI Built-in Commands

Source: developers.openai.com/codex/cli, verified 2026-02-21.

**Session management:**

| Command | Function |
| --- | --- |
| `/compact` | Compress conversation history |
| `/new` | Start new conversation (clear state) |
| `/quit`, `/exit` | End session |
| `/status` | Show model, approval policy, token usage |
| `/diff` | Show git diff of changes |

**Configuration:**

| Command | Function |
| --- | --- |
| `/model` | Switch models (gpt-5.3-codex, etc.) |
| `/permissions` (or `/approvals`) | Set approval mode (Auto, Suggest, etc.) |
| `/personality` | Adjust agent personality |
| `/experimental` | Toggle experimental features (multi-agents, etc.) |
| `/agent` | Select active agent role |
| `/statusline` | Configure status bar items |
| `/debug-config` | View config layer diagnostics |

**Workflows:**

| Command | Function |
| --- | --- |
| `/review` | Code review by separate agent |
| `/plan` | Enter plan mode (no execution) |
| `/init` | Create AGENTS.md, bootstrap project |
| `/fork` | Fork session into new thread |
| `/mention` | Pull specific files into context |

**Memory and context:**

| Command | Function |
| --- | --- |
| `/m_update` | Update memory |
| `/m_drop` | Drop memory item |

**Built-in tools:** Codebase search, file read/write, shell execution,
web search (cached/live).

---

### Codex IDE Extension (VS Code) Commands

Source: developers.openai.com/codex/ide/slash-commands, verified 2026-02-21.

The IDE extension has a significantly reduced command set compared to
the CLI -- this is the single-agent environment referenced in review note 2.

| Command | Function |
| --- | --- |
| `/auto-context` | Toggle automatic context inclusion |
| `/cloud` | Switch to cloud mode (remote execution) |
| `/cloud-environment` | Choose cloud environment |
| `/feedback` | Submit feedback |
| `/local` | Switch to local mode |
| `/review` | Code review of uncommitted changes |
| `/status` | Show thread ID, context, rate limits |

**Notable absences:** No `/compact`, no `/model`, no `/init`, no `/plan`,
no `/fork`, no `/agent`, no `/personality`. The IDE extension operates as
a single-agent chat with simplified controls.

---

### Gemini CLI Built-in Commands

Source: github.com/google-gemini/gemini-cli, developers.google.com,
verified 2026-02-21.

**Session management:**

| Command | Function |
| --- | --- |
| `/help` | List commands and keyboard shortcuts |
| `/quit` | End session |
| `/compact` | Compress conversation |
| `/stats` | Show token and session statistics |
| `/save` | Save conversation checkpoint |
| `/restore` | Restore from checkpoint |
| `/chat` | Switch to chat mode |

**Configuration:**

| Command | Function |
| --- | --- |
| `/model` | Switch models (Pro, Flash) |
| `/tools` | List available tools |
| `/mcp` | List MCP servers and their tools |
| `/memory` | Manage conversation memory |
| `/auth` | Authentication management |

**Built-in tools:** Codebase Investigator Agent, Edit (replace),
FindFiles (glob), GoogleSearch, ReadFile, ReadFolder, SaveMemory,
SearchText, Shell, WebFetch, WriteFile, WriteTodos.

**Custom commands:** TOML-based files in `~/.gemini/commands/` (user)
or `.gemini/commands/` (project). Supports namespacing via subdirectories
(e.g., `git/commit.toml` -> `/git:commit`).

**Context files:** `GEMINI.md` or `AGENT.md` (equivalent to CLAUDE.md
and AGENTS.md).

---

## Cross-Platform Command Mapping

### Universal Capabilities (all three platforms have equivalent)

| Function | Claude Code | Codex CLI | Gemini CLI |
| --- | --- | --- | --- |
| Compress context | `/compact` | `/compact` | `/compact` |
| Clear/reset | `/clear` | `/new` | (restart) |
| Switch model | `/model` | `/model` | `/model` |
| Status/stats | `/status`, `/context`, `/cost` | `/status` | `/stats` |
| Code review | `/review` | `/review` | (via custom command) |
| Project init | `/init` | `/init` | (via GEMINI.md manually) |
| MCP integration | `/mcp` | CLI config | `/mcp` |
| Exit | (Ctrl+C) | `/quit` | `/quit` |
| Help | `/help` | `/help` | `/help` |

### Platform-Specific Capabilities

| Capability | Claude Code | Codex CLI | Gemini CLI |
| --- | --- | --- | --- |
| Subagent management | `/agents` | `/agent` (limited) | None |
| Plugin management | `/plugin` | None | None |
| Session resume | `/resume` | `codex resume` (CLI flag) | `/restore` |
| Session fork | None | `/fork` | None |
| Git diff view | None | `/diff` | None |
| Plan mode | Plan subagent | `/plan` | (via custom command) |
| Personality/style | `/output-style` | `/personality` | None |
| Lifecycle hooks | `/hooks` | CLI config | None |
| Web search | Via tools | `/search` flag | GoogleSearch tool |
| Memory management | `/memory` (CLAUDE.md) | `/m_update`, `/m_drop` | `/memory`, SaveMemory |
| Permission presets | `/permissions` | `/permissions` | (sandboxing config) |
| Export conversation | `/export` | Transcript files | `/save` |
| Diagnostics | `/doctor` | `/debug-config` | None |

### Capabilities Absent from All Platforms (ai_ops fills the gap)

| Capability | ai_ops Command | Why native doesn't provide this |
| --- | --- | --- |
| Governed work lifecycle | `/work`, `/work_savepoint`, `/work_status` | Native agents have no concept of a "governed work session" with authority levels, scope tracking, and evidence requirements. |
| Structured peer review | `/crosscheck` | Native `/review` does code review. `/crosscheck` reviews against repo quality axes (clarity, thrift, context, governance). |
| Repository health audit | `/health` | No native equivalent. `/health` checks structural integrity against ai_ops standards. |
| Artifact promotion/archive | `/harvest` | No native artifact lifecycle management. |
| Governed closeout | `/closeout` | Native commit/push is ungoverned. `/closeout` adds validation gates, commit message standards, and archive steps. |
| Context initialization | `/bootstrap` | Native `/init` creates config files. `/bootstrap` loads governance context (AGENTS.md, CONTRIBUTING.md). |
| Agent behavioral profiles | `/profiles` | `/personality` (Codex) and `/output-style` (Claude) are session-level surface adjustments. `/profiles` manages persistent behavioral contracts across roles. |
| Standalone validation | `/lint` | No native "just run the linters" command. |
| Repo configuration | `/customize` | Native config is agent-centric. `/customize` is repo-centric (preferences, session limits, external resources). |
| Setup for multiple agents | `/ai_ops_setup` | Each platform has its own init. ai_ops provides cross-platform setup. |

---

## Complementarity Analysis

### Commands That Complement Each Other

| ai_ops Command | Native Complement | How They Work Together |
| --- | --- | --- |
| `/work` | `/init` (Claude/Codex) | `/init` creates platform config files. `/work` loads governance context on top of them. User runs `/init` once, then `/work` each session. |
| `/crosscheck` | `/review` (Claude/Codex) | `/review` does code review (syntax, logic, style). `/crosscheck` does governance review (axes, evidence, authority). Use both for comprehensive review. |
| `/closeout` | `/diff` (Codex) | Codex `/diff` shows changes. ai_ops `/closeout` validates, commits, and archives. User can run `/diff` before `/closeout` for a preview. |
| `/profiles` | `/output-style` (Claude), `/personality` (Codex) | Native commands handle session-level formatting. `/profiles` handles persistent behavioral contracts. `/output-style` takes precedence for surface formatting; rider profiles govern decision-making. |
| `/lint` | (no equivalent) | Pure addition. No native conflict. |
| `/bootstrap` | `/init` (Claude/Codex) | `/init` is one-time setup. `/bootstrap` is per-session context loading. Complementary lifecycle stages. |
| `/work_status` | `/status` (all) | Native `/status` shows token/model info. `/work_status` shows governed context (active artifacts, session scope, workbook state). Different information. |
| `/compact` (native) | `/work_savepoint` (ai_ops) | When context is running low, user can `/work_savepoint` to commit governed state, then `/compact` to reclaim tokens. `/work_savepoint` preserves governance metadata that `/compact` might lose. |

### Potential Conflict Points

| Risk | Description | Mitigation |
| --- | --- | --- |
| `/review` confusion | User might type `/review` expecting ai_ops crosscheck behavior | Document in `/crosscheck` description that it differs from native `/review`. Consider an alias: `/crosscheck` can also be invoked as `/ai-ops:review` in plugin contexts to disambiguate. |
| `/init` vs `/bootstrap` | User runs `/init` and expects governance context | `/work` should detect whether `/init` was run but `/bootstrap` was not, and offer to bootstrap. |
| Memory systems | Native `/memory` edits CLAUDE.md. ai_ops config lives in `.ai_ops/`. | Separate concerns. Document that native memory manages the platform's context file; ai_ops config manages repo governance settings. |
| Plan mode confusion | Codex `/plan` enters a read-only planning mode. ai_ops planner subagent is a delegated planning role. | Different mechanisms. Document that `/plan` is a session mode; the ai_ops planner is a functional role assigned to a subagent. |

---

## Single-Agent Mode Considerations

### Problem

The Codex IDE extension (VS Code) and some Gemini configurations operate
as single-agent environments -- there is no subagent spawning mechanism.
ai_ops must degrade gracefully.

### Architecture

In single-agent mode:

1. **No subagent delegation.** The lead (and only) agent executes all
   workflow steps directly.
2. **Agent profiles still apply.** The active profile's behavioral
   instructions are injected into the agent's context (via AGENTS.md
   or equivalent). The agent follows the prose contract even without
   subagent infrastructure.
3. **Role-specific sections are collapsed.** Instead of delegating
   `/crosscheck` to a reviewer subagent, the single agent reads the
   crosscheck workflow and follows its steps using the reviewer profile's
   professional-layer instructions.
4. **The AI-facing return protocol is not used.** Since there is no lead
   agent receiving structured returns from subagents, the protocol section
   is omitted. The agent communicates directly with the human using the
   relational layer.
5. **Profile switching is per-workflow.** When the single agent runs
   `/crosscheck`, it loads the reviewer profile's behavioral instructions.
   When it runs `/work`, it loads the executor profile. This is
   "virtual role switching" -- the agent changes its behavioral contract
   based on what it is doing, not based on which subagent is spawned.

### Implementation

The profiler script generates two output variants:

- **Multi-agent variant:** Subagent `.md` files with 2-section body
  (professional + AI-facing protocol). Used by Claude Code plugin.
- **Single-agent variant:** A consolidated profile file that maps
  workflows to behavioral instructions. Used by Codex IDE, Gemini
  agent mode, and any environment without subagent support.

The single-agent variant would be structured as:

```markdown
## Behavioral Profiles by Workflow Context

### When executing /work, /scratchpad, /customize
[Executor profile professional-layer prose]

### When executing /crosscheck, /health
[Reviewer profile professional-layer prose]

### When executing /bootstrap, /work_status
[Planner profile professional-layer prose]

### When executing /closeout, /harvest
[Closer profile professional-layer prose]

### When executing /lint
[Linter profile professional-layer prose]

### When researching or gathering context
[Researcher profile professional-layer prose]

### Communication style (all contexts)
[Primary agent relational-layer prose]
```

This file is included in AGENTS.md, GEMINI.md, or the equivalent
context file for the target platform.

---

## Multi-Account User Dynamics

Users who work with multiple AI agents (Claude Code, Codex,
Gemini) across sessions need:

1. **Consistent governance.** ai_ops rules apply regardless of which
   agent is executing. The SoT workflow files are agent-agnostic.
2. **Consistent behavioral profiles.** A Logike planner should behave
   similarly whether the agent is Claude or Codex. The prose generation
   pipeline produces agent-agnostic instructions. Platform-specific
   tuning is a future enhancement (see PS in scratchpad about per-model
   prompt tuning).
3. **Predictable command mapping.** Users should know that `/work`
   means the same thing in every agent environment. The workflow file
   content is identical; only the delivery mechanism differs (skill,
   command, custom prompt, TOML).
4. **Cross-agent setup.** `/ai_ops_setup` detects the active environment
   and creates the appropriate adapter files (workspace-root `.claude/skills/`,
   `.agents/skills/`, `.gemini/commands/`).

### Platform Adapter Matrix

| ai_ops Asset | Claude Code | Codex CLI | Codex IDE | Gemini CLI |
| --- | --- | --- | --- | --- |
| Workflow files | Skill (SKILL.md) | Skill (SKILL.md) | Skill (SKILL.md) | Custom command (TOML) |
| Agent profiles (multi-agent) | Subagent `.md` files | Not applicable | Not applicable | Not applicable |
| Agent profiles (single-agent) | CLAUDE.md section | AGENTS.md section | AGENTS.md section | GEMINI.md section |
| Configuration | `.ai_ops/local/config.yaml` | `.ai_ops/local/config.yaml` | `.ai_ops/local/config.yaml` | `.ai_ops/local/config.yaml` |
| Context file | CLAUDE.md | AGENTS.md | AGENTS.md | GEMINI.md / AGENT.md |
| Plugin package | `plugins/ai-ops-governance/` | Not applicable | Not applicable | Not applicable |
| Custom commands | `commands/*.md` | `.codex/prompts/*.md` | Not applicable | `.gemini/commands/*.toml` |

Legacy compatibility note: `.ai_ops/config.yaml` remains a fallback path
during the active migration window; `.ai_ops/local/config.yaml` is canonical.

<!-- REVIEW NOTE: Codex is deprecating custom prompts in favor of skills.
The "custom commands" row for Codex may shift to skills-only. Gemini
custom commands use TOML format, not Markdown -- the export script needs
a Gemini-specific adapter that generates TOML from the SoT workflow files.
This is a gap in the current export architecture (WB-02). -->

---

## Recommendations

### Immediate Actions (This Workbundle)

1. Update `guide_skills_commands_classification.md` to reference this
   analysis for the native comparison section.
2. Add single-agent mode provisions to `spec_subagent_file.md`
   and `guide_prose_generation.md`.
3. Add the platform adapter matrix to the workbundle README as a
   key decision.

### Future Work

1. **Gemini TOML adapter** -- Export generation script (WB-02) needs a
   Gemini target that generates `.toml` command files from SoT workflows.
2. **Per-model prompt tuning** -- Empirical testing of prose fragments
   across Claude, GPT-5.x, and Gemini models to verify behavioral
   consistency.
3. **Native command documentation** -- Add a "working with native commands"
   section to each ai_ops workflow file, noting which native commands
   complement that workflow.
4. **Multi-agent detection** -- The `/work` bootstrap sequence should
   detect whether the current environment supports subagents. If not,
   load the single-agent profile variant automatically.
