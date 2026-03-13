# GitHub Copilot Instructions for ai_ops

This file is a lightweight entry point for Copilot surfaces that honor
repository instruction files. The canonical governance source remains
`AGENTS.md`.

## Start Here

- If you are acting as an AI agent, read `AGENTS.md` first.
- If the user is a human operator asking how to use ai_ops, route them to
  `HUMANS.md`.
- Treat `.ai_ops/workflows/*.md` as the source for ai_ops commands like
  `/work`, `/crosscheck`, `/health`, and `/closeout`.

## Operating Rules

- Determine mode first: direct mode in `ai_ops`, or governed mode in an
  external work repo.
- In governed mode, keep work artifacts, validation, and git operations in the
  target repo. ai_ops stays clean.
- Respect authority gates. Do not edit `AGENTS.md`, `CONTRIBUTING.md`,
  `.ai_ops/workflows/**`, `00_Admin/policies/**`, `00_Admin/specs/**`, or
  `00_Admin/configs/**` without explicit approval.
- Use artifact-based context for resumable work. If the work needs to survive
  the session, it must exist in files.

## Practical Use

- Prefer natural-language invocation such as "run `/work` for this repo" or
  "perform a `/crosscheck` review of this workbook".
- On supported Copilot surfaces, project skills may also be loaded from
  `.claude/skills/` or `.github/skills/`.
- If slash-command wrappers are unavailable, follow the matching workflow file
  manually from `.ai_ops/workflows/`.
- Keep repo-local conventions authoritative when ai_ops governs an external
  repo.

For broader setup and supported-surface details, see `README.md`, `HUMANS.md`,
and `.ai_ops/setup/README.md`.
