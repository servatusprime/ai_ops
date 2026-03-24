# ai-ops-governance agents

<!-- markdownlint-disable MD013 -->

Generated lane-aligned subagent definitions managed by `/profiles`.

## Inventory

| File | Purpose | Canonical lane | permissionMode | Primary workflow lanes |
| --- | --- | --- | --- | --- |
| `ai-ops-planner.md` | Planning and scope analysis | `Planner` | `plan` | `/work`, `/bootstrap`, `/work_status` |
| `ai-ops-executor.md` | Implementation and file changes | `Executor` | `default` | `/work`, `/customize`, `/scratchpad` |
| `ai-ops-builder.md` | Tooling, automation, and config changes | `Builder` | `default` | `/work`, `/customize` |
| `ai-ops-reviewer.md` | Structured review and findings | `Reviewer` | `plan` | `/crosscheck`, `/health` |
| `ai-ops-researcher.md` | Context gathering and synthesis | `Researcher` | `plan` | Research phases before planning/execution |
| `ai-ops-closer.md` | Validation and closeout execution | `Closer` | `default` | `/closeout`, `/harvest` |
| `ai-ops-linter.md` | Mechanical validation checks | `Linter` | `default` | `/lint`, validation gates in `/closeout` and `/crosscheck` |

## Canonical Routing Matrix

These generated plugin profiles are derivative routing surfaces. They do not
replace the canonical lane schema in `AGENTS.md`; they map back to it.

| Canonical lane | Plugin profile | Typical marker | Notes |
| --- | --- | --- | --- |
| `Coordinator` | no dedicated generated profile | `[Agent: Coordinator \| <tier>]` | Intentionally absent. Coordinator is the lead lane — it owns sequencing, architecture judgment, and delegation contracts. Giving it a worker profile would create authority ambiguity in single-level delegation. Hierarchical topologies where a nested Coordinator manages a sub-bundle are a Workbook D (native subagent runtime delivery) design decision. |
| `Planner` | `ai-ops-planner.md` | `[Agent: Planner \| <tier>]` | Planning and scoping translation lane. |
| `Researcher` | `ai-ops-researcher.md` | `[Agent: Researcher \| <tier>]` | Read-only evidence and contradiction gathering lane. |
| `Executor` | `ai-ops-executor.md` | `[Agent: Executor \| <tier>]` | Primary implementation lane. |
| `Builder` | `ai-ops-builder.md` | `[Agent: Builder \| <tier>]` | Dedicated tooling/config and substrate-change lane. |
| `Reviewer` | `ai-ops-reviewer.md` | `[Agent: Reviewer \| <tier>]` | Judgment-heavy review lane. |
| `Linter` | `ai-ops-linter.md` | `[Agent: Linter \| <tier>]` | Mechanical validation lane. |
| `Closer` | `ai-ops-closer.md` | `[Agent: Closer \| <tier>]` | Finalization and closeout lane. |

## Delegation Payload Contract (Derivative Surface)

When the lead agent delegates to one of these plugin profiles, the minimum
payload should stay aligned to Workbook A canon:

- `task_brief`: the scoped Delegation Brief or queue item the child is expected to satisfy
- `context_pack`: cited workbook, target files, and supporting evidence needed for the task
- `permission_envelope`: frontmatter `tools` and `permissionMode`, plus any narrower lead-agent constraints
- `skill_surface`: the listed workflow skills, used only when the delegated task calls for them
- `return_contract`: evidence-backed outcomes, blockers, and file references mapped to the delegated acceptance criteria

Plugin profiles should not be expected to infer omitted parent intent from the
ambient session. The lead agent remains responsible for packaging the minimum
viable delegation payload.

Builder work now routes to `ai-ops-builder.md`. Keep `ai-ops-executor.md`
focused on implementation tasks that do not need the dedicated Builder lane.

## Model Selection Policy

Agent files default to `model: inherit`, preserving the lead agent's discretion
to select the cheapest tier adequate for the delegated task. The lead
agent SHOULD prefer the cheapest tier adequate for each delegation:

| Task complexity | Recommended tier | Example delegation |
| --- | --- | --- |
| Mechanical checks, simple searches | `low` | Lint pass, file inventory, grep tasks |
| Moderate analysis, structured output | `medium` | Review findings, plan generation, report synthesis |
| Complex judgment, architectural decisions | `high` | Governance audits, cross-cutting design reviews |

To override the default for a specific lane, set `model:` in the agent file
frontmatter (via `/profiles` source YAML, not hand-edit). Static model
assignment removes lead agent discretion for that lane. Concrete provider/model
choice is surface-specific and should be resolved by the lead agent or native
runtime, not hard-coded in this README.

## Plugin Subagent Limitations

When these generated agent files are loaded through a Claude plugin surface,
some native Claude Code controls are not applied. Treat the plugin surface as
narrower than project- or user-level native `.claude/agents/` subagents.

- Plugin-loaded subagents ignore `permissionMode`, `hooks`, and `mcpServers`.
- Plugin agent files therefore should not be treated as full-fidelity mirrors
  of native Claude Code subagent configuration.
- If a workflow depends on those controls, prefer native `.claude/agents/`
  configuration or document the limitation explicitly in the governed-repo
  execution lane.

## Regeneration Contract

- Source profile data: `02_Modules/01_agent_profiles/base/default_crew.yaml` or
  `.ai_ops/local/profiles/active_crew.yaml`.
- Legacy local fallback (compatibility): `.ai_ops/profiles/active_crew.yaml`.
- Regeneration script: `00_Admin/scripts/regenerate_profiles.py`.
- Canonical lane alignment, delegation-payload expectations, role summaries,
  operating protocol text, report-contract text, and `Best fit:` routing hints
  in the generated agent files are upstream-managed through the regeneration
  pipeline and must be changed in source/generator inputs, not by
  hand-editing files in this directory.
- Generated files in this directory are derived artifacts and should not be
  hand-edited.
