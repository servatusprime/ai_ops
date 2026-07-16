---
title: Future Work Scorecard
version: 0.1.0
status: active
updated: '2026-07-16'
source_registry: 00_Admin/backlog/future_work_registry.yaml
generated_by: 00_Admin/scripts/generate_future_work_scorecard.py
---

<!-- markdownlint-disable-next-line MD025 -->
# Future Work Scorecard

> Auto-generated. Do not edit manually; update the registry and regenerate.

<!-- markdownlint-disable MD013 -->
| ID | Title | Domain | Repo | Priority | Benefit | Effort | Readiness | Deferred Risk | Next Review |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fw_20260716_02 | Document R-6 and narrow VS035 active-state enforcement | validation | both | high | high | m | ready | high | 2026-08-01 |
| fw_20260716_03 | Make Director approval delegation efficient and measurable | governance | ai_ops | high | high | m | ready | high | 2026-08-01 |
| fw_20260216_01 | Protected-path authority evidence enforcement for workflow edits | governance | ai_ops | medium | high | m | partial | medium | 2026-03-01 |
| fw_20260227_04 | Bash equivalents for critical PowerShell setup scripts | operations | ai_ops | medium | medium | l | deferred | medium | 2026-04-01 |
| fw_20260504_01 | Subagent Budget Governance in Coordination and Director Protocols | governance | ai_ops | medium | medium | m | deferred | low | 2026-08-01 |
| fw_20260619_02 | Reduce git permission-prompt friction (atomic invocation convention + git rebase allowlist) | operations | both | medium | medium | s | ready | low | 2026-08-01 |
| fw_20260323_01 | Director Topology implementation | governance | ai_ops | medium | medium | l | partial | medium | 2026-08-15 |
| fw_20260716_01 | Advanced run-family version resolution and migration automation | tooling | both | medium | medium | l | deferred | low | 2026-10-15 |
| fw_20260125_01 | Audit event schemas for Emergency Autonomy | governance | ai_ops | low | low | s | deferred | low | 2026-03-01 |
| fw_20260227_03 | Add examples/ directory with sample artifacts | documentation | ai_ops | low | medium | m | deferred | low | 2026-04-01 |
| fw_20260227_07 | Review /work numeric scoring contract | governance | ai_ops | low | low | s | deferred | low | 2026-06-01 |
| fw_20260315_01 | Session-state infrastructure for context routing fast-path evaluation | integration | ai_ops | low | medium | xl | deferred | low | 2026-10-01 |
<!-- markdownlint-enable MD013 -->

## Notes

- Registry and scorecard should be updated together in the same change.
- Use `python ai_ops/00_Admin/scripts/generate_future_work_scorecard.py` after registry edits.
