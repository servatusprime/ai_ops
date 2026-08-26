---
title: AI Workbook - Run-Family Generator Determinism 01
id: wb_runfamily_generator_determinism_01_2026_08_16
status: completed
license: Apache-2.0
version: 0.3.0
created: 2026-08-16
last_updated: 2026-08-26
owner: ai_ops
ai_role: coordinator
model_profile: "Luna:low | Terra:medium | Sol:high"
authority_level: 4
execution_mode: execution
execution_topology: hybrid
activated_lanes:
  - Coordinator
  - Planner
  - Executor
  - Reviewer
  - Linter
delegation_policy: coordinator_judgment
convergence_profile: bounded_patch_then_cross_process_regression
parallel_coordination_id: pcid_runfamily_generator_determinism_20260816
depends_on:
  - wb_runfamily_canon_uplift_01
affects:
  artifacts:
    - 00_Admin/scripts/validate_run_family_graph.py
    - 00_Admin/scripts/generate_run_family_views.py
    - 00_Admin/configs/validator/schema_run_family_registry.yaml
    - 00_Admin/configs/validator/schema_run_family_intake_receipt.yaml
    - 00_Admin/configs/validator/schema_run_family_provider_receipt.yaml
    - 00_Admin/tests/test_run_family_graph.py
    - 00_Admin/runbooks/run_family_registry.yaml
    - 00_Admin/reports/generated/graphs/*.yaml
  workbooks: []
shared_files:
  - 00_Admin/scripts/validate_run_family_graph.py
  - 00_Admin/scripts/generate_run_family_views.py
  - 00_Admin/configs/validator/schema_run_family_registry.yaml
  - 00_Admin/tests/test_run_family_graph.py
execution_root: .
path_basis: repo_root
description: >-
  Level-4 direct ai_ops remediation for run-family derived-view determinism,
  generator provenance, registry contract versioning, and runtime receipt/schema
  parity. The canonical input contract remains the colocated run-family
  manifests; generated views remain derived and non-authoritative.
related_refs:
  - 00_Admin/specs/spec_artifact_graph_identity.md
  - 00_Admin/specs/spec_run_family_composition.md
  - 00_Admin/scripts/validate_run_family_graph.py
  - 00_Admin/scripts/generate_run_family_views.py
  - 00_Admin/tests/test_run_family_graph.py
  - 00_Admin/configs/validator/schema_run_family_intake_receipt.yaml
  - 00_Admin/configs/validator/schema_run_family_provider_receipt.yaml
  - 99_Trash/wb_runfamily_generator_determinism_01_2026-08-16/validation_receipt_2026-08-16.md
checklist_allowance:
  kind: forward_handoff
  target_artifact: wb_runfamily_generator_determinism_01_2026_08_16
  rationale: >-
    2026-08-26 closeout review found this bundle's canonical patch was
    already committed and pushed (051561f, 2026-08-16, servatusprime) --
    resolving five of the six original open items (commit, push, requestor
    acceptance-by-committing, and both explicit authorizations). The one
    remaining open item is a genuine forward handoff: downstream
    (governed-repo) consumer regeneration/recheck is this bundle's own
    README's explicit non-goal ("Governed-repository generated views are
    validation consumers, not write targets. They must be regenerated and
    checked by their owning governed workbundle after this ai_ops change is
    accepted."), not a gap in this bundle's own scope.
  open_items:
    - "Downstream consumer regeneration/recheck is recorded."
---

<!-- markdownlint-disable MD013 MD025 -->

# AI Workbook: Run-Family Generator Determinism 01

## Status Checklist

- [x] Separate Level-4 ai_ops workbundle created for the generator defect.
- [x] Downstream governed-repository consumer impact is recorded as evidence;
      no downstream write authority is assumed.
- [x] Patch validator field-order projection without weakening set-based
      contract validation.
- [x] Add generator identity/version and repo-relative provenance to outputs.
- [x] Add discovered-manifest cross-process/hash-seed regression coverage for
      all four generated views.
- [x] Add runtime receipt type enforcement and bump the incompatible registry
      output/schema contract to version `0.2.0`.
- [x] Run scoped schema, unit, validator, and generator checks; whole-repo
      validation retains two pre-existing VS003 audit errors.
- [x] Obtain independent Sol strict hybrid re-adjudication after remediation;
      final verdict is `ACCEPT` with only non-blocking test hardening, which was
      also completed.
- [x] Commit or push. **Done 2026-08-26 (discovered already complete):**
      `051561f` ("Harden run-family generator determinism", 2026-08-16,
      author servatusprime) is on `main`, matching `origin/main`.

## Intake Classification and Gated Boundary

- **Classification:** `execution`.
- **Target:** direct-mode `ai_ops` only.
- **Authorized now:** the declared `affects.artifacts` set, discovered-manifest
  regression fixtures, receipt validation fixtures, sibling-root provenance
  fixtures, and ai_ops-local derived-view regeneration.
- **Hard-gated:** governed downstream repository writes, promotion, commit, and
  push. A downstream consumer must rerun its own generated-view checks after
  this bundle is accepted.

## Execution Topology Contract

```yaml
execution_topology: hybrid
activated_lanes: [Coordinator, Planner, Executor, Reviewer, Linter]
delegation_policy: coordinator_judgment
convergence_profile: bounded_patch_then_cross_process_regression
merge_owner: Coordinator
review_direction: hybrid
review_strictness: strict
write_targets:
  - declared ai_ops scripts, registry schema, tests, and ai_ops-local derived views
hard_stops:
  - no governed downstream repository edits
  - no promotion, commit, or push without a later explicit gate
```

## Cold-Start Execution Contract

- Read `AGENTS.md`, setup contract/receipt, active state, and the two graph
  identity/composition specs before editing.
- Treat colocated manifests as canonical input and all registries/graphs as
  derived non-authoritative outputs.
- Preserve the public set semantics of validator required-field constants while
  introducing an explicit deterministic iteration order.
- Record one merge owner and one validation receipt for every affected consumer.

## Pre-Execution Readiness Gate

- [x] Authority level 4 is declared and the workbundle is isolated.
- [x] Affected scripts, schema, tests, and derived outputs are allowlisted.
- [x] The defect is reproduced by `generate_run_family_views.py --check` and
      fixed-seed serialization diagnostics.
- [x] Requestor/maintainer acceptance of the canonical patch. Evidenced by
      the requestor committing the patch themselves (`051561f`, 2026-08-16).
- [x] Independent Sol recheck.
- [x] Commit/push authorization. Evidenced by the completed commit and push
      (`051561f` on `main`, matching `origin/main`).

## Resume Delta - 2026-08-16

- **Prior claimed state:** the generator was treated as an available shared
  validator surface, while downstream graph consumers reported registry drift.
- **Live evidence checked:** `ARTIFACT_REQUIRED` was a set iterated during
  artifact projection; generated outputs lacked generator identity/version;
  receipt runtime checks accepted schema-invalid scalar types; and the registry
  schema changed incompatibly without a registry contract-version bump.
- **Deltas found and corrected:** ordered projection, generator provenance,
  discovered-manifest/all-view regression, runtime receipt type enforcement,
  registry/schema versioning, and sibling-root provenance enforcement are
  patched in this bundle.
- **Checks rerun or owed:** scoped unit, generator, schema, and direct graph
  checks pass after the patch; the packet-local validation receipt records the
  exact commands and the two unrelated baseline VS003 errors. Final Sol
  re-adjudication and downstream consumer regeneration/recheck remain owed.
- **Gates still open:** canonical patch acceptance, Sol review, downstream
  regeneration/recheck, commit, and push.

## Ordered Execution Queue

### Phase 0 — Reproduce and freeze

1. Capture the current ai_ops-local generator/validator outputs and source hash.
2. Run multiple `PYTHONHASHSEED` values against the same canonical input.
3. Confirm no downstream repository is a write target of this bundle.

### Phase 1 — Deterministic canonical patch

1. Add an ordered tuple for artifact projection while retaining the set constant
   used by schema membership assertions.
2. Add a generator version constant and repo-relative generator provenance.
3. Extend the registry schema and tests for the version/provenance fields.

### Phase 2 — Regression and derived refresh

1. Run the ai_ops unittest for run-family graph behavior.
2. Run the generator across fixed hash seeds and compare bytes.
3. Run registry/schema/repo-rule validators.
4. Regenerate ai_ops-local derived views and confirm `--check` passes in fresh
   processes.

### Phase 3 — Independent review and downstream handoff

1. Obtain strict hybrid Sol recheck against the patched validator, generator,
   schemas, tests, and receipts.
2. Record any remediation dispositions and preserve the review as a packet
   artifact.
3. Hand downstream consumers the generator version/provenance and receipt
   contract for their own regenerated-view checks.

## Verification Checklist

- [x] Required-field projection is byte-stable across fixed hash seeds.
- [x] Registry and graph outputs contain generator identity/version.
- [x] Registry schema accepts the new provenance contract and rejects malformed
      versions.
- [x] Existing set-based validator behavior remains intact.
- [x] Runtime receipt validation rejects schema-invalid scalar types and
      negative sizes.
- [x] Unittest and repository validators pass within the documented baseline.
- [x] `generate_run_family_views.py --check` passes in fresh processes.
- [x] Sol review is retained with blocking/non-blocking dispositions.
- [x] No governed downstream file is changed by this bundle.

## Selfcheck Results

| Check | Result | Evidence |
| --- | --- | --- |
| Scope/authority | `PASS` | Direct ai_ops Level-4 bundle with explicit downstream hard stop. |
| Determinism patch | `PASS` | Ordered projection and generator provenance are patched. |
| Cross-process regression | `PASS` | Fresh-process hash-seed coverage compares all four generated views from discovered manifests. |
| Schema/unit/repo validation | `PASS_WITH_BASELINE` | Scoped checks pass; whole-repo validation retains two unrelated VS003 errors. |
| Independent Sol review | `ACCEPT` | Final Sol recheck accepts downstream handoff; commit/push remain gated. |
| Commit/push | `DONE` | `051561f` ("Harden run-family generator determinism", 2026-08-16, servatusprime) on `main`, matching `origin/main`. Discovered already complete during the 2026-08-26 closeout review; this bundle's own docs had not been updated to reflect it. |

## Requestor Gates

- [x] Requestor directed execution of the separate generator remediation lane.
- [x] Sol accepts the implementation and provenance contract.
- [ ] Downstream consumer regeneration/recheck is recorded.

  Genuine forward handoff, not a gap: per this bundle's own README, governed
  consumer views are regenerated/checked by their owning governed workbundle
  after this change is accepted, not by this bundle. See `checklist_allowance`
  in the frontmatter above.
- [x] Commit is explicitly authorized. Already exercised (`051561f`).
- [x] Push is explicitly authorized. Already exercised (`051561f` on
      `origin/main`).

## Closeout Note (2026-08-26)

This bundle's substantive canonical work, Sol acceptance, commit, and push
were all already complete as of 2026-08-16. The only action this closeout
pass took was documentation sync (this workbook, the bundle README) plus
adding the missing `00_Admin/logs/log_workbook_run.md` entry that the
Post-Execution Archival contract requires for any commit/push -- that entry
did not exist for `051561f` prior to this pass. No new canonical/behavior
changes were made. Archived to `99_Trash/` as part of this closeout pass.
