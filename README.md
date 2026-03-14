---
title: ai_ops
version: 0.3.1
status: active
license: Apache-2.0
last_updated: 2026-03-13
owner: ai_ops
description: AI-first governance layer for structured human-agent execution.
related:
  - HUMANS.md
  - AGENTS.md
  - CONTRIBUTING.md
---

<!-- markdownlint-disable MD013 MD025 -->

![ai_ops banner](01_Resources/images/branding/ai_ops-banner.png)

# ai_ops

<!-- @AI_AGENT: If you are an AI agent reading this, go to AGENTS.md. Do not read further. -->

**A governance layer for human-AI collaboration.**

## The problem

AI coding assistants are powerful but can drift in scope, context, and
traceability when work is not structured.

## The solution

ai_ops provides a governance layer for agents working across your
repos, enabling structured execution without losing control:

- authority-aware execution gates across any repo it governs
- durable, artifact-based context that survives session and agent handoffs
- built-in verification and review loops
- structured agent behavior — roles and model tiering calibrated to task scope

## Deployment model

ai_ops lives in its own repository and governs execution in your project repos.
Install it once; point it at any repo. Work artifacts, validation, and git
operations all happen in the target repo -- ai_ops stays clean. One ai_ops
install can govern multiple project repos simultaneously.

## What ai_ops Is / Is Not

ai_ops **is**:

- a governance and workflow layer for human-agent execution
- an artifact-first state model for resumable work
- a set of reusable workflow contracts with validation hooks

ai_ops **is not**:

- an AI model
- a replacement for your IDE or coding assistant
- a CI/CD system by itself
- a project code framework

## What ai_ops does

1. **Governs execution across any repo you point it at**
   - Work artifacts, validation, and git ops stay in the target repo.
   - Authority, scope, and verification gates apply consistently across all governed repos.
2. **Preserves work context across sessions and agents**
   - Work state is stored in repository artifacts, not chat memory.
   - *Work state belongs in the repository, not in the conversation. If it
     matters tomorrow, it must exist as a file today.*
3. **Gates actions by authority and scope**
   - Atomic work can be fast.
   - Multi-step and governance work requires explicit structure and approvals.
4. **Scales from small fixes to multi-phase programs**
   - Workbook -> Workbundle -> Workprogram progression.
   - Naming families: `workbook -> workbundle -> workprogram` and
     `runbook -> runbundle -> runprogram`.
   - Program artifacts are pipeline-level orchestration files over book/bundle artifacts.
5. **Builds verification into the workflow**
   - Selfcheck loops, crosschecks, and validator/runbook patterns reduce drift.
   - Eight named design tests must pass before any new artifact type or process
     is adopted. See [Design Tests](HUMANS.md#design-tests).
   - Every artifact is evaluated against four quality axes: Clarity, Thrift,
     Context, and Governance. See [HUMANS.md](HUMANS.md#axes-at-a-glance).
6. **Structures agent behavior through roles and profiles**
   - Four roles — Coordinator, Executor, Builder, Validator — cycle through
     every work session, single agent or multi-agent.
   - The authority and role framework guides agents to self-select the right
     model and approach per step: simpler models for bounded execution,
     higher-capability models for governance and crosschecks, escalation
     when scope is uncertain.
   - Rider archetypes tune working style independently of task; profiles are
     opt-in. See [HUMANS.md](HUMANS.md#agent-profiles-and-customization).

## Supported Platforms

ai_ops provides governance across multiple AI agent platforms from a single
install:

- Claude Code
- Codex
- Cursor
- Gemini CLI
- GitHub Copilot

Setup scripts for Claude Code, Codex, Cursor, and Gemini CLI are in
`.ai_ops/setup/`. GitHub Copilot uses `.github/copilot-instructions.md` for
repo instructions and, on supported surfaces, can also read project skills from
`.claude/skills/` or `.github/skills/`. ai_ops does not currently ship a
Copilot-specific installer; `setup_claude_skills.*` generates compatible
`SKILL.md` wrappers in `.claude/skills/`. See
[HUMANS.md](HUMANS.md#first-session-5-minutes) for platform-specific
installation.

## Start Here

| You are... | Start with |
| --- | --- |
| A human | [HUMANS.md](HUMANS.md) |
| An AI agent | [AGENTS.md](AGENTS.md) |
| A contributor | [CONTRIBUTING.md](CONTRIBUTING.md) |

Setup and operator onboarding are documented in
`HUMANS.md` and `.ai_ops/setup/README.md`.

## Folder Structure

Numbered prefixes provide deterministic scan order for AI agents.

| Folder | Purpose |
| --- | --- |
| `00_Admin/` | Policies, guides, specs, runbooks, configs |
| `01_Resources/` | Templates and shared references |
| `02_Modules/` | Reusable capabilities |
| `90_Sandbox/` | Active work artifacts |
| `99_Trash/` | Staged deletions and deprecated artifacts |

Detailed structure:
[guide_repository_structure.md](00_Admin/guides/architecture/guide_repository_structure.md)

## Commands

| Command | Purpose |
| --- | --- |
| `/work` | Start or resume a structured work session |
| `/work_status` | Summarize active work and blockers |
| `/work_savepoint` | Checkpoint current work without closeout |
| `/crosscheck` | Run structured review workflow |
| `/health` | Run report-only health checks |
| `/closeout` | Run validation and closeout steps |
| `/lint` | Run configured validators and linters (report-only) |
| `/harvest` | Consolidate and prune artifacts |
| `/scratchpad` | Create or continue session notes |
| `/customize` | Update preferences |
| `/profiles` | Manage rider/crew behavior profiles and regeneration |
| `/bootstrap` | Recenter context and readiness |
| `/ai_ops_setup` | Run setup helper for skills/wrappers |

Commands are user-facing names. Depending on tool surface, they are often
installed as skills or wrappers that dispatch to the same workflow files.

Recommended after `/ai_ops_setup`: run `/customize` to declare available models
and default reasoning preference, then `/profiles` for model-family behavior tuning.

If wrappers are unavailable, invoke `.ai_ops/workflows/<command>.md` when
available.
