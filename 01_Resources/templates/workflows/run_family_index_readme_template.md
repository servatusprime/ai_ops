---
title: Run-Family Index - <steward or repo scope>
status: active
owner: <steward_id>
description: Human navigation projection of the generated run-family registry.
---

<!-- markdownlint-disable MD013 MD025 -->

# Run-Family Index: <steward or repo scope>

This is the **minimum root document** for a run-family home. It is a *human
navigation projection* of the generated registry, not an authority. Authority
lives in each artifact's colocated `manifest.yaml`; this page and the registry
are `derived_non_authoritative` and MUST be regenerated/parity-checked, never
hand-treated as source of truth.

## Inventory

Projection of the generated registry. Keep in parity with it -- do not
hand-maintain a competing list.

| Artifact ID | Kind | Canonical home | Lifecycle |
| --- | --- | --- | --- |
| `run_program_<id>` | runprogram | `<repo-relative path>` | active |
| `rnb_<id>` | runbundle | `<repo-relative path>` | active |
| `rb_<id>` | runbook | `<repo-relative path>` | active |

Machine index: `<path>/run_family_registry.yaml` (generated,
`derived_non_authoritative`). "Who consumes X" is the registry's derived
reverse-index -- never inferred from folders.

## Discovery and regeneration

```powershell
# regenerate the registry + graph views from the manifests, then verify parity
python 00_Admin/scripts/generate_run_family_views.py --repo-root . --write
python 00_Admin/scripts/generate_run_family_views.py --repo-root . --check
python 00_Admin/scripts/validate_run_family_graph.py --discover --check-files --check-closure
```

## Runnable recipe

This section is part of the promoted artifact's cold-start contract. Replace
the placeholders with the actual artifact-specific invocation and keep the
flags aligned with the current validator help output.

```powershell
# resolve and validate this run-family definition
python 00_Admin/scripts/resolve_run_family.py --help
python 00_Admin/scripts/validate_run_family_graph.py --discover --check-files --check-closure
```

The recipe is a projection of canonical commands, not an authority. A changed
flag or path requires updating this recipe in the same governed batch as the
implementation and its validation evidence.

## Organization contract (this home)

- Folder-per-artifact: each artifact is a folder holding its own `manifest.yaml`
  plus companions (the artifact, tests, fixtures, `execution_graph.yaml` for a
  runprogram). One uniform manifest name (`manifest.yaml`) = one discovery
  contract.
- Home-by-steward: artifacts homed under their maintainer at the broadest scope
  covering all consumers; shared artifacts get a neutral home and are referenced
  by stable ID, never placed under a consumer.
- Kind buckets (`programs/`, `bundles/`, `books/`) are an optional human-scan
  convenience, never an authority boundary.
- `canonical_home` in each manifest is the single path binding; update it in the
  same governed batch as any move, then regenerate.

## Guidance

Reference canon; do not restate it here.

- Run-family authoring: `00_Admin/guides/ai_operations/guide_run_programs.md`,
  `00_Admin/guides/authoring/guide_runbooks.md`
- Composition + identity: `00_Admin/specs/spec_run_family_composition.md`,
  `00_Admin/specs/spec_artifact_graph_identity.md`,
  `00_Admin/specs/spec_repository_indices.md`
- Control graph: `00_Admin/specs/spec_execution_control_graph.md`

### Local conventions

<!-- Only conventions specific to THIS steward/domain. Everything general
belongs in ai_ops canon, linked above. -->

- <local convention, if any>
