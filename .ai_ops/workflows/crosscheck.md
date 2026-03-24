---
description: Conduct a structured peer review of work.
name: crosscheck
kind: workflow
version: 0.1.2
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
    short-description: Conduct a structured peer review of work.
  interface:
    display_name: crosscheck
    short_description: Conduct a structured peer review of work.
  policy:
    allow_implicit_invocation: true
exports:
  claude_plugin:
    enabled: true
    skill_name: crosscheck
  codex:
    enabled: true
    skill_name: crosscheck
  claude_project:
    enabled: true
    skill_name: crosscheck
---

<!-- markdownlint-disable MD013 -->
# /crosscheck

## Purpose

Conduct a structured crosscheck of work.

## Inputs and Preconditions

- Target artifact(s) or scope must be provided or confirmed.
- Review format (inline notes or review file) will be confirmed during execution if not specified.
- Review type must be selected: `design`, `mid_execution`, or `completion`.
- Review direction should be selected: `top-down`, `bottom-up`, or `hybrid`.
- Review strictness should be selected: `standard` or `strict`.
  - Default to `strict` for Level 3+ workbooks, governance scope, or 3+ target artifacts.
- If user asks for "audit-style" review, map to `strict + hybrid` unless user
  explicitly overrides direction.
- If inputs are insufficient or the request is illogical, pause and ask for clarification.

## Context Routing Hook

Use `00_Admin/configs/context_routing.yaml` as the canonical onboarding
contract.

1. Apply `commands._defaults.guard_profile` and `commands.crosscheck.guard_profile`.
2. Resolve onboarding tier in order: `fresh_bootstrap`,
   `resume_same_scope`, `recenter` (fallback `fresh_bootstrap` when state is
   unknown).
3. If routing resolved `resume_same_scope`, skip bootstrap rereads and keep
   current scope.
4. Apply bootstrap guard: if bootstrap requirements are missing or
   unverifiable, use `fresh_bootstrap` tier (read `AGENTS.md`) before review
   steps.
5. Load `always_read`; expand `read_on_demand` only when needed.
6. For review outputs, emit route metadata:
   `bootstrap_path`, `resume_basis`, and `reads_applied`.
7. If requested action is remediation/edit work, transition to `/work`.

## Decision Matrix (Cold-Start)

Use `00_Admin/guides/ai_operations/guide_workflows.md` for canonical
artifact-selection and execution-context matrices. This block covers only
review-local defaults and workflow-specific deltas.

### Decision Matrix - Inside (Maintainer)

- No active artifacts: ask for explicit review targets.
- Multiple active artifacts: ask which to review.
- Active workbundle/workprogram/workbook/runbundle/runprogram/runbook: confirm whether to limit review to that scope.
- Review direction defaults:
  - `design` review -> `top-down`
  - `mid_execution` review -> `top-down`
  - `completion` review -> `bottom-up`
  - Level 3+ workbook or governance scope -> `hybrid` (required)

### Decision Matrix - Governed External (Maintainer)

- Confirm governed target repo and active artifact path before review.
- Default to `hybrid` for Level 3+ workbook or governance reviews in the
  governed repo.
- Use repo-relative ai_ops governance references in findings, not machine-local
  absolute paths.
- If git is unavailable on the active surface, use the workbook's Ordered
  Execution Queue and evidence ledger for bottom-up coverage.

### Decision Matrix - External (User)

- No active artifacts: ask for explicit targets.
- Multiple active artifacts: ask which to review.
- Active user artifacts: confirm review scope and format.
- Default to `top-down` unless user asks for audit-style review.
- Audit-style review defaults to `strict + hybrid` unless user explicitly
  overrides direction.
- Use `bottom-up` for pre-commit gate checks.

## Steps

### Inside Repo (Maintainer)

<!-- markdownlint-disable MD029 -->
1. If routing resolved `resume_same_scope`, keep current target scope and skip
   bootstrap rereads.
2. If bootstrap requirements are missing or unverifiable, apply bootstrap
   guard: use `fresh_bootstrap` tier (read `AGENTS.md`) before review steps.
3. Ask which review style is requested: inline notes or review file.
   - **Default**: If unspecified, use **Review File** (non-destructive).
4. Ask for review type if not specified: `design`, `mid_execution`, or
   `completion`.
   - **Default**: `mid_execution`
5. If user requested audit-style review, set strictness to `strict` and
   direction to `hybrid` unless user explicitly overrides direction.
6. Ask for review direction if not specified.
   - **Default** by review type:
     - design or mid-execution -> `top-down`
     - completion -> `bottom-up`
   - **Override**: if scope is Level 3+ workbook or governance, use `hybrid`.
7. Use `01_Resources/templates/workflows/peer_review_template.md` for
   structured crosschecks.
8. Build an evidence ledger first (paths, line refs, command outputs) before writing findings.
9. Apply direction-specific passes:
   - **Top-down**: verify task completion and acceptance criteria.
   - **Bottom-up**: inventory changed files (staged + unstaged), map each file to authorized scope, flag untraced edits.
     If git is unavailable (for example `claude_app` surface), base the
     inventory on the workbook's Ordered Execution Queue and evidence ledger
     rather than staged diff.
   - **Hybrid**: run top-down first, then bottom-up, then reconcile discrepancies.
10. For workbook/runbook/spine/pipeline scope, run an execution-topology
    alignment pass:
    - verify `execution_topology`, `activated_lanes`, `delegation_policy`, and
      `convergence_profile` are present when required,
    - verify the `execution_topology_contract` matches the Ordered Execution
      Queue and delegated-step markers,
    - flag lane-declaration gaps (for example missing `Executor` on write
      phases or missing controlling-artifact freeze gates on derivative lanes).
11. For completion reviews in ai_ops or governed repos with
    `customizations.validation_policy.governed_mode: ai_ops`:
    - Run validator and include `VS025` results.
    - If target repo uses a different validator contract, report equivalent
      readiness signals instead of forcing `VS025`.
    - For each `VS025` warning, record disposition (intentional or oversight).
12. Run a cross-repo reference contract check on touched artifacts:
    - In `ai_ops` scope, flag concrete governed-repo names/paths as findings.
    - In governed-repo scope, verify ai_ops governance references are
      repo-relative and not machine-local absolute paths.
13. Classify each finding by enforcement type:
    - `code_enforced`
    - `doc_only`
    - `process_gap`
14. Mark each recommendation with disposition:
    - `patch_now` (in-scope and actionable)
    - `proposal_seed` (good idea, not yet authorized)
    - `follow_on_workbook` (approved next-lane execution)
15. Run an explicit **four-axis** review on all touched artifacts:

    **Clarity axis** — Can a cold-start agent follow inputs, steps, and outputs
    without inference? Are required paths explicit? Are ambiguous terms
    resolved? See `peer_review_template.md` `Clarity Pass (Cold-Start Read)`.

    **Thrift axis** — Is each change purposeful with no bloat? Thrift is not
    minimalism. Thrift is efficiency — the minimum cost to achieve the
    required outcome. (See `guide_ai_ops_vocabulary.md` for definition.) See
    `peer_review_template.md` `Thrift Pass`.

    **Context axis** — Is context placed as far **downstream** as practical?
    Operational detail belongs near the consumer, not in upstream governance
    files. Check for upstream context that should be pushed downstream. See
    `peer_review_template.md` `Context Pass (Downstream Placement)`.

    **Governance axis** — Are governance rules placed as far **upstream** as
    practical? Policy, authority gates, and enforcement rules belong in specs,
    policies, and upstream guides — not duplicated in downstream operational
    docs. Check for downstream governance that should be consolidated upstream.
    See `peer_review_template.md` `Governance Pass (Upstream Placement)`.
16. Run a streamlining pass on touched docs:
    - identify avoidable internal cycle burden (extra read hops/retracing),
    - confirm moved content has explicit landing zone,
    - confirm no dead references were introduced.
17. For workbook/workbundle/workprogram scope, run a placement/shape pass:
    - verify whether the current body of work still fits the chosen control
      artifact,
    - flag unnecessary sibling workbook/workbundle proliferation as
      `process_gap`,
      - recommend consolidation or workprogram escalation when thresholds are
      crossed.
18. Apply review timing patterns:
    - Design review: before implementation starts
    - Mid-execution review: at phase boundaries
    - Completion review: before closeout
19. If inline comments used, remove them before lint/commit.
<!-- markdownlint-enable MD029 -->

### External Repo (User)

1. Apply bootstrap guard before review steps.
2. If routing resolved `resume_same_scope`, continue without bootstrap rereads.
3. Ask which review style is requested.
4. Ask for review type if not specified (`design`, `mid_execution`,
   `completion`).
   - **Default**: `mid_execution`
5. If user requested audit-style review, use `strict + hybrid` unless user
   explicitly overrides direction.
6. Use simplified review structure (no workbundle context):
   - Summary of changes
   - Key observations
   - Recommendations
7. Do not reference ai_ops internal paths or templates.

## Outputs

- Review notes (inline) or review file (markdown), per user choice.
- Review file template precedence:
  - Direct/governed ai_ops lane: use `01_Resources/templates/workflows/peer_review_template.md`.
  - Standalone external lane: use repo-specific template if present.
  - Standalone external lane with no template: use simplified structure from
    External steps and do not reference ai_ops internal template paths.
- If review file and no repo convention exists: name it `review_<target>_<YYYY-MM-DD>.md`.
- Include direction in review context and include source-control traceability for `bottom-up` or `hybrid`.
- For `strict` reviews, include:
  - evidence citations for each finding (file:line or command output),
  - CSCC (cold-start, capacity-constrained) readiness table,
  - thrift + streamlining assessment for touched docs,
  - explicit verdict with blocking vs non-blocking items.

## Resources

- `00_Admin/guides/authoring/guide_ai_assistants.md` (inline note guidance)

## Lane

Default lane: Reviewer (review only). Use `Linter` only when the review is
explicitly limited to mechanical validation output.

## Risks and Limits

- If remediation or edits are requested, stop and transition to `/work` before changes.
- This is a structured review, not an exhaustive audit.
- Findings are scoped to provided artifacts and context.
- Do not expand scope or introduce new requirements without approval.
- Do not rely on `git diff --staged` only; use both staged and unstaged changes for bottom-up coverage.
- Do not leave inline comments in canonical documents.
- Do not require workbundle context in external repos.
- Do not assume command folders exist; if missing, read `.ai_ops/workflows/crosscheck.md` manually.
- Do not present speculative script names as mandatory fixes; label them as `proposal_seed` unless authorized.
- Do not mark checklist items as pass/fail without evidence.
