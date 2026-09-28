---
title: Guide: Markdownlint Handling
version: 0.2.0
status: active
license: Apache-2.0
last_updated: 2026-09-25
owner: ai_ops
related:
  - ../authoring/guide_markdown_authoring.md
  - ../../runbooks/rb_repo_validator_01.md
---

# Guide: Markdownlint Handling

## Purpose

Define consistent markdownlint execution and exception handling.

## Standard Execution

- Use repo script when available (`run_markdownlint.ps1`).
- Lint changed paths first; run full pass when requested.

## Offline Pinned Tool Renewal

`00_Admin/scripts/lint.ps1` pins the Node executable, Markdownlint CLI entry
point, Markdownlint package metadata, and package version. A mismatch stops lint
with an error. Do not update these pins from an automatic package refresh or
from an unreviewed working directory.

When a legitimate tool update is needed:

1. Stage the candidate Node and Markdownlint installation from an independently
   trusted, approved offline source outside the repository. Retain the current
   binaries and package directory so the previous pins can be restored.
2. Record source provenance, Node version, Markdownlint version, and vendor
   checksums or signatures available for the candidate artifacts. Do not run
   package installation or network fetches from the repository lint workflow.
3. Inspect the candidate package metadata and entry point. Capture SHA-256 for
   the Node executable, `markdownlint.js`, and `package.json`; verify that the
   reported package version matches the version to be pinned. Review package
   dependency changes before promoting the candidate installation.
4. Update the four pin values together in `lint.ps1`. Keep the previous values
   in the renewal receipt with the candidate values and the source provenance.
5. Run a scoped Markdown lint, full `lint.ps1 -NoFix`, and the default
   `run_release_quality_gate.py` from a clean or isolated validation checkout.
   The latter runs lint as a required check. Stop if any check fails; restore
   the previous pins and tool artifacts if the candidate is rejected.
6. Record the validation result and resulting hashes in the active workbook or
   release-quality evidence. Do not silently replace a pin to clear a mismatch.

The pins guard the listed executable and package files; the locally installed
package dependency tree still depends on the reviewed installation provenance.
The renewal receipt should record the complete installed package inventory and
hashes even though the current script does not hash every dependency file.

Routine read-only Git inspection across repositories can run from the target
repository working directory using `git status`, `git diff`, and `git log`.
The settings contract keeps `git -C` prompting because command-text rules
cannot reliably distinguish all harmless reads from chained or mutating forms.
No broader interpreter or shell allowance is introduced by this guide.

## Failure Handling

- Fix rule violations in scope.
- If tooling environment fails (for example pre-commit cache permission issue),
  use direct `markdownlint` CLI fallback.
- Record fallback usage in workbook evidence.

## Exception Policy

- Prefer content fixes over disables.
- Use narrow rule-disable blocks only when necessary and justified.
- Avoid file-wide disables for new artifacts.
