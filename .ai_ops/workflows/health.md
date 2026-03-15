---
description: "Run a repo health check\u2014verify the repo is consistent and clean."
name: health
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
    short-description: "Run a repo health check\u2014verify the repo is consistent\
      \ and clean."
  interface:
    display_name: health
    short_description: "Run a repo health check\u2014verify the repo is consistent\
      \ and clean."
  policy:
    allow_implicit_invocation: true
exports:
  claude_plugin:
    enabled: true
    skill_name: health
  codex:
    enabled: true
    skill_name: health
  claude_project:
    enabled: true
    skill_name: health
---

# /health

## Purpose

Run a repo health check and report issues with suggested fixes.

## Inputs and Preconditions

- None required; confirm target repo scope if unclear.
- If inputs are insufficient or the request is illogical, pause and ask for clarification.

## Context Routing Hook

Use `00_Admin/configs/context_routing.yaml` as the canonical onboarding
contract.

1. Apply `commands._defaults.guard_profile` and `commands.health.guard_profile`.
2. Resolve onboarding tier in order: `fresh_bootstrap`,
   `resume_same_scope`, `recenter` (fallback `fresh_bootstrap` when state is
   unknown).
3. Enforce BRG-01:
   if bootstrap requirements are missing or unverifiable, apply
   `fresh_bootstrap` tier (read `AGENTS.md`) before lane steps.
4. Load `always_read`; expand `read_on_demand` only when needed.
5. Apply `skip_unless_referenced` when configured.
6. Emit report metadata: `bootstrap_path`, `resume_basis`, and `reads_applied`.
7. If routing config is missing, use conservative fallback and record it in
   report metadata.

## Execution Gates (Mandatory)

Before running health checks:

1. Confirm the target repo unless it is already unambiguous in the request.
2. If multiple repos are in context, do not infer from current directory alone;
   ask the requestor to choose.
3. For external/governed targets, confirm output location before artifact
   writes (`reports`, `sandbox`, or `inline-only`).
4. Do not assume sandbox creation for external repos without requestor
   confirmation.
5. Run lock-preflight checks for report output targets and high-churn artifact
   directories; record lock status in findings (see
   `00_Admin/runbooks/rb_repo_health_review.md`).
6. Enforce `/health` write scope:
   - report artifacts only (in resolved output location),
   - no canonical workflow/runbook/guide/spec/template edits.
7. If remediation or edits are requested, stop and transition to `/work` before changes.

## Scope Options

Before running health checks, ask the requestor which scope they want. If they already stated a scope in the request,
confirm it and proceed:

> "Which health check scope would you like?
>
> - **Option 1 (Quick):** Targeted checks based on known categories. Faster, lower token cost.
> - **Option 2 (Comprehensive):** Systematic scan of entire repo with full checklists. Thorough but higher cost.
> - **Option 3 (Section Placement Audit):** Inventory sections and evaluate upstream/downstream placement plus in-file
>   section order. Highest cost; architecture-focused."

If scope is not specified, ask and wait for selection; do not default silently.

| Option                      | Scope                           | Use Case                                            |
| --------------------------- | ------------------------------- | --------------------------------------------------- |
| 1 (Quick)                   | Known categories, spot checks   | CI/CD gates, routine checks, known pain points      |
| 2 (Comprehensive)           | Full systematic scan, all files | Periodic reviews, post-milestone, first-time health |
| 3 (Section Placement Audit) | Section placement audit         | Placement tuning and streamlining                   |

Document the selected scope in the health report header. Include `dead_chain_depth` in the report header when dead chain
analysis is performed.

### Option 3: Section Placement Audit Mode

When Option 3 is selected, follow
`00_Admin/runbooks/rb_repo_health_review.md` and execute the full runbook
procedure (same pattern as Options 1 and 2).

## Decision Matrix (Cold-Start)

### Decision Matrix - Inside (Maintainer)

- Target repo stated + scope stated: confirm and proceed with health check.
- Target repo or scope missing: ask for both before running checks.

### Decision Matrix - External (User)

- Confirm target repo and stated rules.
- Scope not stated: ask which scope (Option 1, 2, or 3) and confirm repo/subpath before checks.
- Confirm output location preference (reports folder vs sandbox vs inline-only)
  before writing artifacts.

## Runbook Relationship

This workflow is a **summary**. The detailed procedure is in `00_Admin/runbooks/rb_repo_health_review.md`.

- **Primary Guide**: Use the **Workflow Steps below** as your primary trusted source.
- **Reference**: Only consult the full Runbook for edge cases or specific report formatting details not covered here.
- **Preflight Contract**: Lock preflight and recovery signals are defined in
  `rb_repo_health_review.md`.
- The steps below are a quick reference; defer to the runbook for report format and edge cases.

## Steps

### Inside Repo (Maintainer)

1. Read `AGENTS.md` to confirm inside ai_ops repo.
2. Confirm scope and (if needed) output location.
3. Execute the detailed procedure in
   `00_Admin/runbooks/rb_repo_health_review.md`.
4. Return findings with severity, fix stubs, route metadata, and lock-preflight
   results.

### External Repo (User)

1. Confirm working on requestor's repo, selected scope, and output location.
2. Read `customizations.validation_policy.governed_mode` from `.ai_ops/local/config.yaml`.
3. Execute the runbook procedure against the target repo's stated rules.
4. If governed mode baseline checks apply and `governed_mode: ai_ops`, run the
   validator readiness lane from the runbook.
4. Run scope-specific lanes on requestor-approved targets and produce artifacts
   only when output location is confirmed.
5. Return findings and recommended fixes, including lock-preflight status for
   any blocked cleanup/archive actions.

## Entropy Reduction Pass (Comprehensive Scope)

When scope is Option 2 (Comprehensive), run and report:

1. stale guidance candidates
2. dead references
3. template drift candidates
4. dead-chain strength candidates:
   - referenced artifacts with no clear execution trigger/use case
   - "reference-only" artifacts (mentioned in docs but not selected/required by a
     workflow, runbook, guide path, or validator contract)
5. canonical placement conflicts:
   - duplicate role artifacts where one canonical location is defined
   - index/README pairs that represent the same function in different folders
6. seed velocity snapshot:
   - seeds_created (period)
   - seeds_actualized (period)
   - velocity_ratio (`actualized / created`)

## Outputs

- Structured health report with recommended fixes.
- Summary of findings and proposed next steps.
- Include an explicit target-repo confirmation line in report header.
- Produce outputs/artifacts for the selected scope and write to the resolved
  output location per runbook guidance.
- If external output location is unconfirmed, return inline findings only and
  ask for location confirmation before artifact writes.
- Follow report contract/metrics formatting from
  `00_Admin/runbooks/rb_repo_health_review.md`.

## Roles

Default role: Validator (read-only check).

## Risks and Limits

- If remediation or edits are requested, stop and transition to `/work` before changes.
- Health checks report issues; they do not apply fixes without approval.
- Do not make changes to files (read-only check).
- Do not edit canonical governance/docs/templates during `/health`; use `/work`
  for remediation.
- Do not assume ai_ops folder structure in external repos.
- Do not apply ai_ops runbooks in external repos unless governed mode is active
  and `customizations.validation_policy.governed_mode` is `ai_ops`.
- Do not apply ai_ops rules in standalone external repos unless the requestor
  explicitly asks for governed-mode checks.
- Do not assume command folders exist; if missing, read `.ai_ops/workflows/health.md` manually.

## Follow-Up Actions

After presenting the health report, offer to help address issues:

- "Would you like me to create a plan to address these health issues?"
- If yes, propose specific actions for each issue category:
  - **Deprecated artifacts:** Move to archive or trash
  - **Dead files:** Delete or document why kept
  - **Stale branches:** Delete or explain retention
  - **Documentation gaps:** Draft updates

The health check itself is read-only; remediation is a separate step requiring
user approval and `/work` lane transition before canonical edits.

Health check categories and scoring criteria are defined in `00_Admin/runbooks/rb_repo_health_review.md`.

## Conversation Hygiene (Repo-Anchored)

When relevant, include a light chat/thread hygiene check in findings:

- Treat chats as disposable; repo artifacts remain source of truth.
- Apply archive test: if a thread vanished now, would repo still explain operation?
- Flag only ledger-worthy decisions (irreversible, cross-cutting, non-obvious rationale).
- Keep retained long-running threads minimal.
