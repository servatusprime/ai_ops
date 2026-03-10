---
title: Governed Repo Bootstrap Template
id: governed_repo_bootstrap_template
status: active
license: Apache-2.0
version: 0.1.0
created: 2026-03-10
last_updated: 2026-03-10
owner: ai_ops
description: >
  Starter checklist and file skeleton for onboarding a new governed repository
  under ai_ops governance.
---

<!-- markdownlint-disable MD013 -->
<!-- markdownlint-disable-next-line MD025 -->
# Governed Repo Bootstrap Template

## Purpose

Bootstrap a governed repository so cold-start agents can discover and apply
ai_ops governance with minimal ambiguity.

## Inputs

- target repo root: `<governed_repo_root>`
- ai_ops sibling root: `../ai_ops`
- selected validation policy: `ai_ops` or `repo_native`

## Output Surfaces

- `<governed_repo_root>/aiops.yaml`
- `<governed_repo_root>/AGENTS.md`
- `<governed_repo_root>/CONTRIBUTING.md`
- optional local runtime state under `<governed_repo_root>/.ai_ops/local/`

## Steps

1. Confirm sibling layout:
   - `<governed_repo_root>`
   - `../ai_ops`
2. Create `aiops.yaml` with repo-relative governance references:
   - `../ai_ops/AGENTS.md`
   - `../ai_ops/CONTRIBUTING.md`
   - optional bootstrap guide path under `../ai_ops/00_Admin/...`
3. Add lightweight governed `AGENTS.md`:
   - quick-start points to `aiops.yaml`
   - governance source is `../ai_ops/AGENTS.md`
   - work artifact lane is `90_Sandbox/ai_workbooks/`
4. Add `CONTRIBUTING.md` governance pointer:
   - reference `../ai_ops/CONTRIBUTING.md`
   - state cross-repo path contract:
     - use `../ai_ops/...`
     - do not use machine-local absolute paths
5. Run setup lane as needed for active surface:
   - from target repo, invoke `../ai_ops/.ai_ops/setup/setup_*` scripts with
     `--workspace` where applicable.
6. Record bootstrap evidence in active workbook/selfcheck.

## Validation Commands

```powershell
# Required governance pointers exist
Test-Path ../ai_ops/AGENTS.md
Test-Path ../ai_ops/CONTRIBUTING.md

# No machine-local absolute governance paths
rg -n "C:/RE_Projects|C:\\\\RE_Projects|C:/Users|C:\\\\Users|/Users/|/home/" AGENTS.md CONTRIBUTING.md aiops.yaml

# ai_ops governance references are repo-relative
rg -n -P "(?<!\\.\\./)ai_ops/" AGENTS.md CONTRIBUTING.md aiops.yaml
```

## Verification Checklist

- [ ] `aiops.yaml` created and path-valid
- [ ] governed `AGENTS.md` created with quick-start and contract notes
- [ ] governed `CONTRIBUTING.md` points to `../ai_ops/CONTRIBUTING.md`
- [ ] setup command evidence captured for active surface
- [ ] path-contract checks pass
<!-- markdownlint-enable MD013 -->
