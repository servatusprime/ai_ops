---
title: Environment Variables Template
version: 1.0.0
status: active
license: Apache-2.0
owner: ai_ops
created: 2026-01-12
updated: 2026-02-26
---

# Environment Variables

## Purpose

Document repo-relevant environment variable expectations without storing machine-specific values.

## New User Setup

1. Copy the example env file (e.g., `db.local.example.env`) to `db.local.env` in the same folder or your preferred local
   path.
2. Fill in machine-local values.
3. Keep local env files out of git (see workspace `.gitignore`).

## Trigger

Use this pattern when:

- setting up a new local machine for repo scripts that rely on env variables
- onboarding a new contributor who needs a safe example baseline
- introducing a new repo-level variable that should be documented for everyone

Do not use this folder to store personal machine snapshots or secrets.

## Repo Rule

- Track examples and documentation only.
- Do not commit real credentials, hostnames, or machine-specific paths.
- Use `*.local.env` for machine-local env files and keep them out of git.

## Typical Variables

Customize this section for each repo:

- `<REPO>_ROOT`: local workspace root path (machine-local, not committed)
- Any tool-specific connection variables (host, port, database, user, password)
- Tool binary paths if not on PATH

## Gitignore Pattern

Add the following to your repo `.gitignore`:

```gitignore
# Local env files -- machine-specific, never commit
*.local.env
!*.local.example.env
```
