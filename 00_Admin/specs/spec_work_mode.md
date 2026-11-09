---
title: Work Mode Spec
id: spec_work_mode
module: admin
status: active
license: Apache-2.0
version: 0.2.0
created: 2026-11-04
updated: 2026-11-09
owner: ai_ops
ai_generated: true
spec_archetype: governance_spec
description: Normative /work behavior for Direct and Governed mode, the placement decision echo and the cross-repo reference rule.
---

<!-- markdownlint-disable-next-line MD025 -->
# Work Mode Spec

## 1. Purpose

Defines the `/work` behavior that depends on the target repo: Direct mode
(`target_repo` is `ai_ops`) and Governed mode (ai_ops governs a different
target). `.ai_ops/workflows/work.md` holds the flow; this spec holds the rules it
points to. It replaces `spec_work_mode_direct.md`, `spec_work_mode_governed.md`
and the placement echo of `spec_workbundle_placement_suggestion.md`.

## 2. Shared Behavior (both modes)

`/work` MUST:

1. Confirm the mode and state the target repo before any write.
2. Resolve active artifacts from `.ai_ops/local/work_state.yaml`
   `work_context.active_artifacts`, scoped to the target repo, before proposing a
   new artifact; never scan the filesystem to infer them.
3. If no active artifact exists, ask for explicit scope: an existing artifact or a
   new workbook or workbundle.
4. Enforce the pre-write authority guard and the Level 4 stop-gates (`AGENTS.md` authority levels) before any write,
   including governed-path writes that require approval.
5. Apply the command routing hook from `context_routing.yaml` and keep reads to the
   references it names.
6. Record the mode confirmation and the active-artifact resolution in the
   execution notes or the session output.

## 3. Mode Deltas

| Concern | Direct (`ai_ops`) | Governed (external target) |
| --- | --- | --- |
| Target resolution | `ai_ops` itself | the `work.md` Scope Block order: explicit user target, open-file context, then `.ai_ops/local/config.yaml` `workspace.work_repos` over the `AGENTS.md` workspace topology; ask if still ambiguous |
| Governance text | edited in place under the authority guard | applied by reference; governance prose is not copied into the target unless explicitly warranted |
| Validation policy | ai_ops validators | `customizations.validation_policy.governed_mode` in `.ai_ops/local/config.yaml` |
| Evidence | target confirmation, active-artifact resolution, authority disposition for touched files | the same, plus the target selection, the handoff state and the cross-repo reference disposition |

Safety constraints:

- `/work` MUST NOT bypass the Level 4 stop-gates for governance files, in either mode.
- `/work` MUST NOT create a new command-surface workflow file in place of updating canonical `/work`.
- In Governed mode, `/work` MUST NOT change ai_ops governance files as part of downstream execution
  unless explicitly approved.

Standalone mode (a repo outside ai_ops governance) has no rules beyond its column in the `work.md` Steps table.

## 4. Placement Decision Echo

Before a new workbook or workbundle is created, the relevance-gate record, written into the new workbook's Scope and
Authority section (or the bundle README), holds:

- `requested_scope_echo`
- `candidate_workbundle_echo`
- `relevance_result` (`match`, `mismatch` or `uncertain`; with no candidate, `mismatch`)
- `placement_decision_echo`

Candidates come from the purpose and scope lines of existing bundle READMEs; no
numeric score is required. On `mismatch` or `uncertain`, `/work` asks before it
places the artifact, and it never creates a workbook without explicit confirmation.

## 5. Cross-Repo Reference Rule (VS028)

- Canonical `ai_ops` artifacts use generic governed-repo placeholders, not concrete
  external repo names or paths.
- Governed repos reference ai_ops governance by repo-root-relative paths (for
  example `../ai_ops/...`).
- A committed artifact MUST NOT carry a machine-local absolute governance path (for
  example `C:\...` or `/Users/...`).

## 6. Focus Recenter

`/work` establishes initial focus at session start or resume; it recenters only when
an active signal appears: scope drift, a blocker or unresolved gate, return from an
explicitly logged side quest, or a completion-integrity mismatch. A high-impact
pre-action recenter is conditional when drift risk is non-trivial, not blanket
overhead. Recenter output records the active artifact, current phase/task, next
required gate, and pending validation commands. Recenter never authorizes an
out-of-scope edit or bypasses a capability gate.

## 7. Related References

- `.ai_ops/workflows/work.md`
- `AGENTS.md`
- `00_Admin/guides/ai_operations/guide_command_workflows.md`
- `00_Admin/policies/policy_status_values.md` (the status vocabulary of `work_state.yaml`)

## Change Log

- 0.2.0 (2026-11-09): Consolidated the focus-recenter behavior into this spec and
  made the purpose and related-reference sections explicit.
- 0.1.0 (2026-11-04): Created from the direct and governed mode specs and the
  placement echo; the focus-recenter spec and placement scoring contract were
  retired to `99_Trash/` under the use test.
