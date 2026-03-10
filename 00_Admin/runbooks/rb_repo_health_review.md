---
title: rb_repo_health_review
version: 0.5.2
status: active
license: Apache-2.0
last_updated: 2026-02-28
owner: ai_ops
related:
  - .ai_ops/workflows/health.md
  - 00_Admin/specs/spec_execution_orchestration.md
  - 00_Admin/specs/spec_governance_enforcement.md
  - 00_Admin/specs/spec_repo_metadata_standard.md
  - 00_Admin/specs/spec_repository_indices.md
  - 00_Admin/specs/spec_runbook_structure.md
  - 00_Admin/specs/spec_workbook_structure.md
  - 00_Admin/specs/spec_workflow_structure.md
---

<!-- markdownlint-disable MD025 -->

# Runbook: Repo Health Review

> **Note**: This runbook is model-agnostic. Agents must have **write access** to create the health report (and should
> only write the report artifact). For external repos, agents should adapt these checks to the target repo's own
> stated conventions.

## 1. Purpose

Verify that a repo is **healthy**: consistent with its own stated rules, free of cruft, and properly documented. Health
reviews catch drift before it becomes technical debt.

## 2. Cadence

Recommended triggers:

- **Periodic:** Every 4-6 weeks
- **After milestones:** Completion of a major feature or refactor
- **After structural changes:** New folders, renamed files, dependency updates

## 2.5 Scope Modes

Ask requestor: "Option 1 (Quick), Option 2 (Comprehensive), or Option 3 (Section Placement Audit)?"

| Mode                               | Scope                         | When to Use                                    |
| ---------------------------------- | ----------------------------- | ---------------------------------------------- |
| Option 1 (Quick)                   | Known categories, spot checks | Routine, CI/CD, targeted pain points           |
| Option 2 (Comprehensive)           | Full systematic scan          | Periodic reviews, post-milestone, first-time   |
| Option 3 (Section Placement Audit) | Section placement audit       | Placement tuning and architecture streamlining |

**Comprehensive Checklist (ai_ops):**

- [ ] Root: README.md, CONTRIBUTING.md, AGENTS.md, HUMANS.md
- [ ] Root configs: .editorconfig, .markdownlint.json, .prettierrc, ruff.toml, yamllint config (`.yamllint`)
- [ ] 00_Admin/policies/ (all files)
- [ ] 00_Admin/specs/ (all files)
- [ ] 00_Admin/guides/ (all subdirs: ai_operations, architecture, authoring)
- [ ] 00_Admin/runbooks/ (all files)
- [ ] 00_Admin/configs/ (validator, other)
- [ ] 00_Admin/logs/, reports/, research/, tests/, tooling/
- [ ] Optional: 01_Agents/ (README, metadata) when repo uses the pattern
- [ ] 01_Resources/templates/ (all templates)
- [ ] 02_Modules/ (module metadata, docs)
- [ ] 90_Sandbox/ai_workbooks/ (active workbundles)
- [ ] 00_Admin/scripts/ (scripts, utilities)
- [ ] .ai_ops/workflows/ (all command workflows)

Document selected scope in health report header. If dead chain analysis is run, include `dead_chain_depth` in the
header.

### 2.6 Output Location Resolution

Resolve output path in this order:

1. Requestor-provided output path.
2. Active workbundle/workbook for target repo.
3. Direct mode (`ai_ops`): `00_Admin/reports/health/`.
4. Governed/external mode with requestor-confirmed location: use that location
   (reports folder, sandbox, or inline-only).
5. Governed/external mode without requestor confirmation: do not write
   artifacts; return inline findings and ask for output location.

Always include the resolved output path in report metadata.

### 2.7 Option 3 Dedup Pattern

For Option 3 artifact bundles:

1. Inventory CSV is source of truth for row-level section verdicts/rationales.
2. Summary markdown should aggregate only (metrics/hotspots/lanes) and point
   to CSV.
3. Reorder map markdown should contain Pass B sequencing guidance only.
4. Do not duplicate full row-level inventory tables across summary/reorder
   artifacts.
5. Dedup moves must include canonical target and axis rationale.
6. Dedup moves must include nuance-retention evidence to avoid detail loss.

### 2.8 Option 3 Axes and Nuance Rule

For section placement and dedup in ai_ops:

1. Place governance content upstream (policy/spec/guide).
2. Place execution context downstream (workflow/template/runbook).
3. Treat overlap consolidation as semantic, not cosmetic:
   - identify nuance-bearing details in source sections,
   - preserve nuance in canonical destination,
   - flag unresolved nuance-loss risk before recommending moves.

### 2.9 Option 3 Artifact Bundle Contract

When Option 3 is selected, produce these artifacts (not inline-only output):

1. Summary report markdown:
   - `audit_<repo>_section_placement_<YYYY-MM-DD>.md`
2. Full section inventory CSV:
   - `audit_<repo>_section_placement_inventory_<YYYY-MM-DD>.csv`
3. Reorder map markdown (Pass B guidance):
   - `audit_<repo>_section_reorder_map_<YYYY-MM-DD>.md`

Template starters:

- `01_Resources/templates/documents/health/section_placement_audit_template.md`
- `01_Resources/templates/documents/health/section_placement_inventory_template.csv`
- `01_Resources/templates/documents/health/section_reorder_map_template.md`

Default target set (if requestor does not specify targets):

- active artifact + directly related governance files
- or requestor-scoped targets when provided

## 3. Health Check Categories

### 3.1 Self-Consistency

Verify the repo does what it says it does.

**Checks:**

1. **README accuracy:** Does README describe the actual project structure?
   - List top-level folders mentioned in README
   - Compare against actual folder structure
   - Flag mismatches (folders mentioned but missing, or present but undocumented)

2. **Convention compliance:** Are stated conventions being followed?
   - If README states naming conventions, verify files follow them
   - If CONTRIBUTING.md exists, check stated workflows match reality

3. **Config alignment:** Do config files match documented behavior?
   - Check if documented linters are actually configured
   - Verify CI/CD config matches stated workflows

### 3.2 Documentation Accuracy

Verify documentation is current and complete.

**Checks:**

1. **Dependency documentation:**
   - Compare package.json/requirements.txt/etc. against documented dependencies
   - Flag undocumented dependencies or documented-but-removed ones

2. **Ignore/config coverage:**
   - Check for common files that should be ignored (`node_modules`, `.env`, `__pycache__`, etc.)
   - Flag sensitive file patterns missing from ignore config.
   - In monorepo mode, allow config inheritance from `workspace_root` when
     documented in `AGENTS.md`.

3. **Setup instructions:** If README has setup steps, verify they reference existing files/scripts

4. **Architecture guide coverage (external repos only):**
   - If repo lacks analogs of **repository structure**, **naming conventions**, or **file placement** docs, flag as a
     documentation gap.
   - Recommend creating **only the minimal necessary guide** (usually repository structure first), and keep it short.
   - Trigger suggestion should appear in the health report, not auto-created.

### 3.3 Cruft Detection

Find dead weight in the repo.

**Checks:**

1. **Dead files:**
   - Files not imported/referenced anywhere
   - Empty files (except intentional .gitkeep)
   - Backup files (.bak, .old, ~files)

2. **Orphaned references:**
   - Imports pointing to non-existent files
   - Links in markdown pointing to missing targets
   - Config references to missing files

3. **Stale branches:**
   - Branches with no commits in 90+ days
   - Merged branches not deleted

4. **Deprecated artifacts:**
   - Files with `status: deprecated` in YAML frontmatter
   - Files in archive folders that should be removed
   - Superseded documents still in canonical locations

5. **Post-relocation stale-reference risk:**
   - If recent move/archive/delete actions occurred, run a focused stale-link
     check on touched docs/indexes.
   - Report any broken references as warnings with remediation stubs.

6. **Canonical placement conflict check:**
   - Detect duplicate artifacts serving the same role in different folders
     where a canonical location already exists.
   - Typical examples:
     - index-style guide in `00_Admin/guides/**` duplicating a canonical
       `README.md` index in an owning operational folder (`00_Admin/runbooks/`,
       `00_Admin/policies/`, `00_Admin/specs/`).
   - Classify as warning when both copies are active and diverge risk exists.
   - Remediation preference:
     1) keep canonical artifact,
     2) migrate any unique content,
     3) move duplicate to `99_Trash`.

### 3.4 Metadata Completeness

Verify required metadata is present.

**Checks:**

1. **Frontmatter:** Do markdown files have required YAML frontmatter fields?
   - Check for title, status, version where expected
   - Validate required field expectations against `00_Admin/specs/spec_repo_metadata_standard.md`

2. **Config files:** Are required config files present?
   - README.md at minimum
   - Ignore/lint config can be repo-local or inherited from `workspace_root`
     in monorepo mode
   - Project-specific configs as documented

### 3.5 Dead Chain Analysis

Identify specs/contracts with no operational trigger (dead chains).

**Entry points:** `.ai_ops/workflows/*.md` and `00_Admin/runbooks/*.md`

**Checks:**

1. **Direct triggers (depth 1, default):**
   - Scan entry points for references to specs/contracts
   - List specs/contracts NOT referenced from any entry point
   - Mark as **candidate dead chains** (informational only)

2. **Dead-chain strength lane (reference-only candidates):**
   - Identify artifacts with inbound references but no clear execution use case
   - Treat "mentioned only" references as weak triggers unless at least one of
     these exists:
     - selected/required in a command workflow (`.ai_ops/workflows/*.md`)
     - operationally selected from a runbook procedure
     - used by validator/lint/runtime contracts (`00_Admin/configs/validator/*`,
       scripts, or CI hooks)
   - Report these as **reference-only dead-chain candidates**
   - Recommend keep/document/use-case, or archive/trash as appropriate

3. **Transitive triggers (depth 2, optional):**
   - Follow entry points -> guides -> specs -> contracts
   - Requires explicit opt-in (higher token cost)
   - Document depth in report header
   - Escalate to warning only if still unreferenced at depth 2

**Report format:**

```markdown
### Dead Chains (depth: 1)

- spec_example.md -- no operational trigger from workflows/runbooks
  - **Fix stub:** Add reference from relevant runbook or deprecate

### Dead-Chain Strength (reference-only candidates)

- artifact_example.md -- referenced, but no clear execution trigger/use case
  - **Fix stub:** document executable use case, wire into workflow/runbook, or archive/trash
```

**Note:** Default depth is 1 (direct triggers only). Depth 1 results are
candidate signals; do not treat as defects without depth 2 confirmation.
Reference-only dead-chain strength findings are actionable in Option 2 when no
clear execution use case exists.

### 3.6 Governed Repo Validator Baseline (External Repos)

Apply this check when the target repo is governed by `ai_ops` (for example,
lists ai_ops governance in `AGENTS.md` workspace topology).

**Checks:**

1. Confirm these baseline artifacts exist:
   - `00_Admin/runbooks/rb_repo_validator_01.md`
   - `00_Admin/scripts/run_markdownlint.ps1`
   - `00_Admin/scripts/validate_repo_rules.py`
   - `00_Admin/configs/validator/validator_config.yaml`

2. Confirm commands are executable:
   - markdown lint script runs
   - validator script runs with local config

3. If missing, classify as warning or critical based on impact:
   - **Critical** when active workbooks require validation before execution.
   - **Warning** when no active execution work depends on it yet.

### 3.7 Option 3 Section Placement and Dedup Lane

When Option 3 is selected:

1. Inventory all headings in each target file (line + section level).
2. For each section, evaluate placement:
   - keep in current file,
   - move upstream (guide/spec/policy),
   - move downstream (workflow/template/runbook).
3. For sections that stay in-file, evaluate order:
   - keep position,
   - move up,
   - move down.
4. Detect duplicate/overlapping content clusters across interrelated files,
   including lexical-authority collisions (for example, glossary-style
   documents that restate canonical vocabulary definitions).
5. For each overlap cluster, select canonical destination using axes:
   - governance content upstream (policy/spec/guide),
   - execution context downstream (workflow/template/runbook).
6. Run nuance-retention check before proposing dedup moves:
   - capture detail/nuance points in source sections,
   - confirm canonical target preserves them,
   - flag nuance-loss risk.
7. Report section-level verdicts with rationale and a per-file summary.

### 3.8 Lock Preflight and Recovery Signals

Detect lock-prone execution conditions before recommending cleanup/remediation.

**Checks:**

1. Probe report output location and any high-churn artifact directories for
   move/rename/delete readiness.
2. If lock/permission blocks are detected, classify as:
   - `hard_lock` (cannot move/delete/rename),
   - `soft_lock` (temporary contention likely resolvable),
   - `policy_block` (insufficient permission or scope gate).
3. Record likely lock owner signals when observable (for example active writer
   process families).
4. Recommend archive-first/non-destructive fallback when hard locks persist.

**Report contract:**

- Include `lock_preflight_status` in report header.
- Include `lock_blockers` summary in findings when any hard lock is detected.

## 4. Execution Steps

1. **Bootstrap:** Read `AGENTS.md` to confirm repo structure and mode (Direct/Governed/Standalone).

2. **Run checks:** Execute each category's checks in order:
   - Self-consistency
   - Documentation accuracy
   - Cruft detection
   - Canonical placement conflict check
   - Metadata completeness
   - Dead chain analysis (if in scope)
   - Dead-chain strength lane (if in scope)
   - Lock preflight and recovery signals

3. **Classify findings:** Assign severity to each issue:
   - **Critical:** Broken functionality, security risk, missing essential files
   - **Warning:** Inconsistencies, outdated docs, minor cruft
   - **Info:** Suggestions, style improvements, optional cleanups

4. **Generate report:** Summarize findings with:
   - High-level health score (healthy / needs attention / unhealthy)
   - List of issues by severity
   - Recommended actions with effort estimates (S/M/L)
   - Compact fix stubs (1-3 bullets per issue) so another agent can expand into a full plan
   - For Option 3: produce artifact bundle (summary markdown + inventory CSV +
     reorder map markdown)
   - For Option 3: include overlap clusters, canonical target decisions, and
     nuance-retention results

5. **Output location:**
   - Use Section 2.6 resolution order.
   - Option 3 outputs should not be inline-only when output location is
     confirmed.
6. **Remediation handoff rule:**
   - `/health` remains read-only except report artifact generation.
   - If requestor wants fixes, stop health lane and transition to `/work`
     before canonical edits.

## 5. Report Template

```markdown
H1: Health Report: [Repo Name]

**Date:** YYYY-MM-DD **Status:** [Healthy / Needs Attention / Unhealthy]
**Target Repo:** `<repo_name>`
**Scope:** Option 1 (Quick) | Option 2 (Comprehensive) | Option 3 (Section Placement Audit)
**Dead Chain Depth:** 1 (default) | 2 (optional)
**Routing Profile:** `<profile_name>`
**Routing Fallback Used:** `true|false`
**Routing Fallback Reason:** `<reason|none>`
**Context Reset Applied:** `true|false`
**Scope Echo:** `<resolved scope summary>`
**Output Root Echo:** `<resolved output root|inline-only>`
**Exclusions Echo:** `<list|none>` (when applicable)
**Lock Preflight Status:** `pass | warning | blocked`

## Summary

[1-2 sentence overview]

## Findings

### Critical

- [Issue description] -- [file path]
  - **Fix stub:** [1-2 bullets with minimal steps]

### Warning

- [Issue description] -- [file path]
  - **Fix stub:** [1-2 bullets with minimal steps]

### Lock Blockers

- [Lock or permission blocker] -- [path]
  - **Type:** `hard_lock | soft_lock | policy_block`
  - **Fix stub:** [archive-first fallback, process-close request, or scoped escalation]

### Info

- [Issue description] -- [file path]
  - **Fix stub:** [1-2 bullets with minimal steps]

## Recommended Actions

| Priority | Action   | Effort | Impact       |
| -------- | -------- | ------ | ------------ |
| 1        | [Action] | S/M/L  | High/Med/Low |

## Fix Stubs (Compact)

For each issue above, provide a minimal fix stub (1-3 bullets) so another agent can expand into a full plan without
re-scanning the repo.
```

## 5.1 Metrics Output Contract

When entropy checks or seed-velocity reporting are in scope, include this
stable metrics table in the report:

| field_name | value | period | notes |
| --- | --- | --- | --- |
| `entropy_findings_count` | `<int>` | `<scope period>` | `<how counted>` |
| `seed_velocity_created` | `<int>` | `<scope period>` | `<seed source>` |
| `seed_velocity_actualized` | `<int>` | `<scope period>` | `<actualization source>` |
| `seed_velocity_ratio` | `<decimal>` | `<scope period>` | `actualized / created` |
| `recommended_actions_count` | `<int>` | `<current run>` | `<action list reference>` |

If a field is out of scope, set value to `not_applicable` and explain why in
`notes`.

## 5.2 Routing Metadata Echo Contract

For `/health` reports, include these metadata fields in the report header:

- `routing_profile`
- `routing_fallback_used`
- `routing_fallback_reason`
- `context_reset_applied`
- `scope_echo`
- `output_root_echo`
- `exclusions_echo` (when applicable)

## 6. Does Not

- Make changes to files (read-only)
- Make canonical remediation edits during `/health` (switch to `/work` first)
- Access network or external services
- Run destructive git operations
- Assume any specific folder structure in external repos

## 7. Option 3 Artifact Templates

For Section Placement Audit runs, use when available:

- `01_Resources/templates/documents/health/section_placement_audit_template.md`
- `01_Resources/templates/documents/health/section_placement_inventory_template.csv`
- `01_Resources/templates/documents/health/section_reorder_map_template.md`

## See Also

- `.ai_ops/workflows/health.md` - Command workflow
- `00_Admin/specs/spec_runbook_structure.md`
- `00_Admin/specs/spec_workbook_structure.md`
- `00_Admin/specs/spec_workflow_structure.md`
