---
name: lint
description: Run configured validators and linters against a target scope and report
  findings without modifying files.
kind: workflow
version: 0.2.1
status: active
owner: ai_ops
license: Apache-2.0
claude:
  argument-hint: '[target]'
  disable-model-invocation: true
  user-invocable: true
  allowed-tools: Read Grep Glob LS Bash
  model: null
  context: null
  agent: null
codex:
  metadata:
    short-description: Run validators and linters for a target scope.
  interface:
    display_name: lint
    short_description: Run configured lint checks without fixing files.
  policy:
    allow_implicit_invocation: false
exports:
  claude_plugin:
    enabled: true
    skill_name: lint
  codex:
    enabled: true
    skill_name: lint
  claude_project:
    enabled: true
    skill_name: lint
---

<!-- markdownlint-disable MD013 -->
# /lint

## Purpose

Run configured validators and linters against a target scope and return a
structured report without making changes.

## Inputs and Preconditions

- Target scope: file path, directory path, `all`, or `changed`.
- If target scope is omitted, ask for one before execution.
- If inputs are insufficient or the request is illogical, pause and ask for clarification.

## Context Routing Hook

Use `00_Admin/configs/context_routing.yaml` as the canonical onboarding
contract.

1. Apply `commands._defaults.guard_profile` and `commands.lint.guard_profile`.
2. Resolve onboarding tier in order: `fresh_bootstrap`,
   `resume_same_scope`, `recenter` (fallback `fresh_bootstrap` when state is
   unknown).
3. Load `always_read`; expand `read_on_demand` only when needed.
4. Emit report metadata: `bootstrap_path`, `resume_basis`, and `reads_applied`.
5. If requested action requires remediation edits, transition to `/work`.

## Decision Matrix (Cold-Start)

Use `00_Admin/guides/ai_operations/guide_workflows.md` for canonical
artifact-selection and execution-context matrices. This block covers only
lint-specific branching.

### Decision Matrix - Inside (Maintainer)

- No target specified: ask for scope (`file`, `directory`, `changed`, `all`).
- Target specified and configured validators found: run configured validators against scope.
- Target specified and configured validators not found: report available lint tools and offer fallback run.
- Findings present: return structured report and stop.
- No findings: return pass summary and stop.

### Decision Matrix - Governed (External Repo with ai_ops)

- Read `customizations.validation_policy.governed_mode` from `.ai_ops/local/config.yaml`.
- If `governed_mode: ai_ops`, read `governed_repo_validation` from `context_routing.yaml`
  and run the `minimum_commands` list for the target scope. Also read per-repo override
  from `.ai_ops/local/config.yaml`: find the entry in `workspace.work_repos` whose
  `path`, when resolved relative to the workspace root (parent directory of the ai_ops
  repo), matches the normalized `<target_repo>`. Absolute `path` values are compared
  directly; relative values (e.g. `my_project/`) are joined with the workspace root
  before comparing. Read the matched entry's `savepoint_validation` key.
  If no matching entry exists, record `validation_commands_run: []` and report.
  Do NOT claim the governed repo is lint-ready until at least one validator is confirmed
  discovered and run.
- If `governed_mode: repo_native`, detect and run the repo's configured validators/linters
  (`.markdownlint.json`, `.yamllint`, `ruff.toml`, `.pre-commit-config.yaml`).
  Require explicit confirmation that validator discovery succeeded before reporting pass.
- If policy is missing, ask and default to `ai_ops` only with confirmation.

### Decision Matrix - External (User)

- Ask for scope if missing.
- Run available linters for the repo.
- Return findings and suggested remediation path.

## Steps

### Inside Repo (Maintainer)

1. Apply bootstrap guard BRG-01: if bootstrap requirements are missing or
   unverifiable, apply `fresh_bootstrap` tier (read `AGENTS.md`) before lane
   steps.
2. Confirm target scope (`file`, `directory`, `changed`, or `all`).
3. Detect configured validators/linters:
   - `.markdownlint.json` or `.markdownlint.yaml` -> markdownlint
   - `.yamllint` or `.yamllint.yaml` -> yamllint
   - `ruff.toml` or `pyproject.toml` with `[tool.ruff]` -> ruff
   - `.pre-commit-config.yaml` -> pre-commit
   - `00_Admin/scripts/validate_repo_rules.py` -> repo validator
   - `00_Admin/scripts/validate_workflow_frontmatter.py` -> workflow frontmatter validator
   - `00_Admin/configs/validator/validator_config.yaml` -> validator config
4. Run each configured validator against the requested scope.
5. Collect results by validator:
   - status (`pass`/`fail`)
   - error count
   - warning count
   - file and line references
6. Report using the lint report format below.
7. Do not fix findings and do not edit files in this command lane.
8. If user requests fixes, transition to `/work` for remediation execution.

### Lint Report Format

```markdown
## Lint Report

**Target:** `<scope>`
**Timestamp:** `<ISO 8601>`

### Validators Run

| Validator | Status | Errors | Warnings |
| --- | --- | --- | --- |
| markdownlint | pass/fail | N | N |
| yamllint | pass/fail | N | N |
| ruff | pass/fail | N | N |
| repo-validator | pass/fail | N | N |
| workflow-frontmatter | pass/fail | N | N |

### Findings

#### [validator_name] - [severity]

- `<file_path>:<line>` - <description>

### Summary

- Total errors: N
- Total warnings: N
- Blocking: yes/no (errors > 0)
```

### External Repo (User)

1. **Repo-Root Resolution**: Resolve the target repository root before any lint operations.
   - Resolve `target_repo` from: explicit user scope → active artifact `repo` field → `.ai_ops/local/config.yaml` `workspace.work_repos` list.
   - **Explicit user scope**: an absolute path or workspace-relative path. Normalize to absolute path.
   - **Unregistered repos**: require explicit user-provided path if not resolvable. Stop and ask if none given.
   - **Windows**: normalize to forward-slash absolute path.
   - Run `git -C <target_repo> rev-parse --show-toplevel` to confirm repo access and establish `repo_root`.
     If it fails with `dubious ownership`, run `git config --global --add safe.directory <target_repo>` and
     re-run. Record `safe_directory_applied: true/false`.
2. Confirm target scope.
3. Read `customizations.validation_policy.governed_mode` from `.ai_ops/local/config.yaml` if governed mode applies.
4. Detect repo-native validation tools.
5. Run available checks per validation policy and report findings without applying fixes.
6. If fixes are requested, switch to a work lane for edits.

## Outputs

- Structured lint report with validator outcomes, findings, and blocking verdict.

## Lane

Default lane: Linter (read-only report lane).

## Risks and Limits

- `/lint` is report-only; it does not fix findings.
- Do not assume ai_ops validator scripts exist in external repos unless
  `customizations.validation_policy.governed_mode` is `ai_ops`.
- Do not mark repo as ready when required validators were not run.
- Do not mutate files from this lane.
- Do not assume command folders exist; if missing, read `.ai_ops/workflows/lint.md` manually.

## Resources

- `00_Admin/scripts/lint.ps1`
- `00_Admin/scripts/validate_repo_rules.py`
- `00_Admin/scripts/validate_workflow_frontmatter.py`

## Working with Native Commands

Use native assistant commands for session-scoped mechanics (model selection,
output formatting, local IDE helpers) when available.

Use ai_ops workflow commands for governed execution contracts, authority gates,
artifact handling, and validation/reporting behavior.

If overlap exists, native commands handle session mechanics while this workflow
remains the source of truth for governed process behavior.
