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

- Markdown lint: ai_ops has its own `.pre-commit-config.yaml` and
  `.markdownlint.json` at its repo root; run
  `pre-commit run markdownlint --files <paths>` from the `ai_ops/` repo
  root for ai_ops files. Do not run from `re_stack/` root for ai_ops
  content -- that root's config applies to `re_stack/` files, not this
  repo's.
- YAML lint: `pre-commit run yamllint --all-files`
- Repo validator: `00_Admin/runbooks/rb_repo_validator_01.md`

## IMPORTANT

- Open-source repo. Never include proprietary content.
- Generated files in `.claude/agents/` — do not hand-edit. Use `/profiles`
  to modify source data, then regenerate.
- `AGENTS.md` is authoritative, not this file.
