---
title: Guide: JSON Authoring
version: 1.0.0
status: active
license: Apache-2.0
last_updated: 2026-01-12
owner: ai_ops
related:
  - 00_Admin/guides/authoring/guide_yaml_authoring.md
  - 00_Admin/guides/authoring/guide_markdown_authoring.md
  - 00_Admin/guides/authoring/guide_python_authoring.md
  - 00_Admin/specs/spec_repo_metadata_standard.md
---

# Guide: JSON Authoring

## Purpose

Defines JSON authoring conventions for the repo. Used for configuration, manifests, AI agent payloads, and
structured outputs to ensure agents can reliably parse and produce JSON artifacts.

This guide defines the JSON authoring conventions for the `<repo_name>` repo. JSON is used for configuration, manifests,
AI agent payloads, and structured outputs. Consistency ensures agents (ChatGPT, Codex) can reliably parse and produce
JSON artifacts.

## 1. Baseline Rules

- Use 2 spaces for indentation.
- No tabs.
- UTF-8, LF newlines.
- No trailing commas.
- Boolean/literal case: true, false, null.
- Never include comments; JSON does not support them.
- End file with a final newline.

## 2. Ordering and Stability

- Sort keys alphabetically unless semantic order is required.
- AI-generators should output canonical sorted keys.
- Always use sort_keys=True in Python serialization.

## 3. Schema and Validation

- Prefer light JSON schema when necessary.
- Optional $schema references allowed.
- Versioned config should include a schema_version field.

## 4. Data Types and Formatting

- Datetimes must be ISO 8601 strings.
- Arrays should be vertically formatted when multi-line.
- Avoid embedding binary or base64.

## 5. Usage

- JSON is used for machine-oriented data, manifests, and agent payloads.
- JSON is not used for long-form metadata or templates.

## 6. Tooling

- Validate with python -m json.tool.
- Use IDE JSON extension.
