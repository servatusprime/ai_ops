---
title: Run-Family Generator Determinism Validation Receipt
id: validation_receipt_wb_runfamily_generator_determinism_2026_08_16
status: active
authority: packet_local_validation_evidence
workbundle: wb_runfamily_generator_determinism_01_2026_08_16
---

## Scoped results

| Command/check | Result |
| --- | --- |
| `python -m unittest discover -s 00_Admin/tests -p test_run_family_graph.py -v` | PASS — 33/33 tests |
| `generate_run_family_views.py --write` | PASS — four ai_ops-local views regenerated |
| `generate_run_family_views.py --check` | PASS — zero drift; source digest `c661c3d8aa87bde7d2dfff98acb1ff7f1384a34858addc5bfcdcdd740b197328` |
| `validate_run_family_graph.py --discover --check-files` | PASS — empty current ai_ops graph, zero artifacts/edges |
| Registry/intake/provider YAML parse | PASS |
| Scoped `git diff --check` | PASS |

The unit suite includes discovered-manifest all-view hash-seed coverage,
schema-invalid receipt scalar fixtures, negative receipt sizes, supplied
`reference_only.evidence_ref` type enforcement, a resolvable sibling
generator-file provenance fixture, and rejection of a missing sibling target.

## Whole-repository baseline

`validate_repo_rules.py --repo-root C:\\RE_Projects\\ai_ops` exits 1 only for
the two pre-existing unrelated VS003 records in the security-audit bundle:

- `baseline_receipt_2026-08-14.md` has invalid status `evidence`;
- `review_sol_ai_ops_security_audit_plan_2026-08-14.md` has invalid status
  `needs_revision`.

The validator also reports the repository's pre-existing VS008/VS022 warnings.
No new validation error is attributable to this workbundle.

## Gate status

This receipt records scoped validation only. It is not a request to commit or
push, and the governed `re_stack` downstream views require their owning packet
to rerun validation after independent Sol acceptance.
