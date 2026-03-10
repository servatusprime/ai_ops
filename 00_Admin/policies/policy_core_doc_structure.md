---
title: Core Document Structure Policy
version: 0.3.0
updated: 2026-02-15
status: active
license: Apache-2.0
---
<!-- markdownlint-disable MD025 -->

# Core Document Structure Policy

## Purpose

Define the required structure for core documents to keep Markdown consistent and AI-friendly.

## Coverage

This policy applies by default to:

- `00_Admin/policies/policy_*.md`
- `00_Admin/guides/guide_*.md`
- `02_Modules/**/docs/specs/spec_*.md`
- `02_Modules/**/docs/requirements_matrix_*.md`
- `02_Modules/**/docs/prompts/prompt_*.md`
- `00_Admin/backlog/plan_*.md`
- `00_Admin/runbooks/rb_*.md`
- `90_Sandbox/ai_workbooks/wb_*.md`

Consolidation-integrity requirements in this policy also apply repo-wide to
governed artifact types, including:

- documentation artifacts (policies, guides, specs, runbooks, workbooks),
- templates and prompt artifacts,
- structured config artifacts (YAML/JSON),
- implementation artifacts (for example scripts/code) when dedup/consolidation
  refactors are performed.

## Required Structure

```text
---
<YAML front matter>
---
H1: <Single H1 Title>
```

- No text or comments before the opening `---`.
- Exactly one H1 per document (no MD025 violations).
- Subsequent sections use `##`, `###`, etc.

## Consolidation Integrity Rule

When deduplicating or consolidating content across documents:

- Preserve nuance and detail from the source section(s); consolidation MUST NOT
  silently drop constraints, caveats, or edge-case guidance.
- Record a relocation map for each moved/removed section:
  `source_path:section -> destination_path:section`.
- Classify each consolidation decision as one of:
  - `pure_dedup` (safe remove; same meaning already present),
  - `consolidate_with_nuance` (merge required; preserve detail),
  - `warranted_duplication` (intentional duplication retained).
- Do not remove source content until destination content is present and the
  nuance-preservation check is complete.

## Opt-out

- To exempt a document, set `core_doc_exempt: true` in the front matter.
- Use this flag sparingly for special cases or very small docs.
