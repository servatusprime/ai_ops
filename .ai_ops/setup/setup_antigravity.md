---
title: Setup - Antigravity
version: 0.1.0
status: active
created: 2026-01-26
updated: 2026-01-26
owner: ai_ops
---

<!-- markdownlint-disable-next-line MD025 -->
# Setup: Antigravity

| Field | Value |
| --- | --- |
| Target Environment | Antigravity (Agent Manager) |
| Command Source | `.ai_ops/workflows/*.md` |
| Status | Native support (zero requirement) |

## Overview

Antigravity natively detects and exposes workflows defined in the `.ai_ops/workflows`
directory as "Slash Commands" in
the user interface. No external installation script or configuration file is required for this functionality to work,
provided the workflows are formatted correctly.

## Requirements

1. **Directory:** `.ai_ops/workflows/` should exist in the workspace root.
2. **Format:** Markdown files (`.md`).
3. **Frontmatter:** Must include a YAML frontmatter block with a `description` field.

### Example Workflow File

File: `.ai_ops/workflows/example.md`

```markdown
---
description: An example slash command to demonstrate native support
---

# /example

## Behavior

1. The agent acknowledges the command.
2. The agent performs the requested action.
```

## Setup Verification

To verify Antigravity support is active:

1. Open an Antigravity session.
2. Type `/` in the chat input.
3. **Expected:** A list of available commands (corresponding to files in
   `.ai_ops/workflows`) should appear.

## Maintenance

- **Adding Commands:** Create a new `.md` file in `.ai_ops/workflows`.
- **Updating Commands:** Edit the existing `.md` file. Changes are reflected immediately (or on next session start).
- **Removing Commands:** Delete the `.md` file.

## Troubleshooting

- **Command not showing:**
  - Check file extension is `.md`.
  - Verify YAML frontmatter is valid (no syntax errors).
  - Ensure `description` field exists.
