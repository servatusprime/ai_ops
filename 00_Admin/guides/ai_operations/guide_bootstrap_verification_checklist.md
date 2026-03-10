---
title: Guide: Bootstrap Verification Checklist
version: 0.1.0
status: active
license: Apache-2.0
last_updated: 2026-01-21
owner: ai_ops
related:
  - 00_Admin/guides/ai_operations/guide_ai_operations_stack.md
  - 00_Admin/guides/ai_operations/guide_ai_ops_vocabulary.md
  - 00_Admin/guides/architecture/guide_bootstrap_algorithm.md
  - ../../../CONTRIBUTING.md
  - ../../../AGENTS.md
---

# Guide: Bootstrap Verification Checklist

## Purpose and Scope

This checklist verifies that an agent has successfully completed bootstrap and understands the repository's governance
model before executing Level 3+ authority work.

**When Required:**

- **Level 3+ work** (workbooks, 6+ file changes, multi-layer modifications) - REQUIRED
- **Level 2 work** touching governance, schemas, or templates - RECOMMENDED
- **First-time repository access** - RECOMMENDED

**When Not Required:**

- Level 0 (read-only) work
- Level 1 (single atomic edit) in pre-authorized paths

## Bootstrap Verification Checklist

Complete this checklist before executing Level 3+ work. If any item is unchecked, review the corresponding
documentation before proceeding.

### Authority Model Understanding

- [ ] **I understand the 5 authority levels (0-4)** and can identify which level applies to my current task
  - Level 0: Read-only (always allowed)
  - Level 1: Single atomic edit (pre-authorized if in scope)
  - Level 2: 2-5 related changes (confirm first)
  - Level 3: 6+ changes, multi-layer work (workbook required)
  - Level 4: Governance changes (human approval required)
- [ ] **I can use the decision tree** in CONTRIBUTING.md to determine the correct authority level
- [ ] **I know when to create a workbook** vs when to act directly (Level 3+ requires workbook)
- [ ] **I understand Level 4 restrictions**: policies, specs, and architecture require human approval

**Reference:** `CONTRIBUTING.md` sections "Agent Action Authority Levels" and "Agent Decision Tree"

### Canonical Vocabulary

- [ ] **I know the difference between these terms:**
  - Workbook: Single-run execution plan
  - Workbundle: Transient folder grouping workbook with companion artifacts
  - Workprogram: Multi-workbundle coordination container
  - Runbook: Reusable reference procedure
  - Contract: Machine-enforced interface spec
  - Policy: Hard rule (MUST/MUST NOT)
  - Spec: Technical requirement
  - Guide: Explanatory documentation
- [ ] **I can use these terms correctly** in logs, commits, and communication

**Reference:** `00_Admin/guides/ai_operations/guide_ai_ops_vocabulary.md`

### Repository Navigation

- [ ] **I know where to find:**
  - Policies: `00_Admin/policies/`
  - Specs: `00_Admin/specs/`
  - Guides: `00_Admin/guides/`
  - Templates: `01_Resources/templates/`
  - Modules: `02_Modules/`
  - Projects: `../<work_repo>/Projects/`
  - Sandbox (experimental): `90_Sandbox/`
  - Trash (deprecated): `99_Trash/`
- [ ] **I understand the difference** between canonical (00_Admin) and experimental (90_Sandbox) artifacts
- [ ] **I know that sandbox content** requires explicit promotion to become canonical

**Reference:** `00_Admin/guides/architecture/guide_repository_structure.md`

### Workflow Patterns

- [ ] **I understand the Intent/Commitment/Execution pattern** for work proposals
- [ ] **I know when to use Work Proposals** (Level 4 governance changes requiring approval)
- [ ] **I can distinguish** between workbooks (single-run) and runbooks (reusable)
- [ ] **I understand execution spines** and how they provide audit trails

**Reference:** `00_Admin/guides/ai_operations/guide_workflows.md`

### Self-Governance Rules

- [ ] **I know the pre-authorization rules:**
  - Single-file edits in module directories (Level 1)
  - Validation/lint commands after workbook approval (pre-authorized)
  - Logging steps after workbook approval (pre-authorized)
- [ ] **I understand the pause conditions:**
  - No valid target exists for the action
  - Write is outside approved scope
  - Ambiguous requirement needs clarification
- [ ] **I know the Self-Review Smoke Pass requirements:**
  - Required for Level 3/4 work before validation
  - Checks: terminology alignment, interface clarity, recovery paths, artifact completeness, scope integrity, bootstrap
    verification

**Reference:** `CONTRIBUTING.md` section "Agent Handshake and Pre-Authorization"

## Verification Result

After completing the checklist:

- **All items checked**: Proceed with Level 3+ work
- **Some items unchecked**: Review corresponding documentation and re-verify
- **Uncertain about any item**: Ask for clarification before proceeding

When complete, record a short confirmation signal in the session log or response, e.g., `[BOOTSTRAP: COMPLETE]`.

## Common Bootstrap Gaps

These are common issues that indicate incomplete bootstrap:

- **Authority confusion**: Proposing "implementation plan" instead of creating workbook
- **Vocabulary misuse**: Using "wizard" or "CLI-only" instead of AI-first terms
- **Location errors**: Creating files in 90_Sandbox/ when they belong in 00_Admin/
- **Scope creep**: Adding "quick wins" beyond approved workbook scope
- **Assuming authority**: Making governance changes without approval
- **Skipping verification**: Reporting "done" without running smoke pass or validation

If you catch yourself doing any of these, pause and re-verify bootstrap understanding.

## Integration with Workbooks

The workbook template (`01_Resources/templates/workflows/wb_template_generic.md`) includes bootstrap verification in
the Authority Self-Check section:

```markdown
## Authority Self-Check

- [ ] I am operating at the correct authority level for this work
- [ ] Scope is explicitly defined (what is in, what is out)
- [ ] Preconditions are clear and verifiable
- [ ] Verification criteria are defined
- [ ] I know what "done" looks like
- [ ] (Level 3+ only) I have confirmed my understanding of: authority model, canonical vocabulary, decision tree
```

This checklist serves as a detailed expansion of that final item.

## Maintenance

This checklist should be updated when:

- Authority levels are modified
- New canonical vocabulary terms are added
- Repository structure changes significantly
- New workflow patterns are introduced
- Bootstrap failures reveal gaps in verification

Record significant updates in `00_Admin/logs/` with appropriate log entry and bump the version number.
