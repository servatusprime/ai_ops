---
title: Security Policy
status: active
license: Apache-2.0
owner: ai_ops
---

<!-- markdownlint-disable MD013 -->

# Security Policy

## Supported Versions

ai_ops is governance tooling, not a runtime service. All releases on the
`main` branch are considered current. There are no versioned releases with
separate support windows at this time.

## Reporting a Vulnerability

**Do not report security vulnerabilities via public GitHub issues.**

To report a vulnerability, use one of the following:

- **GitHub private vulnerability reporting** (preferred): navigate to the
  Security tab of the repository and select "Report a vulnerability."

Please include:

- A description of the issue and its potential impact.
- Steps to reproduce or a minimal proof-of-concept.
- Any suggested mitigations, if known.

## Expected Response

- **Acknowledgement**: within 5 business days.
- **Triage and initial assessment**: within 10 business days.
- **Resolution or workaround**: timeline communicated after triage.

## Scope

This project is a governance and workflow framework for AI agents. Security
issues that are in scope include:

- Workflow instructions that could cause an agent to exfiltrate credentials
  or sensitive data.
- Validator or script logic that executes arbitrary user-supplied input.
- Configuration patterns that bypass intended authority controls.

Out of scope: issues specific to the AI models or agent runtimes themselves
(Claude, Codex, Gemini, etc.). Report those to the respective providers.

## Contact

Maintainer: `@servatusprime` on GitHub.
