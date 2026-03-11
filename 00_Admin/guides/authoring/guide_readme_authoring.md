---
title: Guide: README Authoring
version: 1.1.0
status: active
license: Apache-2.0
last_updated: 2026-02-26
owner: ai_ops
related:
  - ./guide_markdown_authoring.md
  - ../architecture/guide_naming_conventions.md
  - ../architecture/guide_repository_structure.md
  - ../ai_operations/guide_workflows.md
  - 00_Admin/specs/spec_repo_metadata_standard.md
---

<!-- markdownlint-disable-next-line MD025 -->
# Guide: README Authoring

This guide defines how to author README files in `<repo_name>` and formalizes
front matter expectations for root onboarding docs.

## Format Standard

README files in this repo are authored in Markdown and named `README.md`.

- Include YAML front matter at the top.
- Include a single H1 that matches the `title` in front matter.
- Follow lint and formatting rules from `guide_markdown_authoring.md`.

## Root Onboarding Doc Front Matter Standard

Use this baseline front matter profile for root onboarding docs:

- `README.md`
- `AGENTS.md`
- `HUMANS.md`
- `CONTRIBUTING.md`

Required fields:

- `title`
- `version`
- `status`
- `license`
- `last_updated`
- `owner`
- `description`
- `related`

Recommended usage rules:

- Keep `related` focused on onboarding/governance entrypoints only.
- Avoid environment- or deployment-specific links in root onboarding docs;
  place those in topical guides or setup docs.

## Minimal README Structure

Use this minimal structure unless a folder requires more detail:

1. Purpose: what the folder contains and why it exists
2. Scope: what is in and out of scope
3. Navigation: key subfolders or indexes
4. Notes: constraints or special handling

## Index Pattern

If a folder contains multiple peer documents, create a short index section
listing them in priority order. Use repo-relative paths for references outside
current folder.

## Exceptions

If a non-Markdown README is ever required, document the exception in:

- This guide
- `00_Admin/policies/policy_core_doc_structure.md` (if policy-level)

Do not introduce new README formats without documenting the decision.

## See Also

- `00_Admin/guides/authoring/guide_markdown_authoring.md`
- `00_Admin/guides/architecture/guide_repository_structure.md`
- `00_Admin/guides/architecture/guide_naming_conventions.md`
