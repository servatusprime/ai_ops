---
title: Workbundle - Run-Family Generator Determinism 01
id: wb_runfamily_generator_determinism_01
status: completed
version: 0.3.0
created: 2026-08-16
last_updated: 2026-08-26
owner: ai_ops
description: >-
  Isolated Level-4 ai_ops remediation for deterministic run-family derived-view
  serialization, resolvable generator provenance, registry contract versioning,
  and fail-closed receipt validation. The bundle is a direct
  ai_ops lane and does not authorize changes to governed downstream repositories.
---

<!-- markdownlint-disable MD013 MD025 -->

# Workbundle: Run-Family Generator Determinism 01

## Purpose

Repair the run-family derived-view generator so the same canonical manifests
produce byte-identical registry and graph views across fresh Python processes,
while recording generator identity and version in generated outputs. The
downstream consumer packet that exposed this defect is evidence only; no
governed-repository files are edited by this ai_ops bundle.

## Scope

| Surface | Disposition |
| --- | --- |
| `00_Admin/scripts/validate_run_family_graph.py` | Deterministic required-field ordering, registry contract version, and schema-aligned receipt type enforcement |
| `00_Admin/scripts/generate_run_family_views.py` | Generator version, governed-root provenance, registry contract version, and deterministic serialization |
| `00_Admin/configs/validator/schema_run_family_registry.yaml` | Versioned registry provenance contract |
| `00_Admin/configs/validator/schema_run_family_intake_receipt.yaml` | Runtime/schema receipt alignment evidence |
| `00_Admin/configs/validator/schema_run_family_provider_receipt.yaml` | Runtime/schema receipt alignment evidence |
| `00_Admin/tests/test_run_family_graph.py` | Discovered-manifest cross-process/order/provenance and malformed-receipt regression coverage |
| `00_Admin/runbooks/run_family_registry.yaml` | Regenerated ai_ops-local derived evidence only |
| `00_Admin/reports/generated/graphs/*.yaml` | Regenerated ai_ops-local derived evidence only |

Governed-repository generated views are validation consumers, not write targets.
They must be regenerated and checked by their owning governed workbundle after
this ai_ops change is accepted.

## Status

| Gate | State |
| --- | --- |
| Separate Level-4 workbook and scope | Active |
| Deterministic validator/generator/receipt patch | Patched; scoped checks pass |
| Discovered-manifest all-view regression | Pass across four generated views |
| Versioned schema/test validation | Pass; whole-repo baseline errors retained |
| Independent Sol review | `ACCEPT`; downstream handoff/recheck remains open |
| Commit / push | **Done.** `051561f` ("Harden run-family generator determinism", 2026-08-16, servatusprime) on `main`, matching `origin/main`. |

## Handoff

The governing workbook is
`wb_runfamily_generator_determinism_01_2026-08-16.md`. This bundle is
deliberately separate from the active governed-repository writer-consolidation
packet and from the earlier run-family canon uplift bundle.

**Closed out 2026-08-26.** Commit/push were already done as of 2026-08-16;
this pass synced the sandbox docs to match and added the missing
`log_workbook_run.md` entry. The one remaining item -- downstream
(governed-repo) consumer regeneration/recheck -- is explicitly this bundle's
non-goal per the Scope section above, not a blocker for this bundle's own
closeout. Archived to `99_Trash/` as part of this closeout pass.
