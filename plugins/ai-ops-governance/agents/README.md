# ai-ops-governance agents

<!-- markdownlint-disable MD013 -->

Generated functional subagent definitions managed by `/profiles`.

## Inventory

| File | Functional role | permissionMode | Primary workflow lanes |
| --- | --- | --- | --- |
| `ai-ops-planner.md` | Planning and scope analysis | `plan` | `/work`, `/bootstrap`, `/work_status` |
| `ai-ops-executor.md` | Implementation and file changes | `default` | `/work`, `/customize`, `/scratchpad` |
| `ai-ops-reviewer.md` | Structured review and findings | `plan` | `/crosscheck`, `/health` |
| `ai-ops-researcher.md` | Context gathering and synthesis | `plan` | Research phases before planning/execution |
| `ai-ops-closer.md` | Validation and closeout execution | `default` | `/closeout`, `/harvest` |
| `ai-ops-linter.md` | Mechanical validation checks | `default` | `/lint`, validation gates in `/closeout` and `/crosscheck` |

## Model Selection Policy

Agent files default to `model: inherit`, preserving the lead agent's discretion
to select the most token-efficient model capable of the delegated task. The lead
agent SHOULD prefer the cheapest capable model for each delegation:

| Task complexity | Recommended model | Example delegation |
| --- | --- | --- |
| Mechanical checks, simple searches | `haiku` | Lint pass, file inventory, grep tasks |
| Moderate analysis, structured output | `sonnet` | Review findings, plan generation, report synthesis |
| Complex judgment, architectural decisions | `opus` | Governance audits, cross-cutting design reviews |

To override the default for a specific role, set `model:` in the agent file
frontmatter (via `/profiles` source YAML, not hand-edit). Static model
assignment removes lead agent discretion for that role.

## Regeneration Contract

- Source profile data: `02_Modules/01_agent_profiles/base/default_crew.yaml` or
  `.ai_ops/local/profiles/active_crew.yaml`.
- Legacy local fallback during migration: `.ai_ops/profiles/active_crew.yaml`.
- Regeneration script: `00_Admin/scripts/regenerate_profiles.py`.
- Generated files in this directory are derived artifacts and should not be
  hand-edited.
