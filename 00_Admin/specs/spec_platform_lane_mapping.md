---
title: Platform Lane Mapping Spec
id: spec_platform_lane_mapping
module: admin
status: active
license: Apache-2.0
version: 1.0.0
created: 2026-06-19
updated: 2026-06-19
owner: ai_ops
ai_generated: true
spec_archetype: governance_spec
related:
  - AGENTS.md
  - 00_Admin/guides/ai_operations/guide_ai_ops_vocabulary.md
  - 00_Admin/specs/spec_execution_orchestration.md
  - 00_Admin/specs/README.md
---

<!-- markdownlint-disable MD013 MD025 MD041 -->
# Platform Lane Mapping Spec

## Quick Reference

- **What:** Maps each of the 8 canonical ai_ops lanes to platform instantiation guidance for
  Claude Code, Dispatch/Managed Agents, and OpenClaw.
- **Governance-intent only.** This spec is a conceptual mapping -- it defines what each lane
  means in each platform context. It is NOT a runtime router, harness, or SDK integration guide.
- **Lanes are authoritative in AGENTS.md.** This spec maps; it does not redefine lanes.
- **Platform implementation detail** (tool configs, sandbox parameters, runtime commands) belongs
  in downstream platform docs, not here.
- See also: `AGENTS.md` (canonical lane definitions), `spec_execution_orchestration.md`
  (execution lifecycle).

## Purpose

Provides a single-document reference mapping the 8 canonical ai_ops lanes to their concrete
instantiation surfaces on each supported platform. Without this spec, platform integrators must
infer lane-to-platform correspondence from AGENTS.md, the vocabulary guide, and platform-specific
docs -- a multi-hop read that is error-prone when adopting a second or third platform.

This spec closes that gap by answering: "For each ai_ops lane, what is the platform surface or
mechanism that instantiates it on this platform?"

## Non-Harness Boundary

This document defines a conceptual mapping of ai_ops governance lanes to platform surfaces.

- It MUST NOT be interpreted as a runtime routing specification.
- It MUST NOT be implemented as harness logic, conditional dispatch, or SDK integration code.
- Platform-specific implementation detail (tool manifests, sandbox flags, API parameters,
  agent file formats) belongs in downstream platform integration runbooks and guides, not here.
- If a platform surface does not have a direct equivalent for a lane, the spec records the
  closest available surface and notes the gap -- it does not invent a harness to fill it.

## Lane-to-Platform Mapping

Lanes are defined in `AGENTS.md ## Canonical Lanes`. This table maps each lane to its primary
instantiation surface on each platform. The mapping is governance-intent only.

<!-- markdownlint-disable MD013 -->
| Lane | Claude Code | Dispatch/Managed Agents | OpenClaw |
| --- | --- | --- | --- |
| **Coordinator** | Primary agent context; session owner; phases and escalations managed in-conversation | Session-level system prompt defines governance scope and approval gates; Coordinator intent is declared, not runtime-enforced | Session configuration + system prompt surface; owns the 7-stage loop governance |
| **Planner** | `/plan` mode (EnterPlanMode); produces explicit step-by-step implementation plan before execution | Pre-execution planning step in the session prompt; scope contract authored before task dispatch | SKILL.md: planning template skill; produces phased task contract before executor loop begins |
| **Researcher** | Web search tool + web fetch; bounded discovery within conversation | Tool: web search available to the managed agent; researcher output returned to session | SKILL.md: web_search + web_fetch skills; discovery phase within the agentic loop |
| **Executor** | Direct execution in the conversation context; Edit/Write/Bash tools; Ordered Execution Queue tasks | Task execution environment managed by Dispatch; Executor bounded to declared permission envelope | SKILL.md: task execution skill; operates within the agentic loop stage boundary |
| **Builder** | Project init tools; scaffolding via Bash/Write/Edit; used for tooling or substrate changes | Project scaffolding environment within the Dispatch session; Builder scope declared in session prompt | SKILL.md: project scaffolding skill; substrate-change stage in the agentic loop |
| **Linter** | Pre-commit hooks (`validate_repo_rules.py`, markdownlint); explicit `/lint` invocation | Validation environment; Dispatch manages retries; linter output captured as structured evidence | SKILL.md: lint/format/validate skill; validation stage produces evidence-backed defect report |
| **Reviewer** | `/crosscheck` skill or spawned subagent (Agent tool); read-only review lane; no edits | Separate session or sub-agent invocation; reviewer output returned as structured findings | Separate agent instance or SKILL.md review skill; reviewer reports to Coordinator; no edits |
| **Closer** | Git commit workflow (`git add`, `git commit`); explicit operator go-ahead gate before `git push` | Session finalization phase; Dispatch captures completion evidence; operator-gated promotion | SKILL.md: commit/finalize/archive skill; closeout stage in the agentic loop |
<!-- markdownlint-enable MD013 -->

## Per-Platform Notes

### Claude Code

- **Surface model:** One primary agent context per session. All 8 lanes may run sequentially
  within a single conversation (single_agent topology) or be delegated to spawned subagents
  (multi_agent topology via the Agent tool).
- **Coordinator surface:** The primary agent's session context IS the Coordinator surface.
  No separate Coordinator agent file exists by default.
- **Skill surface:** Workflows in `.ai_ops/workflows/` map to slash commands. The `/work`,
  `/crosscheck`, `/closeout` skills are the primary lane-activation surfaces.
- **Reviewer delegation:** Use `Agent(subagent_type=...)` or the `Agent` tool to spawn an
  independent Reviewer. Reviewer subagents receive structured output contracts and return
  findings only -- no edits.
- **Closer gate:** The commit/push gate is manual by governance policy. Agents MUST NOT
  run `git push` without explicit operator instruction.

### Dispatch/Managed Agents

- **Surface model:** Platform manages context, retries, and tool availability. The Coordinator
  declares governance intent (scope, approval gates, lane sequence) in the session-level system
  prompt; the platform handles execution logistics.
- **Lane boundary enforcement:** Dispatch does not natively enforce lane boundaries as separate
  contexts. The session prompt MUST declare lane activation order and return contracts. The
  lead agent enforces lane sequencing in its own reasoning.
- **Reviewer isolation:** A separate Dispatch session or managed sub-agent invocation is
  required for isolated Reviewer work. Reviewer output MUST be returned as structured findings
  before the lead agent proceeds to Closer.
- **Export and artifact handling:** Dispatch sessions produce evidence in whatever form the
  session is configured to capture. Promotion manifests and governance artifacts MUST be
  included in the task output contract.

### OpenClaw

- **Surface model:** 7-stage agentic loop architecture. Each stage maps to one or more lanes.
  Skills are defined as SKILL.md files and loaded into the loop at declared stages.
- **Lane-to-stage correspondence:** Coordinator governs the overall loop; Planner and Researcher
  run in early stages; Executor/Builder run in implementation stages; Linter runs in validation
  stages; Reviewer and Closer run in finalization stages. Exact stage assignment is determined
  by the OpenClaw integration runbook, not by this spec.
- **Harness note:** The 7-stage loop is OpenClaw's execution architecture. ai_ops lanes are
  governance intent overlaid on that architecture. This spec does not prescribe which OpenClaw
  stage corresponds to which ai_ops lane -- that mapping is a platform integration deliverable.
- **Reviewer isolation:** OpenClaw SHOULD instantiate the Reviewer lane as a separate agent
  instance to ensure read-only isolation. A SKILL.md review skill returning structured findings
  is an acceptable alternative when a separate instance is not available.

## Gaps and Limitations

| Gap | Platforms Affected | Notes |
| --- | --- | --- |
| Native lane-boundary enforcement | All | No platform natively enforces ai_ops lane boundaries. Enforcement is behavioral (session prompt instructions + agent reasoning), not runtime-enforced. |
| Closer gate automation | Dispatch, OpenClaw | The operator-gated push step (Claude Code: explicit `git push` instruction) may require a manual handoff pattern in automated platforms. Platform integration runbooks MUST define this gate explicitly. |
| Director topology | All | The Director pattern (Director spawns Coordinator subagents) is not yet implemented on any platform. See `AGENTS.md ## Director topology -- design note`. |

## Related References

- `AGENTS.md` -- canonical lane definitions, topology concepts, and behavioral parameters
- `00_Admin/guides/ai_operations/guide_ai_ops_vocabulary.md` -- normative vocabulary
- `spec_execution_orchestration.md` -- execution lifecycle and state tracking
- `spec_platform_lane_mapping.md` (this file) entry in `00_Admin/specs/README.md`

## Change Log

| Version | Date | Author | Summary |
| --- | --- | --- | --- |
| 1.0.0 | 2026-06-19 | ai_ops | Initial authoring via wb_platform_lane_mapping_01 (fw_20260423_01) |
