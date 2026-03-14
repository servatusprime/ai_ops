---
title: Git Workflow (monorepo)
version: 0.1.1
status: active
updated: 2026-03-14
owner: ai_ops
license: Apache-2.0
---

# Git Workflow (monorepo)

## Purpose

Define the canonical commit/push workflow for humans and agents. This is the single source of truth; other docs should
link here rather than restating steps.

## Branches

- `main`: protected, deployable.
- `feature/<topic>`: short-lived; squash on merge.
- `hotfix/<issue-id>`: quick fixes.

## Tags

- `v0.1.0`, `v0.2.0`, when you version a deliverable.

## Commit/Push Steps (Required)

1. **Preflight**
   - Ensure working tree is understood: `git status -sb`.
   - Convert CRLF to LF for files you touched.
   - Check canonical Markdown for non-ASCII; replace with ASCII or document why it must remain.
   - Decide if this change set produced executed workbooks/workbundles (if no, skip Trash step).
   - Decide if repo structure changed (if no, skip structure map update).
2. **Lint**
   - Run `pre-commit run --all-files` (preferred) or the relevant linters listed in `CONTRIBUTING.md`.
   - Fix issues instead of disabling rules.
   - If `pre-commit` is environment-blocked (for example sqlite readonly/disk I/O), run equivalent direct checks
     (`markdownlint`, `yamllint`, `ruff`) and log the blocker + fallback in the commit/push log.
   - If the closeout scope includes local work artifacts under ignored
     `90_Sandbox/**` or `99_Trash/**` paths, run equivalent direct lint for
     those artifacts via temp-copy, stdin, or explicit ignore override; record
     the strategy and results in the workbook or commit/push log.
2a. **ACL/ACE Recovery (Conditional)**
   - Trigger only when git writes fail with lock/permission symptoms (for example:
     `Unable to create '.git/index.lock': Permission denied`).
   - Capture evidence before remediation:
     - `icacls .git`
     - exact failing command + error text
   - Run the ACL/ACE recovery script lane when available (future canonical script), then retry `git add`/`git commit`.
   - If recovery cannot be completed in-session, stop commit/push and record a blocker note in the active workbook and
     `00_Admin/logs/log_workbook_run.md`.
3. **Requestor Review Gate (Level 3+ Required)**
   - After validation, provide a change summary (files touched, key edits, validation results).
   - For Level 3+ changes, obtain explicit requestor approval before commit/push (staging is allowed).
   - For Level 4 changes, record approval in the Work Proposal and the execution workbook.
   - For Level 2 changes, use this gate when scope is non-trivial or the requestor asks.
   - Record approval in `00_Admin/logs/log_workbook_run.md`.
   - If the requestor uses the turbo marker from `rb_commit_push_streamlining_01.md`, proceed without pausing again for
     the same scope.
4. **Trash Executed Workbooks**
   - Before staging, move any executed workbooks, workbundles, and companion artifacts from `90_Sandbox/` to
     `99_Trash/` as required by `00_Admin/guides/authoring/guide_workbooks.md`.
   - Skip this step if no executed workbooks/workbundles were produced in the current change set.
   - After relocation, repair or document stale references in touched
     docs/indexes before staging.
5. **Update Repo Structure Maps**
   - Before running the generator, compare `<git_root>/repo_structure.txt` and
     `90_Sandbox/ai_external_context/files/repo_structure_reference.txt` against the current repo tree.
   - Agents MUST run `00_Admin/scripts/generate_repo_structure.ps1` as part of any commit/push request.
   - Humans SHOULD run the same step before staging when repo structure changes are expected.
   - In monorepo mode, `<git_root>` may be the workspace root. In split mode, `<git_root>` is the standalone repo root.
6. **Stage**
   - `git add -A` and re-check `git status -sb`.
7. **Commit**
   - If no message is provided, the agent selects a short scope-based message and logs it in
     `00_Admin/logs/log_workbook_run.md`.
   - `git commit -m "summary"`.
8. **Push**
   - `git push`.

## Commit/Push Log (Required)

Maintain a short entry in the rolling log:

- Log: `00_Admin/logs/log_workbook_run.md`
- For Level 3+ or approval-gated work, write or update the entry before commit
  so approval evidence, validation results, and final archived paths land in
  the shipped commit.
- After push, report shipped commit/branch details in chat. Add a second
  in-repo log update only when post-push metadata is required by repo policy or
  is materially useful.
- Include: skipped steps, lint failures encountered, fixes applied, and any remaining risks.
- Add **recommended fixes** that can be addressed now or logged as Future Work.
- If no workbook was executed, still log the commit/push entry in the same log.
- If the only change is adding the commit/push entry itself, no additional entry is required.

## Log Retention

- Keep the most recent 12-18 months of entries in active logs.
- Archive older entries annually to `99_Trash/`.

### Future Work Registry Rule

If you log a fix in `00_Admin/backlog/future_work_registry.yaml`:

- Search for similar entries first.
- If a match exists, append context to the existing item.
- Otherwise, add a new entry with `compacted_context` when a handoff is expected.

## PR Checklist

- Passes scripts (when added).
- Updates docs/specs if behavior changes.
