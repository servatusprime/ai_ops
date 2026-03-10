---
title: secrets_config_readme
version: 0.1.0
status: active
license: Apache-2.0
owner: ai_ops
created: 2026-02-25
updated: 2026-02-25
---

# secrets

## Purpose

Reserved location for local secret configuration artifacts that some scripts or
runbooks may expect by path.

## Rule

- Never commit real secrets.
- Keep only placeholders or local-only files that are ignored by git.

## Trigger

Use this folder only when a workflow requires secret material on disk (for
example local API keys or database credentials) and no safer system secret
store is available.

Prefer OS secret stores and environment variables over files when possible.
