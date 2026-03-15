---
title: Template Catalog
version: 0.1.0
status: active
license: Apache-2.0
created: 2026-03-14
last_updated: 2026-03-14
owner: ai_ops
description: >
  Canonical entrypoint for all authoring templates. Guides and specs link here
  for template discovery.
---

<!-- markdownlint-disable-next-line MD025 -->
# Template Catalog

This is the canonical template entrypoint. All references to authoring templates
should point here first. Templates are blank starting points — copy and fill in;
do not edit in place.

## Template Families

### workflows/

Run-family and work-family scaffolds plus operational wrappers.

<!-- markdownlint-disable MD013 -->
| Template | Path | Primary Consumers | Use Notes | Audience |
| --- | --- | --- | --- | --- |
| `command_wrapper_template.md` | `workflows/command_wrapper_template.md` | `/work`, `/health`, `/crosscheck` command authors | Scaffold for adding a new named command | Mixed |
| `execution_spine_template.md` | `workflows/execution_spine_template.md` | Workbook authors, agents | Gate-and-phase execution spine for single-run workbooks | Agent-facing |
| `governed_repo_bootstrap.md` | `workflows/governed_repo_bootstrap.md` | Repo initializers, operators | Bootstrap scaffold for standing up a governed repo | Human/Mixed |
| `peer_review_template.md` | `workflows/peer_review_template.md` | Crosscheck reviewers, validators | Peer/crosscheck review checklist scaffold | Mixed |
| `rb_template_generic.md` | `workflows/rb_template_generic.md` | Runbook authors | Generic runbook starting point | Mixed |
| `runbundle_pipeline_template.md` | `workflows/runbundle_pipeline_template.md` | Runbundle coordinators | Pipeline descriptor for a runbundle | Agent-facing |
| `runbundle_readme_template.md` | `workflows/runbundle_readme_template.md` | Runbundle authors | README scaffold for runbundles | Mixed |
| `runprogram_pipeline_template.md` | `workflows/runprogram_pipeline_template.md` | Runprogram coordinators | Pipeline descriptor for a runprogram | Agent-facing |
| `runprogram_readme_template.md` | `workflows/runprogram_readme_template.md` | Runprogram authors | README scaffold for runprograms | Mixed |
| `scratchpad_template.md` | `workflows/scratchpad_template.md` | Agents, operators | Proposal seed scratchpad starting point | Agent-facing |
| `wb_template_first_run.md` | `workflows/wb_template_first_run.md` | Workbook authors (first-run ops) | Workbook scaffold for first-run / setup operations | Mixed |
| `wb_template_generic.md` | `workflows/wb_template_generic.md` | Workbook authors | Standard workbook scaffold | Mixed |
| `wb_template_lite.md` | `workflows/wb_template_lite.md` | Workbook authors (lightweight ops) | Reduced-overhead workbook for small tasks | Mixed |
| `work_proposal_template.md` | `workflows/work_proposal_template.md` | Level 4 work proposal authors | Proposal scaffold for Level 3/4 governance | Mixed |
| `work_summary_template.md` | `workflows/work_summary_template.md` | Workbook closeout, agents | Completion summary scaffold | Agent-facing |
| `workbundle_pipeline_template.md` | `workflows/workbundle_pipeline_template.md` | Workbundle coordinators | Pipeline descriptor for a workbundle | Agent-facing |
| `workbundle_readme_template.md` | `workflows/workbundle_readme_template.md` | Workbundle authors | README scaffold for workbundles | Mixed |
| `workprogram_pipeline_template.md` | `workflows/workprogram_pipeline_template.md` | Workprogram coordinators | Pipeline descriptor for a workprogram | Agent-facing |
| `workprogram_readme_template.md` | `workflows/workprogram_readme_template.md` | Workprogram authors | README scaffold for workprograms | Mixed |
<!-- markdownlint-enable MD013 -->

### documents/

Document-type templates for specs, reports, environment config, and project structure.

<!-- markdownlint-disable MD013 -->
| Template | Path | Primary Consumers | Use Notes | Audience |
| --- | --- | --- | --- | --- |
| `env_vars_template.md` | `documents/env_vars_template.md` | Module authors, environment setup | Environment variable documentation scaffold | Mixed |
| `harvest_report_template.md` | `documents/harvest_report_template.md` | Scratchpad harvesters, closeout agents | Seed harvest report scaffold | Agent-facing |
| `project_directory_template.md` | `documents/project_directory_template.md` | Project initializers | Canonical suitcase layout scaffold | Human/Mixed |
| `prompt_spec_template.md` | `documents/prompt_spec_template.md` | Prompt authors | Prompt specification scaffold | Mixed |
| `requirements_matrix_template.md` | `documents/requirements_matrix_template.md` | Spec authors, governance reviewers | Requirements matrix scaffold | Mixed |
| `spec-template.md` | `documents/spec-template.md` | Spec authors | General-purpose spec scaffold | Mixed |
<!-- markdownlint-enable MD013 -->

#### documents/health/

Type 3 section-placement artifact templates (health-check tooling consumers).

<!-- markdownlint-disable MD013 -->
| Template | Path | Primary Consumers | Use Notes | Audience |
| --- | --- | --- | --- | --- |
| `section_placement_audit_template.md` | `documents/health/section_placement_audit_template.md` | `/health` command, health reviewers | Section-placement audit scaffold | Agent-facing |
| `section_placement_inventory_template.csv` | `documents/health/section_placement_inventory_template.csv` | `/health` command | CSV inventory scaffold for section placement | Agent-facing |
| `section_reorder_map_template.md` | `documents/health/section_reorder_map_template.md` | `/health` command, remediation authors | Section reorder mapping scaffold | Agent-facing |
<!-- markdownlint-enable MD013 -->

### scripts/

Code scaffolds for Python scripts and similar executables.

<!-- markdownlint-disable MD013 -->
| Template | Path | Primary Consumers | Use Notes | Audience |
| --- | --- | --- | --- | --- |
| `script_template_python.py` | `scripts/script_template_python.py` | Module/tool authors | Python script starting point with standard header and argparse | Mixed |
<!-- markdownlint-enable MD013 -->

## Optional Subdirectories (Create on First Real Asset)

The following subdirectories are **not pre-created** as empty placeholders.
They emerge when governed content is first placed:

- `metadata/` — template metadata files and schemas. Create when a template
  requires a machine-readable metadata sidecar.

## Notes

- Templates live in `01_Resources/templates/`. There is no `00_Admin/templates/`.
- To discover which template to use, consult `00_Admin/guides/authoring/`
  guides (e.g., `guide_workbooks.md`, `guide_runbooks.md`).
- Filled-in demonstrations (examples) live in `02_Modules/<module>/examples/`
  or sandbox workbundles — not here.
