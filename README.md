---
title: ai_ops
version: 2.6.0
status: active
license: Apache-2.0
last_updated: 2026-03-03
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

ai_ops provides an execution structure that helps teams work with AI agents
without losing control:

In practice, ai_ops serves as an AI workflow operating system across governed
repositories.

- authority-aware execution gates across any repo it governs
- durable, artifact-based context that survives session and agent handoffs
- built-in verification and review loops

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

## Start Here

| You are... | Start with |
| --- | --- |
| A human | [HUMANS.md](HUMANS.md) |
| An AI agent | [AGENTS.md](AGENTS.md) |
| A contributor | [CONTRIBUTING.md](CONTRIBUTING.md) |

Setup and operator onboarding are documented in
`HUMANS.md` and `.ai_ops/setup/README.md`.

## Folder Structure

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

## Quick References

- Guides: [00_Admin/guides/README.md](00_Admin/guides/README.md)
- Policies: [00_Admin/policies/README.md](00_Admin/policies/README.md)
- Vocabulary: [guide_ai_ops_vocabulary.md](00_Admin/guides/ai_operations/guide_ai_ops_vocabulary.md)
- Design tests: [HUMANS.md](HUMANS.md)
