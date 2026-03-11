---
title: Guide: Markdown Authoring
version: 1.0.5
status: active
license: Apache-2.0
last_updated: 2026-02-18
owner: ai_ops
related:
- ../architecture/guide_naming_conventions.md
- ../architecture/guide_repository_structure.md
- 00_Admin/specs/spec_repo_metadata_standard.md
---

<!-- markdownlint-disable MD025 -->

# Guide: Markdown Authoring

This guide is the source of truth for writing Markdown in this repo. It aligns with our configured linters and editor
settings to keep docs readable and diffs clean.

## Lint Rules (Enforced)

### Structure

- When front matter is present, include exactly one H1 that matches the `title`, then use lower levels.
- Do not use bold text as a heading; use H2/H3 instead.
- Avoid duplicate headings within the same document; rename repeated sections.
- Keep headings semantic and durable. Avoid parenthetical suffixes (for example, `(Consolidated)`, `(Legacy)`,
  `(Draft)`) unless they add active disambiguation that a reader needs to execute the task correctly.

### Spacing

- Surround headings, lists, blockquotes, and fenced code with a blank line (MD022, MD032, MD031).
- No multiple consecutive blank lines (MD012).
- No trailing spaces; ensure a final newline (enforced via `.editorconfig`).

### Fences

- Always specify a language for fenced blocks (MD040). Examples: `yaml`, `json`, `bash`, `powershell`, `mermaid`, `text`
  (for ASCII diagrams).

### Line Length

- Wrap narrative prose at 120 characters (MD013). Do not wrap code blocks, tables, or long URLs.

### Lists

- Use `1.` for all ordered list items (MD029).

### EOL

- Line endings MUST be LF (`\n`) for Markdown files; convert CRLF to LF when touching files.

### Character Set

- Canonical Markdown SHOULD remain ASCII-only unless the file already uses non-ASCII characters.
- If non-ASCII is introduced in canonical docs, remove it before commit or document why it must remain.

## Prompts and Specs

- Prompts/specs should include YAML front-matter where useful (title, version, owner, status).
- After front matter, add a single H1 that matches the `title`; keep all other headings below H1.
- Prefer numbered headings for long, structured docs.
- Convert bare URLs to links when practical; long URLs may remain bare inside code blocks.

## Disables (Use Sparingly)

- Prefer narrow, block-scoped disables:
- `<!-- markdownlint-disable MD013 -->` ... `<!-- markdownlint-enable MD013 -->`
- Avoid file-level disables for new content; acceptable only for legacy files with a plan to remove.
- When disabling, add a brief note in a PR about why and when to revisit.

### MD029 Override Policy

- Default: use `1.` for all ordered list items.
- Only disable MD029 in legacy documents that cannot be reflowed safely.
- If you disable MD029, add a short inline note and scope the disable to the smallest block.

### Formatter Interaction (MD025)

If a formatter inserts a blank line between the disable comment and the H1, MD025 may still fail. Use a block-scoped
disable instead:

```markdown
<!-- markdownlint-disable MD025 -->

H1: Title

<!-- markdownlint-enable MD025 -->
```

This keeps lint clean without changing formatter settings. Only disable MD025 when the file still has a single, correct
H1.

## Templates & Examples

- Specification outline: `01_Resources/templates/documents/spec-template.md`
- Prompt drafting template: `01_Resources/templates/documents/prompt_spec_template.md`
- Requirements matrix: `01_Resources/templates/documents/requirements_matrix_template.md`

## Path References

- Use repo-relative paths for references in front matter (for example, `related:`) and in prose.
- Avoid bare filenames when the file is not in the same directory.
- If a reference is illustrative only, label it as an example and keep it inside a fenced block.

## Source of Truth

- Lint rules: `.markdownlint.json` (at the repo root)
- Lint exclusions: `.markdownlintignore`
- Editor defaults: `.editorconfig` and `.vscode/settings.json`
- Pre-commit hooks (optional but recommended): `.pre-commit-config.yaml`
- Commit/push steps and lint execution: `00_Admin/policies/policy_git_workflow_conventions.md`

## AI-generated File Content

- Emit one continuous fenced block per file when returning content in chat.
- Use a language hint for Markdown fences:

  ```markdown
  ## <!-- File: 00_Admin/policies/policy_naming_conventions.md -->

  ...
  ```

- The first line inside the fence SHOULD be an HTML comment with the intended path.
- Do not place narrative or commentary inside fenced blocks; keep commentary outside.
- Preserve core-doc structure: YAML front matter at top, followed by a single H1 matching the `title`.
- For multi-file responses, provide separate fenced blocks, each labeled with its path comment. See also:

- [policy_core_doc_structure.md](../../policies/policy_core_doc_structure.md)
- [policy_status_values.md](../../policies/policy_status_values.md)
- [policy_naming_conventions.md](../../policies/policy_naming_conventions.md)

### Common Pitfalls (Quick Fixes)

- MD013: reflow narrative text to <=120 chars; skip code, tables, and URLs.
- MD022/MD032: add a blank line before and after headings and lists.
- MD031/MD040: add blank lines around fences and specify a fence language.
- MD025/MD041: include one H1 that matches the `title`; avoid additional H1s.
- MD029: use `1.` for all ordered list items.

### Workflow Tips

- Use the IDE Markdownlint extension (recommended in `.vscode/extensions.json`) so issues surface inline while
  typing.

- If lint catches repeated headings across templated sections, rename them immediately (e.g., `### Phase 1 Tasks`) so
  future edits stay compliant.

- During dedup/consolidation edits, apply the policy rule in
  `policy_core_doc_structure.md`:
  - map source section -> destination section,
  - verify nuance/detail preservation before deleting source text,
  - mark decision type (`pure_dedup`, `consolidate_with_nuance`, or
    `warranted_duplication`) in the active workbook/review artifact.

## Blank Line Examples (MD031, MD032)

Use a blank line before and after lists:

```markdown
Paragraph introducing a list.

- Item one
- Item two

Next paragraph after the list.
```

Use a blank line before and after fenced code blocks:

````markdown
Paragraph introducing a code block.

```powershell
Get-ChildItem -Force
```

Next paragraph after the code block.
````

## Change Management

- Update this guide if you adjust `.markdownlint.json` or editor settings.
- Include a one-line summary of changes in the PR description.
- For draft promotion bundles, record section-level deltas in `DRAFT_INDEX.md`
  using `key_edits` and `reviewed_no_change` fields.
