---
title: Design Tests
version: 1.0.0
status: active
license: Apache-2.0
last_updated: 2026-03-03
owner: ai_ops
description: >
  Eight named design tests for validating new ai_ops artifacts and processes.
related:
  - ../../../HUMANS.md
  - ../../../AGENTS.md
  - 00_Admin/guides/ai_operations/guide_ai_operations_stack.md
---

<!-- markdownlint-disable MD013 -->
<!-- markdownlint-disable-next-line MD025 -->

# Design Tests

When proposing a new artifact or process, run these eight named design tests.
All must pass.

## The Eight Tests

| Test Name | Question to Ask | Pass Condition |
| --- | --- | --- |
| **Axis test** | Can you name the primary axis in one word? | Artifact maps to exactly one axis (Intent/Commitment/Execution/Verification/Meta); mixed responsibility fails. |
| **Cold-start test** | Can a new agent start from files and execute without chat history? | New agent can complete task reading only repo artifacts; no external context or conversation required. |
| **Restart test** | If the agent crashes mid-run, can a different agent resume from the artifacts? | Artifacts include explicit state (compacted context, decision log); resumption does not require reconstructing history. |
| **Gate test** | Are validation and approval gates explicit before risk, not after? | Gates appear before irreversible actions; no "ask forgiveness" patterns; decisions are documented before execution. |
| **Thrift test** | Did you reduce internal cycle burden or increase it? | No avoidable read hops; no bouncing across documents for single lane; artifact nesting is minimal and justified. |
| **Adapter test** | Is there one canonical source and many generated targets? | Source of truth is single and explicit; derived artifacts (generated exports, templates, manifests) flow FROM canonical, not back. |
| **Independence test** | If this is a review artifact, was it produced independently of the work being reviewed? | Reviewer had no involvement in creation; review happens without input from creators; findings are third-party. |
| **Portability test** | Does behavior survive tool-surface differences? | No hardcoded tool flags, paths, or model names; behavior adapts to config and environment; not coupled to one CLI. |

## When to Run

Run all eight tests on:

- New artifact types (Policy, Guide, Spec, Workbook, Tool, Contract, etc.)
- Significant process changes (new command, new workflow, new review gate)
- Cross-layer governance changes (touching multiple axes together)

**Pass criteria:** ALL eight tests pass. Any test failure -> redesign required
before adoption.

## Anti-Patterns These Tests Prevent

| Test | Anti-pattern prevented |
| --- | --- |
| **Axis test** | Mixed responsibility (e.g., workbook that also acts as a policy) |
| **Cold-start test** | Chat-only planning with no durable record |
| **Restart test** | Loss of progress when handoffs fail |
| **Gate test** | "Implicit approval" and late-stage corrections |
| **Thrift test** | Fragments that require constant bouncing across documents |
| **Adapter test** | Authority fragmentation (multiple sources of truth) |
| **Independence test** | Echo reviews (reviewer and author being same agent in same context) |
| **Portability test** | Tool lock-in and cross-repo breakage |
