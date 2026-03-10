---
title: Policies Index
version: 1.0.0
status: active
license: Apache-2.0
created: 2026-01-13
updated: 2026-01-13
owner: ai_ops
description: Canonical list of policies in priority reading order
---
<!-- markdownlint-disable-next-line MD025 -->
# Policies Index

Policies are hard rules (MUST/MUST NOT) enforced by human judgment and code review.

## Reading Priority

Applicability labels:

- Required: all agents must know before acting
- Recommended: know before creating or modifying artifacts

Read policies in this order:

### Priority 1: Core Operations

1. `policy_naming_conventions.md` - File/folder/identifier naming rules [Required]
2. `policy_git_workflow_conventions.md` - Commit/branch/PR workflow [Required]
3. `policy_core_doc_structure.md` - Required Markdown structure [Required]

### Priority 2: Quality and Metadata

1. `policy_status_values.md` - Canonical status values [Required]
1. `policy_module_metadata_standards.md` - Module metadata requirements [Recommended]
1. `policy_requirements_management.md` - Requirements tracking [Recommended]

## Policy Characteristics

All policies:

- Use MUST/MUST NOT language (normative)
- Are enforced by human judgment
- Violations require context to evaluate
- Change via governance process
- Are versioned and track changes

## New Policies

To propose a new policy:

1. Create draft in `90_Sandbox/`
2. Document rationale and alternatives
3. Create workbook for policy addition
4. Requires human approval (Level 4 governance)

## See Also

- Specs: `00_Admin/specs/README.md` (technical requirements)
- Guides: `00_Admin/guides/README.md` (explanatory documentation)
- Contracts: `../<work_repo>/01_Resources/<domain_core>/contracts/` (machine-enforced specs)
