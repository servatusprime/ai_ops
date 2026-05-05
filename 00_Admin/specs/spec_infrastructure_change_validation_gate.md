---
title: Spec - Infrastructure Change Validation Gate
id: spec_infrastructure_change_validation_gate
module: admin
version: 0.2.0
status: active
license: Apache-2.0
created: 2026-02-24
updated: 2026-05-05
owner: ai_ops
owners: ["ai_ops"]
ai_generated: true
spec_archetype: governance_spec
description: Canonical validation gate contract for infrastructure-touching changes.
---

# Spec - Infrastructure Change Validation Gate

## Purpose

Standardize validation requirements for infrastructure-touching changes
(workflows, validators, scripts, routing configs, manifest schemas).

## Scope

Applies to workbook, runbook, workflow, script, validator, config, and manifest-schema changes
that touch ai_ops infrastructure or governed-repo infrastructure managed by ai_ops.

## Trigger Conditions

Run this gate when a change touches one or more of:

- `.ai_ops/workflows/**`
- `00_Admin/scripts/**`
- `00_Admin/configs/**`
- validator schema files

## Gate Checklist

1. **Affected Surface Inventory**
   - list touched infrastructure files
   - list declared dependent workbooks/runbooks
2. **Baseline Capture**
   - run pre-change validation commands
   - record pass/fail + notable warnings
3. **Post-Change Validation**
   - rerun same checks
   - compare regression signals
4. **Rollback Readiness**
   - define immediate rollback action
   - confirm rollback owner/trigger
5. **Closeout Evidence**
   - include commands and outcomes in workbook
   - include unresolved risks explicitly

## Minimum Required Commands

- `python 00_Admin/scripts/validate_repo_rules.py`
- `python 00_Admin/scripts/validate_workflow_frontmatter.py` when workflow sources are touched
- `python 00_Admin/scripts/run_release_quality_gate.py --dry-run`

## Pass Criteria

- no new high-severity validation regressions
- all required commands executed or explicitly blocked with workaround rationale
- rollback action documented

## Change Log

- 0.2.0 (2026-05-05): Metadata normalized to declare spec_archetype.
  Existing version history remains in Git history and prior frontmatter dates.
