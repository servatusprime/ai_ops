---
title: Runbook: Agent Bootstrap
version: 0.3.1
status: active
license: Apache-2.0
created: 2026-01-24
updated: 2026-03-04
owner: ai_ops
ai_agent_applicability: recommended
---
<!-- markdownlint-disable-next-line MD025 -->
# Runbook: Agent Bootstrap

## Purpose

Guide an agent through bootstrap for external repos so it can align to the
target repo's rules and declared validation policy without scanning or guessing.

Primary use is external repos; internal ai_ops sessions should use the
bootstrap chain in `AGENTS.md` unless a runbook is explicitly requested.
Governed external repos should capture `customizations.validation_policy.governed_mode`
from `.ai_ops/local/config.yaml` before execution lanes begin.

## AI Agent Applicability

- Applicability: Recommended
- Explicit triggers: user requests bootstrap or recovery
- Implicit triggers: cold start or long idle resume
- Role selection is dynamic; see `AGENTS.md` Command Roles.

## When to Use

- Fresh agent session (cold start) in a target repo
- Session resume after long idle
- After major repo structure changes
- When bootstrap failure detected

## Standard Bootstrap Sequence

### Step 1: Read AGENTS.md

From repo root, read `AGENTS.md`:

- Parse the workspace topology block (`ops_stack_root`, `work_repos`)
- Determine mode: Direct (ai_ops is target), Governed (external target), or Standalone (no ai_ops)

If `AGENTS.md` is missing, halt with error: "AGENTS.md not found; cannot bootstrap."
Do not fall back to aiops.yaml -- it has been retired.

### Step 2: Follow Bootstrap Sequence

After reading `AGENTS.md`:

1. **CONTRIBUTING.md** -- Contributor governance and guardrails
2. **context_routing.yaml** -- Read orchestration for the active command
3. **Active artifacts** -- `.ai_ops/local/work_state.yaml` `work_context.active_artifacts`
4. **Validation policy (governed mode)** -- read `.ai_ops/local/config.yaml`
   and record `customizations.validation_policy.governed_mode` (ask if missing).

**Do not scan the filesystem** unless the user explicitly asks. Follow the
AGENTS.md bootstrap section read order only.

If the active environment uses `.ai_ops/workflows` as a command source,
verify the directory exists and is readable.

### Step 3: Capability Certification (Recommended)

Verify bootstrap succeeded:

- Can answer authority level questions (L1)
- Can locate key repo directories (L2)
- Understand workbook/workbundle patterns (L3)

See: [guide_capability_certification.md](../guides/ai_operations/guide_capability_certification.md)

## Bootstrap Failure

If `AGENTS.md` is missing or unreadable:

1. Enter safe-mode (read-only operations)
2. Report failure clearly to user: "AGENTS.md not found; cannot bootstrap"
3. Ask user to confirm repo root and provide AGENTS.md path
4. Do not proceed with governance operations without AGENTS.md

## Bootstrap Failure Recovery

If bootstrap fails (parse errors, missing files, permissions):

1. Enter safe-mode (read-only operations)
2. Report failure clearly to user
3. Provide recovery options

See: [guide_bootstrap_self_repair.md](../guides/ai_operations/guide_bootstrap_self_repair.md)

## Verification

After bootstrap, agent should be able to:

- Identify authority level for file creation (Level 2, requires approval)
- Locate the repo's own policies/specs/guides (if present)
- Avoid inferring purpose from directory names

## Bootstrap Validation Scenarios (Operational Suite)

Use this suite for strict bootstrap validation lanes. These scenarios supersede
the old standalone bootstrap testing spec.

### Critical Scenario Set

| Scenario | Setup | Expected Result |
| --- | --- | --- |
| TS-01 Standard cold start | `AGENTS.md` present at repo root | bootstrap chain respected, no pre-bootstrap scan |
| TS-02 Unstructured prompt cold start | `AGENTS.md` present at repo root | bootstrap still runs first; no invented repo summary |
| TS-04 Missing AGENTS.md | no `AGENTS.md` at repo root | halt with "AGENTS.md not found" error; safe-mode |
| TS-06 Permission error | unreadable `AGENTS.md` | safe-mode + explicit permission remediation |
| TS-08 Onboarding prompt | fresh session | concise onboarding through `/work`, not manual dump |
| TS-10 Orientation prompt | fresh session | sourced repo summary after bootstrap |
| TS-15 Fixture manifests | run valid/invalid fixture set | valid accepted, invalid rejected with clear errors |
| TS-16 Minimal endpoint contract | only minimal required files | bootstrap succeeds without false optional-path failures |

### Fixture Lane for TS-15

Fixtures are maintained at:

- `00_Admin/tests/fixtures/manifests/`

Use these fixture groups:

- valid: `valid_minimal.yaml`, `valid_full.yaml`
- invalid: `invalid_syntax.yaml`, `invalid_schema.yaml`,
  `invalid_paths.yaml`, `invalid_legacy_work_context_keys.yaml`

## References

- [guide_bootstrap_algorithm.md](../guides/architecture/guide_bootstrap_algorithm.md) - Detailed algorithm
- [guide_capability_certification.md](../guides/ai_operations/guide_capability_certification.md) - Certification checks
- [guide_bootstrap_self_repair.md](../guides/ai_operations/guide_bootstrap_self_repair.md) - Failure recovery
- [00_Admin/tests/fixtures/manifests/README.md](../tests/fixtures/manifests/README.md) - fixture descriptions
