---
title: Runbooks Index
version: 2.2.0
status: active
license: Apache-2.0
created: 2026-01-13
updated: 2026-07-16
owner: ai_ops
description: Index for runbooks under 00_Admin/runbooks
---

<!-- markdownlint-disable-next-line MD025 -->
# Runbooks Index

Runbooks are reusable execution workflows. They live in `00_Admin/runbooks/` and use the `rb_` prefix.

## Active Runbooks

| Runbook | Purpose | Related Command |
| --- | --- | --- |
| `rb_bootstrap.md` | Agent context initialization | `/bootstrap` |
| `rb_commit_push_streamlining_01.md` | Turbo lint/commit/push workflow | `/closeout` |
| `rb_repo_health_review.md` | Self-consistency and cruft detection | `/health` |
| `rb_repo_validator_01.md` | Validation utility (linters, structure) | Referenced by `/closeout` |
| `rb_release_quality_gate_01.md` | Canonical pre-closeout release-quality checks | Workbook closeout readiness |
| `rb_setup_smoke_matrix_01.md` | Setup script help/dry-run verification matrix | `/ai_ops_setup` and setup maintenance waves |
| `rb_workflow_frontmatter_validation_01.md` | Validate `.ai_ops/workflows` frontmatter contract | `/lint`, release-quality gate |
| `rb_packet_relocation_01.md` | Safe workbundle move/copy/verify/remove flow | Workbook-triggered utility |

## Run-Family Discovery

Runprograms, runbundles, and runbooks compose through stable IDs and
consumer-owned `consumes` references. Read
`00_Admin/specs/spec_artifact_graph_identity.md` first, then
`00_Admin/specs/spec_run_family_composition.md`.

`run_family_registry.yaml` is the generated machine index of resolved IDs and
canonical homes. This README remains the human navigation surface and is
mechanically checked against that registry. The registry and generated graph
views are derived; colocated run-family manifests remain the only machine
authority for graph-addressable run-family identity and outgoing edges.

## Usage

Runbooks are invoked by slash commands defined in `.ai_ops/workflows/`. When a user runs
a command like `/health`, the agent reads the workflow file which references the appropriate
runbook.

## Trashed Runbooks (2026-01-25)

The following runbooks were moved to `99_Trash/runbooks_2026-01-25/` as part of WB-07
command gap closeout:

- Layer maintenance runbooks (9) - Never executed, archived after command consolidation
- `rb_deprecated_artifact_sweep_01.md` - Intent rolled into `/health` cruft detection

See `wb_ai_ops_stack_cli_01_07_command_gap_closeout.md` Task 8.1b for rationale.

## Notes

- Use `rb_` as the canonical prefix per `00_Admin/guides/architecture/guide_naming_conventions.md`.
- Runbooks should be model-agnostic (any AI agent can execute them).
- Add new runbooks here and keep this list updated.
- Keep the run-family navigation section aligned with the generated registry.
