---
title: Guide: Naming Conventions (ai_ops)
version: 0.1.0
status: active
license: Apache-2.0
last_updated: 2026-03-04
owner: ai_ops
---

# Guide: Naming Conventions (ai_ops)

## 1) General Principles

- Use **lowercase_with_underscores** for all files and folders.
- Prefer short, descriptive names; use domain prefixes to group types.
- Avoid spaces and uppercase; use hyphens **only** for external export filenames (e.g., PDFs).
- Always include **YAML front-matter** and a visible `# Heading` for Markdown files.
- Define new acronyms or domain-specific terms in `<work_repo>/01_Resources/guides/glossary.md` so every document
  references the same vocabulary.

---

## 1.1 Unique Basename Rule

No two files may share the same basename unless:

1. **README.md / .gitignore / .gitkeep**: Expected per-directory
2. **module.yaml / **init**.py**: Expected per-module/package
3. **Templates/Archives**: Files in `templates/` or `archive/` directories
4. **Generated Mirrors**: `repo_structure_reference.txt`, auto-generated maps
5. **Run Outputs**: Files in `outputs/` directories with `artifact_type: output`
6. **Explicit Mirror**: File has `status: active` (or `deprecated` if being phased out) + `mirrored_from:` in front
   matter

### Mirror Front Matter Convention

```yaml
status: review
mirrored_from: <canonical_path>
mirror_date: <YYYY-MM-DD>
note: 'Do not edit directly; update canonical source and re-copy.'
```

### Enforcement

- Pre-commit hooks SHOULD warn on new duplicate basenames outside this whitelist.
- Promotion workbooks MUST verify no conflicts before promoting files.

---

## 2) File Type Prefixes

| Type                | Prefix                      | Example                       |
| ------------------- | --------------------------- | ----------------------------- |
| Guide               | `guide_`                    | `guide_environment_setup.md`  |
| Specification       | `spec_`                     | `spec_workflow_structure.md`  |
| Prompt              | `prompt_`                   | `prompt_manifest_layers.md`   |
| Runbook             | `rb_`                       | `rb_postgis_backup.md`        |
| Convention          | `guide_`                    | `guide_naming_conventions.md` |
| Project Log         | `project_log_YYYY-MM-DD.md` | `project_log_2025-11-10.md`   |
| Style (QGIS)        | `style_`                    | `style_zoning_base.qml`       |
| Layout (QGIS)       | `layout_`                   | `layout_env_constraints.qpt`  |
| SQL                 | `sql_` (optional)           | `sql_01_schemas.sql`          |
| Script (PowerShell) | `ps_`                       | `ps_backup_postgis.ps1`       |
| Script (Python)     | `py_` (optional)            | `py_refresh_aoi.py`           |

> Module directories may add their own sub-prefixes; keep them consistent.

Runbook prefix note:

- Canonical prefix is `rb_`.
- Legacy `runbook_` is allowed only for existing files until renamed.
- `rb_` is reserved for runbooks; it MUST NOT be used for runbundles.
- `wb_` is the canonical prefix for workbundle folders.
- `work_program_` and `run_program_` are reserved for workprogram/runprogram folders.
- `rnb_` is reserved for runbundle folders.
- Workbundle folder pattern: `wb_<topic>_<nn>_<YYYY-MM-DD>`
  (e.g., `wb_repo_health_01_2026-01-30`).
- Legacy `wp_` workbundle folders may remain in historical artifacts;
  do not rename in-place without a dedicated refactor workbook.

### 2.1 Sequential Naming for Work-Family Books in Bundles

When workbooks or runbooks are intended to execute in a fixed sequence within a bundle, prepend a zero-padded
two-digit sequence number immediately after the type prefix:

- Workbook in sequence: `wb_NN_<name>.md` (e.g., `wb_01_audit.md`, `wb_02_refactor.md`)
- Runbook in sequence: `rb_NN_<name>.md` (e.g., `rb_01_preflight.md`, `rb_02_execute.md`)

Rules:

- Use sequential naming only when order matters and a bundle or program coordinates the sequence.
- If books are unordered or their sequence is informal, omit the number.
- Start at `01`; reserve gaps only if a slot is deliberately held for a future book.
- Applies to books (workbooks and runbooks) only -- not to bundles, programs, or support artifacts.

---

## 3) Operation Classes for Executable Logic

Executable logic files (Python, PowerShell, shell scripts, and similar) must use an operation-class prefix as the first
token in the filename.

Pattern:

- `<operation>_<domain>_<subject>[_qualifiers].py`

Examples:

- `build_layout_modern_marketing_11x17.py`
- `generate_workbook_scaffold.py`
- `render_exhibit_map_constraints.py`
- `export_aoi_geojson.py`
- `validate_layer_manifest_yaml.py`

### 3.1 Canonical operation prefixes

<!-- markdownlint-disable MD013 -->
| Operation class | Prefix        | Purpose                                                        | Example                                          |
| --------------- | ------------- | -------------------------------------------------------------- | ------------------------------------------------ |
| Build           | `build_`      | Assemble multiple inputs into a complete artifact or template  | `build_layout_modern_marketing_11x17.py`         |
| Generate        | `generate_`   | Create structured data or files from rules/metadata            | `generate_workbook_scaffold.py`                  |
| Render          | `render_`     | Produce final user-facing visuals (PDF/PNG/HTML)               | `render_exhibit_map_constraints.py`              |
| Export          | `export_`     | Send internal objects to external formats or locations         | `export_aoi_geojson.py`                          |
| Fetch           | `fetch_`      | Pull data from a single external source (API/REST/WMS/CSV)     | `fetch_nc_onemap_layers.py`                      |
| Ingest          | `ingest_`     | Bring external data into internal storage/standard structures  | `ingest_parcels_shapefile_to_postgis.py`         |
| Transform       | `transform_`  | Reshape, clean, or re-map data without creating a new artifact | `transform_zoning_csv_to_yaml.py`                |
| Validate        | `validate_`   | Check that data/files/configs meet standards or schemas        | `validate_layer_manifest_yaml.py`                |
| Analyze         | `analyze_`    | Perform calculations/analytics and report findings             | `analyze_aoi_infrastructure_capacity.py`         |
| Cleanup/Maintain| `cleanup_`    | Housekeeping tasks (purge temp/trash, reset sandboxes, etc.)   | `cleanup_sandbox.ps1`                            |
<!-- markdownlint-enable MD013 -->

Notes:

- Prefer these prefixes instead of generic `py_` (or unnamed) scripts. The operation class should tell the agent/human
  what the script does, not just that it is an executable.

- `py_` remains allowed for ad-hoc or mixed-purpose scripts where the operation class is unclear or not worth modeling,
  but use an operation prefix whenever intent is known.

### 3.2 Choosing between operation classes

Use the operation that best matches the primary intent of the script:

- Use `build_` when assembling multiple inputs into a durable artifact (layout templates, manifests, workbooks,
  models).
- Use `generate_` when producing structured data or files primarily from metadata, prompts, or definitions.
- Use `render_` when the main output is a user-facing visual (map exhibit, report PDF, HTML view).
- Use `export_` when moving internal objects out to external formats (GeoJSON, CSV, PDF, ZIP, and similar).
- Use `fetch_` when pulling data from a single external source.
- Use `ingest_` when taking external data and loading it into internal storage (PostGIS, canonical folders,
  standardized schemas).

- Use `transform_` when reshaping or cleaning data.
- Use `validate_` when checking quality/compliance against standards.
- Use `analyze_` when the primary output is insight (metrics, statistics, diagnostics), not a new artifact.

When in doubt, pick the verb that best communicates the user's intent for running the script.

---

## 3.3 Operation Prefix Glossary (Short)

Operation prefixes are intent-based and not domain-specific. Use the shortest verb that describes the primary outcome.

| Prefix | Meaning (short) |
| --- | --- |
| `build_` | Assemble inputs into a durable artifact |
| `fetch_` | Retrieve from a single external source |
| `generate_` | Produce structured outputs from rules/metadata |
| `render_` | Produce user-facing visuals or reports |
| `export_` | Emit internal objects to external formats |
| `transform_` | Reshape or clean data without new artifacts |
| `validate_` | Check compliance or quality |
| `analyze_` | Compute metrics or insights |

## 4) Dates & Versions

- **Dates in text:** `YYYY-MM-DD`
- **Dates in filenames:** `YYYYMMDD` or explicit in the `project_log_YYYY-MM-DD.md` pattern.
- **Semantic versioning:** `major.minor.patch` in front-matter.
- **Front matter dates:** `created` and `updated` must reflect the actual draft/last-edit dates (do not use future
  dates).

---

## 5) Branch & Commit Conventions

### Branches

- `feat/<module>_<topic>` (e.g., `feat/gis_refresh_aoi`)
- `fix/<module>_<topic>`
- `docs/<area>_<topic>`
- Short-lived; merge via PR; delete after merge.

### Commits (Conventional Commits)

- `feat: add refresh_aoi script`
- `fix: correct EPSG in schemas`
- `docs: add environment guide`
- `chore: update .gitignore`

---

## 6) Module-Specific Naming

### 6.1 GIS

- **Schemas:** `base`, `reference_nc`, `reference_in`, `derived`, `dynamic_<project>`, `meta`.
- **Tables:** `snake_case`; geometry column `geom`; include SRID.
- **SQL files:** `03_SQL/01_schemas.sql`, `03_SQL/02_meta_tables.sql`, `03_SQL/03_roles_grants.sql`,
  `03_SQL/04_audit_triggers.sql`.
- **Scripts:** `04_Scripts/refresh_aoi.py`, `04_Scripts/backup_postgis.ps1`.
- **QGIS Project:** `<work_repo>/02_Modules/gis_workflow/templates/project_template.qgz`.
- **QGIS Styles:** `<work_repo>/02_Modules/gis_workflow/styles/style_<topic>.qml`.
- **Layouts:** `<work_repo>/02_Modules/gis_workflow/templates/layouts/layout_<topic>.qpt`.

#### Canonical Layer IDs (for manifests)

- Pattern: `<scope>_<category>_<specific>__<layer_id_2d>`
- Examples: `mecklenburg_zoning_base__00`, `iredell_util_water_mains__00`.
- Allowed `<scope>` tokens: `mecklenburg`, `iredell`, `charlotte`, `mooresville`, `huntersville`, `statesville`,
  `troutman`, `nc`, `statewide`.

### 6.2 Module workbook-style outputs

- Prompt/specs in `02_Modules/<module>/docs/specs/`.
- Exports named: `<artifact_type>_<scope_or_unknown>_<YYYYMMDD>.xlsx`.
- Logs: `project_log_YYYY-MM-DD.md` with **Exhibit A** notes.

### 6.3 Module code layout

- Specification in `02_Modules/<module>/docs/`.
- Python modules (future): `02_Modules/<module>/src/` with `snake_case.py` files.

---

## 7) Data & Export Artifacts

- **Backups (optional):** `Backups/postgis/YYYYMMDD.dump` or `.sql` (or `05_Backups/` in numbered repos).
- **Map Exports:** `05_Exports/maps/{project}_{layout}_{YYYYMMDD}.pdf`.
- **Data Packages:** `05_Exports/data/{aoi}_public.gpkg`, `{aoi}_trace_base.gpkg`.

---

## 8) IDs, Keys, and Tokens

- **Requirement IDs:** `REQ-<SPEC>-<SECTION>-<NNN>` (see `requirements_matrix_template.md`).
- **Manifest tokens:** `${SCHEMA_*}`, `${STYLE_*}` reserved for build-time substitution.
- **AI Canonical IDs:** match the manifest rules for **layer_source_id** and **canonical_id**.

---

## 9) Do & Don't Examples

### Do

- `guide_environment_setup.md`
- `project_log_2025-11-10.md`
- `mecklenburg_zoning_base__00.qml`

### Don't

- `Guide-Environment-Setup.MD`
- `Project Log Nov 10.md`
- `Meck Zoning Base (Final).qml`

---

## 10) Compliance Checklist (Quick)

- [ ] lower_snake_case used throughout
- [ ] Prefix applied per file type
- [ ] Front-matter + `# Heading` present
- [ ] Dates follow standard pattern
- [ ] Branch/commit follow conventions
- [ ] GIS canonical IDs follow `<scope>_<category>_<specific>__<id>`

---

**End of guide.**
