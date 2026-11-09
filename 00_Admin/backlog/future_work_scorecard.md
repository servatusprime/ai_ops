---
title: Future Work Scorecard
version: 0.1.0
status: active
updated: '2026-11-09'
source_registry: 00_Admin/backlog/future_work_registry.yaml
generated_by: 00_Admin/scripts/generate_future_work_scorecard.py
---

<!-- markdownlint-disable-next-line MD025 -->
# Future Work Scorecard

> Auto-generated. Do not edit manually; update the registry and regenerate.

<!-- markdownlint-disable MD013 -->
| ID | Title | Domain | Repo | Priority | Benefit | Effort | Readiness | Deferred Risk | Next Review |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fw_20261015_01 | Add repository-contained outside-write detection to /health | validation | both | high | high | m | partial | high | 2026-11-15 |
| fw_20261026_01 | Enable governed-repo deterministic closeout admission or an explicit waiver path | workflow | ai_ops | high | high | m | ready | medium | 2026-11-15 |
| fw_20260716_02 | Document R-6 and narrow VS035 active-state enforcement | validation | both | high | high | m | ready | high | 2026-12-15 |
| fw_20260726_01 | Runprogram wiring audit as a scoped health gate | validation | both | high | high | m | ready | high | 2026-12-15 |
| fw_20261106_01 | Enforce factory/local profile output isolation before /profiles customization | tooling | ai_ops | high | high | m | partial | high | 2026-12-15 |
| fw_20260619_02 | Reduce git permission-prompt friction (atomic invocation convention + git rebase allowlist) | operations | both | medium | medium | s | ready | low | 2026-12-15 |
| fw_20260721_02 | Delegation capability parity and installed-surface verification | governance | ai_ops | medium | medium | m | ready | medium | 2026-12-15 |
| fw_20260721_03 | Remove Director-receipt dependency from run-family adoption handoff | governance | ai_ops | medium | medium | s | ready | medium | 2026-12-15 |
| fw_20260820_01 | Sweep and reconcile "packet"/work_packets terminology across ai_ops guides | documentation | ai_ops | medium | medium | m | blocked | medium | 2026-12-15 |
| fw_20260902_02 | Adjudicate validator warning-to-blocker policy for SEC-AIOPS-020 | validation | ai_ops | medium | high | m | partial | medium | 2026-12-15 |
| fw_20261104_01 | Apply the work-workflow simplification AGENTS.md handoff | governance | ai_ops | medium | medium | m | ready | medium | 2026-12-15 |
| fw_20261104_02 | Align the ai_role validator contract across ai_ops and governed repos | validation | both | medium | medium | m | ready | medium | 2026-12-15 |
| fw_20260216_01 | Protected-path authority evidence enforcement for workflow edits | governance | ai_ops | medium | high | m | deferred | medium | 2027-01-15 |
| fw_20260504_01 | Bounded subagent budget guidance for discretionary delegation | governance | ai_ops | medium | medium | m | deferred | low | 2027-01-15 |
| fw_20260716_01 | Advanced run-family version resolution and migration automation | tooling | both | medium | medium | l | deferred | low | 2027-01-15 |
| fw_20260831_01 | Define recoverable and disposable 99_Trash retention lanes | operations | both | medium | high | m | partial | medium | 2027-01-15 |
| fw_20261106_02 | Verify cited closeout receipt before active-artifact removal | validation | ai_ops | medium | high | m | deferred | medium | 2027-01-15 |
| fw_20261106_03 | Validate material-delegation topology contract semantics | validation | ai_ops | medium | medium | m | deferred | medium | 2027-01-15 |
| fw_20261018_01 | Parked closeout security gate rework and post-landing cost measurement | validation | ai_ops | low | medium | l | partial | low | 2026-12-01 |
| fw_20261023_02 | Bounded read-only cross-repository relocation-reference sweep, Tier 3 | tooling | ai_ops | low | medium | m | partial | low | 2026-12-15 |
| fw_20260227_03 | Add examples/ directory with sample artifacts | documentation | ai_ops | low | medium | m | deferred | low | 2027-01-15 |
| fw_20260315_01 | Session-state infrastructure for context routing fast-path evaluation | integration | ai_ops | low | medium | xl | deferred | low | 2027-01-15 |
<!-- markdownlint-enable MD013 -->

## Notes

- Registry and scorecard should be updated together in the same change.
- From the workspace root, use `python ai_ops/00_Admin/scripts/generate_future_work_scorecard.py`.
  From a nested framework repository root, use `python ../ai_ops/00_Admin/scripts/generate_future_work_scorecard.py`.
