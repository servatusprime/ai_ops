---
title: Guide - AI Compatibility Matrix
version: 0.2.0
status: active
license: Apache-2.0
created: 2026-01-25
updated: 2026-03-13
last_updated: 2026-03-13
owner: ai_ops
---

<!-- markdownlint-disable-next-line MD025 -->
# Guide: AI Compatibility Matrix

## How ai_ops Works with AI Tools

ai_ops commands work via workflow files that any AI agent can read.
Direct wrapper installs improve discoverability and make slash commands
available in tools that support skill/command folders.

## Compatibility Summary

| AI Tool | Compatibility | How to Use |
| --- | --- | --- |
| Claude Code | Direct (wrapper files) | Install to workspace-root `.claude/skills/` (recommended) or `.claude/commands/` (legacy), then invoke `/work` |
| Codex CLI | Direct (wrapper files) | Install to `.agents/skills/` (recommended) with optional `.codex/skills/` compatibility mirror, then invoke `/work` |
| GitHub Copilot Chat | Instructions + optional skills | Use `.github/copilot-instructions.md` or `AGENTS.md` for repo guidance; supported surfaces can also read project skills from `.claude/skills/` or `.github/skills/` |
| Cursor | Direct (command wrappers) | Install to `.cursor/commands/` then invoke `/work` |
| Gemini CLI | Direct (TOML command wrappers) | Install to `.gemini/commands/` then invoke `/work` |
| Antigravity | Direct (native) | Uses `.ai_ops/workflows` as command source |
| Cline | Manual | Include workflow files in context |
| Aider | Manual | Add workflow files to chat context |
| ChatGPT (web) | Limited | Copy/paste workflow content into conversation |
| Any LLM with file access | Manual | Read workflow files and follow instructions |

## Command Manifest

The command set is defined by workflow files in `.ai_ops/workflows/`:

- `work.md` -> `/work`
- `work_status.md` -> `/work_status`
- `work_savepoint.md` -> `/work_savepoint`
- `harvest.md` -> `/harvest`
- `crosscheck.md` -> `/crosscheck`
- `health.md` -> `/health`
- `closeout.md` -> `/closeout`
- `bootstrap.md` -> `/bootstrap`
- `scratchpad.md` -> `/scratchpad`
- `customize.md` -> `/customize`

## Feature Support by Tool (Not Verified)

| Feature | Claude Code | Codex | Copilot | Cursor | Gemini | Antigravity |
| --- | --- | --- | --- | --- | --- | --- |
| Read workflow files | Supported | Supported | Instruction-based | Supported | Supported | Supported |
| Execute commands | Supported | Supported | Instruction-based | Supported | Supported | Supported |
| Edit files | Supported | Supported | Limited | Supported | Supported | Supported |
| Git operations | Supported | Supported | Limited | Supported | Supported | Supported |
| Mode detection | Supported | Supported | Instruction-based | Supported | Supported | Supported |

## Notes

- These entries are not verified across tools; treat as expected behavior.
- Antigravity support is verified (native `.ai_ops/workflows` detection).
- Basic usage assumes file access and the ability to read workflow files.
- "Direct" means tool-native wrappers are installed in a tool-specific folder.
- "Instruction-based" means no native slash menu; the tool follows a documented command phrase.
- Install scope can be workspace-level or per-repo; both are supported by WB-07.
