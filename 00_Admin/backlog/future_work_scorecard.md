---
title: Future Work Scorecard
version: 0.1.0
status: active
updated: '2026-03-15'
source_registry: ai_ops/00_Admin/backlog/future_work_registry.yaml
generated_by: 00_Admin/scripts/generate_future_work_scorecard.py
---

<!-- markdownlint-disable-next-line MD025 -->
# Future Work Scorecard

> Auto-generated. Do not edit manually; update the registry and regenerate.

<!-- markdownlint-disable MD013 -->
| ID | Title | Domain | Repo | Priority | Benefit | Effort | Readiness | Deferred Risk | Next Review |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fw_20260227_01 | Set actual GitHub repository URL in plugin.json | operations | ai_ops | high | high | xs | blocked | high | 2026-03-01 |
| fw_20260228_01 | Standalone ai_ops root bootstrap artifacts for repo split | operations | ai_ops | high | high | m | ready | high | 2026-03-07 |
| fw_20260228_02 | Split-aware setup wiring for root config refresh and repo map trigger | tooling | ai_ops | high | high | m | partial | high | 2026-03-07 |
| fw_20260216_01 | Protected-path authority evidence enforcement for workflow edits | governance | ai_ops | medium | high | m | partial | medium | 2026-03-01 |
| fw_20260227_02 | Rename work_pause to work_savepoint with commit/push default | governance | ai_ops | medium | medium | s | ready | low | 2026-03-01 |
| fw_20260227_04 | Bash equivalents for critical PowerShell setup scripts | operations | ai_ops | medium | medium | l | deferred | medium | 2026-04-01 |
| fw_20260312_01 | Refresh GitHub Actions SHA pins in lint.yml | operations | ai_ops | medium | medium | xs | ready | medium | 2026-06-01 |
| fw_20260125_01 | Audit event schemas for Emergency Autonomy | governance | ai_ops | low | low | s | deferred | low | 2026-03-01 |
| fw_20260227_06 | Add HUMANS.md authority level to AGENTS.md path guard table | governance | ai_ops | low | low | xs | ready | low | 2026-03-01 |
| fw_20260227_03 | Add examples/ directory with sample artifacts | documentation | ai_ops | low | medium | m | deferred | low | 2026-04-01 |
| fw_20260227_05 | Remediation-lite workbook template variant | governance | ai_ops | low | low | s | deferred | low | 2026-05-01 |
| fw_20260227_07 | Review /work numeric scoring contract | governance | ai_ops | low | low | s | deferred | low | 2026-06-01 |
| fw_20260315_01 | Session-state infrastructure for context routing fast-path evaluation | integration | ai_ops | low | medium | xl | deferred | low | 2026-06-01 |
<!-- markdownlint-enable MD013 -->

## Notes

- Registry and scorecard should be updated together in the same change.
- Use `python ai_ops/00_Admin/scripts/generate_future_work_scorecard.py` after registry edits.
