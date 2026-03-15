---
description: Initialize agent context by reading repo entry point and instructions.
name: bootstrap
kind: workflow
version: 0.1.3
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
    short-description: Initialize agent context by reading repo entry point and instructions.
  interface:
    display_name: bootstrap
    short_description: Initialize agent context by reading repo entry point and instructions.
  policy:
    allow_implicit_invocation: true
exports:
  claude_plugin:
    enabled: true
    skill_name: bootstrap
  codex:
    enabled: true
    skill_name: bootstrap
  claude_project:
    enabled: true
    skill_name: bootstrap
---

# /bootstrap

## Purpose

Initialize agent context by reading the repo manifest and instructions, with
explicit anchoring for governed external repos.

## Inputs and Preconditions

- Target repo location (current repo or user-specified path).
- If external repo, confirm the repo root before proceeding.
- If inputs are insufficient or the request is illogical, pause and ask for clarification.

## Setup Readiness Contract (Mandatory)

`/bootstrap` is a readiness lane, not a setup lane.

- Read required setup contract version from `00_Admin/configs/setup_contract.yaml` `required_version`.
- Read local setup receipt from receipt path in `00_Admin/configs/setup_contract.yaml`
  (default: `.ai_ops/local/setup/state.yaml`) when present.
- Report one of:
  - `ready`: receipt version matches required version,
  - `setup_required`: receipt missing or version mismatch,
  - `setup_optional`: defaults are sufficient, but setup can still be run.
- If setup is required, route requestor to `/ai_ops_setup` with path-specific
  remediation details.
- Do not create local setup files from `/bootstrap`.

## Context Routing Hook

Use `00_Admin/configs/context_routing.yaml` as the canonical onboarding
contract.

1. Apply `commands._defaults.guard_profile` and
   `commands.bootstrap.guard_profile`.
2. Resolve onboarding tier in order: `fresh_bootstrap`,
   `resume_same_scope`, `recenter` (fallback `fresh_bootstrap` when state is
   unknown).
3. Enforce BRG-01:
   if bootstrap requirements are missing or unverifiable, apply
   `fresh_bootstrap` tier (read `AGENTS.md`) before lane steps.
4. Load `always_read`; expand `read_on_demand` only when needed.
5. Emit route metadata: `bootstrap_path`, `resume_basis`, and `reads_applied`.
6. If requested action requires canonical remediation edits, transition to
   `/work`.

## Pre-Flight Gates (Mandatory)

Before any filesystem exploration:

1. **Read order first:** Read `AGENTS.md` before any scans.
2. **No recursive scans:** Do not use recursive file/directory searches until intent is confirmed.
3. **Scan budget:** Limit initial exploration to manifest-declared paths only.
4. **Monorepo target confirmation:** When multiple repos exist in workspace, confirm target repo
   before reading files outside ai_ops.

Violation of these gates increases token cost and risks operating on wrong context.

## Mode Detection

Use the canonical Mode Detection contract in `AGENTS.md` to resolve
Direct/Governed/Standalone before continuing bootstrap.

Mode quick reference:

| Target                     | Mode           | Behavior                                      |
| -------------------------- | -------------- | --------------------------------------------- |
| ai_ops itself              | **Direct**     | Bootstrap ai_ops context                      |
| External repo in workspace | **Governed**   | Bootstrap with ai_ops + external repo context |
| No ai_ops reachable        | **Standalone** | Bootstrap from local repo context only        |

**Edge case:** If no `AGENTS.md` with ai_ops structure is reachable, fall back to **Standalone**
mode.

For target repo selection logic, see `/work` workflow.

## Decision Matrix (Cold-Start)

### Direct Mode (ai_ops)

- No active artifacts: complete bootstrap; note that no work context is available.
- Active artifacts: complete bootstrap; read contents of active workbundles/workprograms/workbooks.

### Governed Mode (External Repo)

- Context artifacts provided: use them as bootstrap inputs alongside ai_ops context.
- No context artifacts in external repo: bootstrap ai_ops context, then ask about external repo.

### Standalone Mode (No ai_ops)

- Context artifacts provided (README/CONTRIBUTING/AGENTS): use them as bootstrap inputs.
- No context artifacts: ask for a README or brief project summary before proceeding.

## Runbook Relationship

This workflow is a **summary**. The detailed procedure is in `00_Admin/runbooks/rb_bootstrap.md`.

- Read and follow the runbook for complete bootstrap steps.
- The steps below are a quick reference; defer to the runbook for edge cases.

## Bootstrap vs Work

- Use `/bootstrap` to establish context; use `/work` to start/resume tasks.
- `/work` triggers a lightweight bootstrap when context is missing.

## Steps

### Steps: Direct Mode

Use Direct mode only when explicitly requested or when `/work` cannot establish context.

1. Read `AGENTS.md` and confirm mode (see Mode Detection above).
2. Read `CONTRIBUTING.md` only when contributor policy, maintainer workflow, or
   authority ambiguity requires it.
3. Read and follow `00_Admin/runbooks/rb_bootstrap.md` for detailed steps:
   - Load workspace configuration from workspace topology block in AGENTS.md
   - Set authority level from context
   - Identify active work context from `.ai_ops/local/work_state.yaml` `work_context.active_artifacts`
     (absence of `work_state.yaml` = no active work; not an error — create from empty template if needed)
4. Run capability certification (optional, on request):
   - L1: Bootstrap awareness (can identify AGENTS.md and authority model)
   - L2: Repository navigation (can find key files)
   - L3: Operational patterns (understands workflows)
5. Evaluate setup readiness:
   - compare `required_version` from `00_Admin/configs/setup_contract.yaml` with local receipt
     version from `.ai_ops/local/setup/state.yaml` (or configured receipt path),
   - report readiness status and exact next action.
6. Confirm bootstrap complete with context summary.

### Steps: Governed Mode

1. Complete Direct mode steps 1-3 for ai_ops context.
2. Identify target external repo from `AGENTS.md` workspace topology `work_repos` (or `.ai_ops/local/config.yaml` if present).
3. Read external repo's context artifacts (README, CONTRIBUTING, AGENTS if present).
4. Read `customizations.validation_policy.governed_mode` from `.ai_ops/local/config.yaml`.
5. Confirm bootstrap complete with combined context summary and governed-mode validation policy.

### Steps: Standalone Mode

1. Confirm the external repo root.
2. Ask for available context artifacts (README, CONTRIBUTING, AGENTS).
   - **Default**: If no artifacts are found/provided, list root files and ask
     the requestor to confirm entry-point docs and repo purpose.
   - Do not infer repo purpose from file names or folder structure alone.
3. Read any provided context artifacts.
4. Confirm bootstrap complete with simplified context.

## Verification and Self-Repair Hook

After completing mode steps, run a quick integrity check:

1. Read-order compliance verified (`AGENTS.md` before broad scans).
2. Mode/target repo classification still coherent.
3. Active artifact path exists and is reachable.

If any check fails, stop and self-repair before proceeding:

- reload AGENTS.md and command context;
- restate mode and target repo to requestor;
- if ambiguity remains, pause and ask.

## Decision Matrix Self-Check

After completing bootstrap, verify you followed the correct path:

- [ ] I identified the correct mode (Direct/Governed/Standalone) before proceeding
- [ ] I read `AGENTS.md` before scanning the filesystem
- [ ] I did not infer repo purpose from file names or structure
- [ ] I checked `.ai_ops/local/work_state.yaml` `work_context.active_artifacts` for existing work (if Direct/Governed)
- [ ] I confirmed the target repo before reading its files (if Governed/Standalone)

If any item fails, pause and correct before continuing.

## Outputs

- Context summary and readiness confirmation.
- Optional capability certification result (if requested).
- Optional bootstrap report (if the user requests a written record).

## Resources

- `00_Admin/runbooks/rb_bootstrap.md` (bootstrap steps)
- `00_Admin/guides/ai_operations/guide_capability_certification.md`

## Roles

Default role: Coordinator (orientation and readiness).

## Risks and Limits

- Over-reading increases token cost; follow the manifest's read order only.
- Do not scan the filesystem on first turn (read manifest first).
- Do not invent repo summaries (use declared metadata only).
- Do not override user's existing configuration.
- Do not run certification checks in external repos (not applicable).
- Do not assume command folders exist; if missing, read `.ai_ops/workflows/bootstrap.md` manually.
