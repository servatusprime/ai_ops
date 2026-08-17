---
title: Future Work Scorecard
version: 0.1.0
status: active
updated: '2026-08-17'
source_registry: 00_Admin/backlog/future_work_registry.yaml
generated_by: 00_Admin/scripts/generate_future_work_scorecard.py
---

<!-- markdownlint-disable-next-line MD025 -->
# Future Work Scorecard

> Auto-generated. Do not edit manually; update the registry and regenerate.

<!-- markdownlint-disable MD013 -->
| ID | Title | Domain | Repo | Priority | Benefit | Effort | Readiness | Deferred Risk | Next Review |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fw_20260726_01 | Runprogram wiring audit as a scoped health gate | validation | both | high | high | m | ready | high | 2026-08-15 |
| fw_20260716_02 | Document R-6 and narrow VS035 active-state enforcement | validation | both | high | high | m | ready | high | 2026-09-01 |
| fw_20260619_02 | Reduce git permission-prompt friction (atomic invocation convention + git rebase allowlist) | operations | both | medium | medium | s | ready | low | 2026-08-01 |
| fw_20260721_02 | Delegation capability parity and installed-surface verification | governance | ai_ops | medium | medium | m | partial | medium | 2026-08-15 |
| fw_20260721_03 | Remove Director-receipt dependency from run-family adoption handoff | governance | ai_ops | medium | medium | s | ready | medium | 2026-08-15 |
| fw_20260216_01 | Protected-path authority evidence enforcement for workflow edits | governance | ai_ops | medium | high | m | deferred | medium | 2026-10-01 |
| fw_20260227_04 | Bash equivalents for critical PowerShell setup scripts | operations | ai_ops | medium | medium | l | deferred | medium | 2026-10-01 |
| fw_20260504_01 | Bounded subagent budget guidance for discretionary delegation | governance | ai_ops | medium | medium | m | deferred | low | 2026-10-01 |
| fw_20260803_01 | VS035 work-family status-integrity adoption and evolution | validation | both | medium | medium | m | partial | low | 2026-10-01 |
| fw_20260817_03 | Validator coverage for duplicate project layers (same name, new id) | validation | governed_repo | medium | high | s | ready | medium | 2026-10-01 |
| fw_20260716_01 | Advanced run-family version resolution and migration automation | tooling | both | medium | medium | l | deferred | low | 2026-10-15 |
| fw_20260125_01 | Audit event schemas for Emergency Autonomy | governance | ai_ops | low | low | s | deferred | low | 2026-10-01 |
| fw_20260227_03 | Add examples/ directory with sample artifacts | documentation | ai_ops | low | medium | m | deferred | low | 2026-10-01 |
| fw_20260227_07 | Review /work numeric scoring contract | governance | ai_ops | low | low | s | deferred | low | 2026-10-01 |
| fw_20260315_01 | Session-state infrastructure for context routing fast-path evaluation | integration | ai_ops | low | medium | xl | deferred | low | 2026-10-01 |
| fw_20260803_02 | Governed-repo workbook front-matter YAML hygiene | documentation | governed_repo | low | medium | m | ready | medium | 2026-10-01 |
| fw_20260817_01 | Resolve custom-draw-order two-owner conflict (retheme_project_qgz.py vs apply_canonical_draw_order.py) | tooling | governed_repo | low | medium | s | deferred | low | 2026-11-01 |
| fw_20260817_02 | Stable atlas-controller layer id in build_project_layouts.py | tooling | governed_repo | low | medium | m | deferred | medium | 2026-11-01 |
| fw_20260817_04 | Dead group-comparison branch in build_project_layouts.py's patch_startup_state | tooling | governed_repo | low | low | s | deferred | low | 2026-11-01 |
<!-- markdownlint-enable MD013 -->

## Notes

- Registry and scorecard should be updated together in the same change.
- Use `python ai_ops/00_Admin/scripts/generate_future_work_scorecard.py` after registry edits.
