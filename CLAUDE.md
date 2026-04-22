# ai_ops

AI-first governance and operations framework for multi-agent development.
Apache-2.0.

## Entry Point

**Read `AGENTS.md` before any work.** This is the canonical bootstrap
entry point for all agents (Claude, Codex, Cursor, Gemini, Copilot).

## Quick Reference

- Workflows: `.ai_ops/workflows/`
- Agent files (Claude): `.claude/agents/` (generated — do not hand-edit)
- Local config: `.ai_ops/local/config.yaml` (gitignored)
- Work state: `.ai_ops/local/work_state.yaml` (gitignored)
- Sandbox: `90_Sandbox/ai_workbooks/`

## Build / Lint / Test

No compiled code. Governance is pure Markdown/YAML.

- Markdown lint: run from the repo with the `.pre-commit-config.yaml` that
  holds the markdownlint config. For this workspace: run from `re_stack/` root.
- YAML lint: `pre-commit run yamllint --all-files`
- Repo validator: `00_Admin/runbooks/rb_repo_validator_01.md`

## IMPORTANT

- Open-source repo. Never include proprietary content.
- Generated files in `.claude/agents/` — do not hand-edit. Use `/profiles`
  to modify source data, then regenerate.
- `AGENTS.md` is authoritative, not this file.
