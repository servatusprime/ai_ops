---
title: Guide: Workflow Registries
version: 0.1.0
status: stub
license: Apache-2.0
last_updated: 2026-01-24
owner: ai_ops
related:
- ./guide_workflows.md
- ./guide_ai_ops_vocabulary.md
---

# Guide: Workflow Registries

This guide defines how to structure registries for workflows, runbooks, and workbooks. Registries prevent long file
lists in READMEs and keep artifact inventories consistent.

## Purpose and scope

Registries are canonical inventories for:

- Workprograms (`workbooks_registry.md`)
- Runprograms (`runbooks_registry.md`)

This guide applies to both runbook and workbook registries. Run bundle READMEs are not registries.

## Required fields

Registry entries MUST include:

- Artifact ID
- Full path (copy-pasteable)
- Status
- Dependencies
- Owner or responsible role

Registry files MUST include YAML front matter with `title`, `version`, `status`, `last_updated`, and `owner`.

## Placement and naming

- Workprograms: `workbooks_registry.md` at the program root.
- Runprograms: `runbooks_registry.md` at the program root.

## Promotion workflow

When a workbundle produces canonical artifacts:

1. Add or update the corresponding registry entry.
2. Reference the registry from planning outputs/spec/spine (where applicable).
3. Remove duplicate inventories from READMEs; rely on the registry.

Promotion is a gate: update registries before commit/push when canonical artifacts are added or moved.

Registry checks (required before commit/push):

- Every registry path MUST resolve (`Test-Path <path>`).
- Update registry entries whenever files are renamed or moved.
- Validator rule VS018 mirrors this requirement for configured registries.

Recommended Test-Path check (PowerShell):

```powershell
$registry_paths = @(
  "00_Admin/backlog/future_work_registry.yaml",
  "01_Agents/metadata/agent_registry.yaml", # optional if repo uses 01_Agents/
  "90_Sandbox/ai_workbooks/work_program_*/workbooks_registry.md"
)

foreach ($path in $registry_paths) {
  if (Test-Path $path) {
    Write-Host "Validated: $path"
  }
}
```

Ownership and enforcement:

- The executing agent updates the registry when creating or moving artifacts.
- The Validator confirms `Test-Path` checks before reporting completion.
- If no automated registry validator exists, record the check in the execution log.

## Example

<!-- markdownlint-disable MD013 -->
| Artifact ID | Path | Status | Dependencies | Owner |
| --- | --- | --- | --- | --- |
| wb_example_step_01 | 90_Sandbox/ai_workbooks/work_program_example_program/work_packets/wb_example_step_01_2026-01-14/wb_example_step_01.md | stub | none | coordinator |
<!-- markdownlint-enable MD013 -->
