---
title: Guide: SQL Authoring
version: 1.0.0
status: active
license: Apache-2.0
last_updated: 2026-01-12
owner: ai_ops
related:
- 00_Admin/guides/architecture/guide_repository_structure.md
- 00_Admin/guides/authoring/guide_python_authoring.md
- 00_Admin/guides/authoring/guide_yaml_authoring.md
- 00_Admin/specs/spec_repo_metadata_standard.md
---

# Guide: SQL Authoring

## Purpose

Defines SQL authoring conventions for Postgres/PostGIS schema, views, ETL helpers, and validation queries.
Covers dialect rules, formatting standards, and naming conventions for SQL files in the repo.

SQL is used for Postgres/PostGIS schema, views, ETL helpers, and validation queries.

## Dialect & Environment

- Default dialect: **PostgreSQL** (with **PostGIS** where spatial is involved).
- Assume Postgres 14+ unless a file explicitly states otherwise.
- If a script targets a different engine (e.g., SQLite), note it in a header comment.

Example header:

```sql
-- dialect: postgresql+postgis
-- module: <module>
-- purpose: generate module-specific outputs for downstream ETL
```

## File Locations

Prefer these locations, in order:

1. **Module-specific SQL**
   - `02_Modules/<module>/sql/`
   - Use for DDL (tables, views), ETL steps, and module-owned maintenance.

2. **Project-specific SQL**
   - `../<work_repo>/Projects/<project>/sql/`
   - Use for queries tightly coupled to one project or AOI.

3. **Sandbox / experiments**
   - `90_Sandbox/<date>_<purpose>/`
   - Promote only stable, reusable scripts into `02_Modules/<module>/sql/`.

Avoid introducing a new top-level `sql/` or `scripts/` folder without updating `guide_repository_structure.md` first.

## Formatting & Style

- Encoding: **UTF-8**, **LF** line endings, final newline required.
- Indent with **2 spaces** for query bodies and clauses.
- One major statement per file when possible, or clearly separated blocks with comments.
- Uppercase SQL keywords, lowercase identifiers.

Example:

```sql
SELECT
  p.parcel_id,
  ST_Area(p.geom::geography) AS area_sq_m
FROM
  parcels p
WHERE
  p.county = 'Iredell';
```

## Naming Conventions

- Use **snake_case** for tables, columns, views, and functions.
- Avoid reserved words (`user`, `order`, etc.).
- Prefer descriptive names over abbreviations (`parcel_id`, not `pid`).

Examples:

- Tables/views: `aoi_boundary`, `parcel_index`, `zoning_overlay`
- Columns: `created_at`, `updated_at`, `geometry`, `source_system`

If a module has its own naming rules (e.g., prefixes for staging tables), document them in the module spec and keep them
consistent here.

## Safety & Destructive Operations

- Never run **destructive DDL** casually from shared scripts:
- Avoid `DROP TABLE` / `TRUNCATE` without clear intent and protections.
- Prefer `DROP TABLE IF EXISTS ...` when needed.
- For schema changes, prefer a **migration-style** script pattern:
- `001_create_base_tables.sql`
- `002_add_zoning_overlays.sql`
- Clearly mark non-reversible operations with comments at the top of the file.

Example:

```sql
-- WARNING: destructive migration; drops and recreates staging tables
```

## Parameters & Execution

- Do **not** inline user input into SQL strings in Python (no string concatenation or f-strings).
- Use parameterized queries in Python (e.g., `psycopg2` / `asyncpg` placeholders).
- If a `.sql` file is intended to be parameterized, document the parameters:

```sql
-- params:
--   :aoi_id::uuid  - AOI identifier
--   :min_area::numeric - minimum area (sqm)
```

and ensure the Python layer binds those parameters correctly.

## Comments & Documentation

- Use `--` for single-line comments and `/* ... */` sparingly for blocks.
- Each reusable `.sql` file should have a brief header:

```sql
-- name: build_parcel_index
-- module: <module>
-- purpose: normalize and index parcel geometries
-- inputs: source.parcels
-- outputs: work.parcel_index
```

- Prefer describing **inputs, outputs, and assumptions** rather than restating the SQL.

## Tooling

- Use a SQL/DB extension in IDE configured for PostgreSQL.
- Run queries through a safe connection (e.g., test database) before applying to production-like data.
- Consider using `sqlfluff` or a similar linter in the future; if adopted, update this guide with the exact rules and
  commands.

## AI & Codex Considerations

- Keep queries **focused and readable** so they can be safely edited by AI:
- Break complex logic into CTEs with meaningful names.
- Avoid deeply nested subqueries when a CTE would be clearer.
- When a SQL file is tightly coupled to a Python workflow, mention the Python entrypoint in a comment:

```sql
-- used by: <script>.py (02_Modules/<module>/src/cli/<script>.py)
```

This helps Codex and ChatGPT keep Python and SQL in sync when refactoring ETL steps.
