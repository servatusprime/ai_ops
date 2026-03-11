---
title: Guide: Python Authoring
version: 1.6.0
status: active
license: Apache-2.0
last_updated: 2026-02-12
owner: ai_ops
related:
- 00_Admin/guides/tooling/guide_environment_setup.md
- 00_Admin/guides/authoring/guide_json_authoring.md
- 00_Admin/guides/authoring/guide_yaml_authoring.md
- 01_Resources/templates/scripts/script_template_python.py
- 00_Admin/specs/spec_repo_metadata_standard.md
---

<!-- markdownlint-disable MD025 -->

# Guide: Python Authoring

Python is used for ETL, automation, and validation across modules.

## Canonical Script Template

Use this starter when creating new Python scripts:

- `01_Resources/templates/scripts/script_template_python.py`
- `<work_repo>/01_Resources/templates/scripts/script_template_gis_desktop.py`
  (domain-overlay desktop GIS template; canonical in the governed repo)

The template includes a standard pattern for:

- argument parsing (`argparse`)
- structured logging (`logging`)
- path validation (`pathlib.Path`)
- clean entrypoint and exit codes (`main()` + `SystemExit`)

## Cold-Start Checklist (AI Agents)

Before writing Python code, confirm:

1. **Environment:** Which Conda/venv environment? Check `environment.yml` or module docs.
2. **Python version:** 3.11 unless module specifies otherwise.
3. **Path strategy:** Use `pathlib.Path(__file__).resolve()` - never hard-coded paths.
4. **Config source:** Environment variables via `.env` or project config files.
5. **Linting:** Ruff is canonical. Run `ruff --fix` before commit.
6. **Module guide:** If domain-specific (GIS, ETL), read the module's authoring guide first.

If any of these are unclear, ask before writing code.

## Minimum Safe Path (Start Here)

For cold-start execution, use this sequence:

1. Copy `01_Resources/templates/scripts/script_template_python.py`.
2. Implement only argument parsing, input checks, and one deterministic action.
3. Run lint (`ruff --fix`) and markdownlint for touched docs.
4. Add/verify script path in the invoking runbook `script_deps`.
5. Record command output evidence in workbook selfcheck.

Do not add optional features (parallelism, retries, advanced abstractions) until
the baseline path passes.

## Version & Environment

- Python 3.11
- Module-specific environments (for example, geospatial stacks) MUST be documented in module guides.
- Code must not assume a specific Conda environment name at runtime; it should only assume that the required
  dependencies are available, as documented in `environment.yml`.

## Formatting & Linting

- black, isort, ruff/flake8, optional mypy.
- Line length: 120 chars.
- Ruff is the canonical linter; use `ruff --fix` for style issues (E501/B9/etc.) and add `from exc` when re-raising
  exceptions.
- Commit/push steps and lint execution are defined in `00_Admin/policies/policy_git_workflow_conventions.md`.
- Avoid file-wide lint disables; prefer fixing or narrowly scoping ignores.

## Structure

- Scripts: 04_Scripts/
- Reusable code: 02_Modules/<module>/src/
- Tests: 02_Modules/<module>/tests/

## Imports

import json
import logging
from pathlib import Path

## Type Hints & Docstrings

Use triple-quoted docstrings and full type hints.

## Logging

Use logging, never print().

## Paths

Use `pathlib.Path` for all filesystem work; no hard-coded absolute paths.

- **Do not** use user-specific or machine-specific paths (e.g., `C:\\Users\\<user>\...`).
- Treat the repository root as the primary anchor for relative paths.
- When a script lives inside `02_Modules/<module>/src/`, derive `ROOT` like this:

  ```python
  from pathlib import Path

  # Adjust the number of parents as needed based on file location
  ROOT = Path(__file__).resolve().parents[2]

  resources_dir = ROOT / "01_Resources"
  # For repos using the optional Projects/ pattern:
  # projects_dir = ROOT / "Projects"  # or "04_Projects/" in numbered repos
  ```

- Project-specific scripts inside `../<work_repo>/Projects/<project>/` should prefer a project-local root:

  ```python
  PROJECT_ROOT = Path(__file__).resolve().parents[1]
  data_dir = PROJECT_ROOT / "data"
  config_dir = PROJECT_ROOT / "config"
  ```

Absolute paths should only appear in local, machine-specific configuration (e.g., a `.env` file or system environment
variable), never in committed Python code.

## Configuration & Environment Variables

Python code must be environment-independent. Configuration lives outside the code and is injected via:

- **Environment variables** (preferred for secrets and host/port info).
- **Project-level config files** (YAML/TOML) committed to the repo.
- **Local `.env` files** (never committed) for developer-specific overrides.

Recommended environment variables:

- `RE_ROOT` - absolute path to the local `<repo_name>` repo root.
- `POSTGIS_HOST` - usually `localhost` during local development.
- `POSTGIS_PORT` - usually `5432`.
- `POSTGIS_DB` - e.g., `<db_name>`.
- `POSTGIS_USER` - database user, e.g., `<db_user>`.
- `POSTGIS_PASSWORD` - database password (never checked into version control).

Example pattern using `python-dotenv`:

```python
import os
from pathlib import Path

from dotenv import load_dotenv

COMMENT: Load .env from repo or project root
ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

RE_ROOT = Path(os.environ["RE_ROOT"])

DB_HOST = os.getenv("POSTGIS_HOST", "localhost")
DB_PORT = int(os.getenv("POSTGIS_PORT", "5432"))
DB_NAME = os.getenv("POSTGIS_DB", "app_db")
DB_USER = os.getenv("POSTGIS_USER", "app_user")
DB_PASSWORD = os.getenv("POSTGIS_PASSWORD", "")
```

Rules:

- `.env` files must be listed in `.gitignore`.
- Only `.env.example` (with fake or placeholder values) may be committed.
- Python modules **must not** hard-code real passwords, tokens, or hostnames.

## Database Access

Python modules should access PostgreSQL/PostGIS using `psycopg2` or, preferably, SQLAlchemy.

### Recommended pattern (SQLAlchemy + psycopg2)

```python
from sqlalchemy import create_engine, text

DB_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(DB_URL, future=True)

def check_postgis_version() -> str:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT postgis_full_version();"))
        return result.scalar_one()
```

Guidelines:

- Do not shell out to `psql` from normal module code; use SQLAlchemy/psycopg2.
- Keep SQL in Python small, explicit, and parameterized.
- For complex, reusable SQL (schema, migrations, seeds), store `.sql` files under `00_Admin/db/migrations/` or
  module-specific `docs/sql/` and load them from there.

Database connections are considered **external infrastructure**. The repository stores:

- Connection patterns.
- Migrations.
- Example config.
- Tests that are explicit about required DB state.

## Module-Specific Extensions

If a module requires geospatial patterns or domain-specific libraries, reference the module guide:

- `../<work_repo>/02_Modules/gis_workflow/docs/guides/guide_python_gis_patterns.md`

```python
try:
    import geopandas as gpd
    import shapely
except ImportError as exc:
    raise RuntimeError(
        "This module requires the GIS stack (geopandas, shapely, etc.). "
        "Install the `gis-etl` Conda environment or the dependencies defined in environment.yml."
    ) from exc
```

Do not attempt to auto-install packages from within module code. Environment setup is handled by the environment guides,
not by runtime logic.

## Common Failure Patterns and Recovery

| Failure Pattern | Symptom | Recovery |
| --- | --- | --- |
| Hard-coded local paths | Works on one machine only | Replace with `Path(__file__).resolve()` rooted paths |
| Hidden environment assumptions | Script fails in new shell/session | Document env vars and add early validation |
| Non-deterministic outputs | Different results across runs | Pin sort/order logic and explicit output naming |
| Missing input validation | Late-stage runtime errors | Validate required files/args at script start |
| Re-raising without context | Unclear tracebacks | Use `raise ... from exc` with actionable message |

## Common Pitfalls Checklist (Required for Pipeline Scripts)

Before marking a script ready, verify all of the following:

- Geometry compatibility:
  - If your filter allows multiple geometry types (for example `Point` and
    `MultiPoint`), your downstream access pattern must safely handle each type.
  - If needed, normalize geometry first (for example explode multipart
    geometry into single-part features).
- Output scan safety:
  - If a script scans an output tree (`rglob`, recursive listing), explicitly
    exclude its own output artifact path(s) to avoid self-inclusion.
- Idempotency truth check:
  - If `CONTRACT["idempotent"]` is `True`, reruns must fully update all claimed
    fields/artifacts, not only a subset.
  - If full overwrite behavior is not implemented, document the partial behavior
    and set idempotency claims accordingly.

## Required for Multi-Step Pipelines: Script Contract Pattern (CONTRACT Dict)

When scripts participate in agent-chained workflows (e.g., milestone
pipelines where one script's output feeds another), scripts MUST export a
module-level `CONTRACT` dict. This is required for multi-step pipelines and
recommended for standalone scripts.

```python
CONTRACT = {
    "id": "gp_m2_manifest_build",         # stable manifest ID
    "filename": "build_map_output_manifest.py",
    "inputs": ["layer_catalog.yaml", "bbox_policy.yaml"],
    "outputs": ["map_output_manifest.yaml"],
    "crs": "EPSG:2264",
    "idempotent": True,
    "desktop_gis_required": False,
}
```

Benefits:

- Agents can read `CONTRACT` to discover inputs/outputs without parsing
  docstrings.
- Pipeline orchestrators can chain scripts by matching outputs to inputs.
- The `idempotent` flag signals whether re-runs are safe.
- The `desktop_gis_required` flag helps agents choose the right execution
  environment.

When using CONTRACT, keep the `id` field aligned with the authoritative
script manifest ID to maintain traceability.

Pipeline baseline requirements:

- Pipeline scripts MUST accept `--project-root` when they emit run artifacts.
- Pipeline scripts MUST write a run manifest under `admin/run_logs/` with
  inputs, outputs, script id, timestamp, and exit status.
- If business-logic parameters are consumed, run manifests MUST include either:
  - resolved parameter key/value pairs, or
  - a pointer to the resolved parameter manifest plus a stable checksum/hash.

## Parameter Authority in Scripts

Scripts that consume business-logic parameters (values affecting deliverable
content such as corridor widths, station intervals, or classification
thresholds) MUST follow the parameter authority contract (`C42`):

- **No hidden defaults for business-logic values.** Scripts must fail closed
  (exit non-zero with a clear message) when a required business parameter is
  missing, rather than silently using a fallback value.
- **Technical/runtime defaults are permitted** (e.g., thread count, log level,
  output format) when explicitly labeled as such in the script's `CONTRACT`
  dict or argparse help text.
- **Parameter source binding:** scripts must reference values from the
  **parameter manifest** (C42) or explicit CLI input parameters. Do not embed
  business values as Python literals unless they are labeled as canonical
  baselines and the parameter-manifest contract permits it.

Manifest terminology note:

- **Parameter manifest**: business-logic inputs and resolved values (C42).
- **Run manifest**: execution provenance/log output for a run.
- **Script manifest**: script catalog/metadata entry.

Example pattern:

```python
import argparse
import yaml

def load_manifest(path):
    with open(path) as f:
        return yaml.safe_load(f)

parser = argparse.ArgumentParser()
parser.add_argument("--manifest", required=True, help="Path to parameter manifest YAML")
parser.add_argument("--log-level", default="INFO", help="Runtime default: log verbosity")
args = parser.parse_args()

manifest = load_manifest(args.manifest)
row_width = manifest["parameters"]["required"]["row_width_total_ft"]
COMMENT: No hidden fallback; script fails if key is missing
```

## Runtime Dependency Gates (C35/C36)

Scripts with non-stdlib imports MUST support explicit runtime dependency gates
in workbook preflight sections.

Requirements:

- Declare critical runtime modules in script docs or `CONTRACT` metadata.
- Provide an import smoke-check command per module:
  - `python -c "import <module>; print(<module>.__name__)"`
- If a required import fails, treat as a blocking precondition failure.

Offline/limited-network environments:

- Support staged dependency installation from a wheelhouse or internal mirror.
- Prefer reproducible commands in workbook/runbook evidence:
  - `python -m pip install --no-index --find-links <wheelhouse> <package>`
- If online install remains allowed, declare mode as `hybrid` and document both
  code paths.

## CLI Contract Drift Compatibility (C33)

To support workbook CLI drift validation (`validate_workbook_cli_contracts.py`):

- Define argparse flags via `add_argument("--long-flag", ...)` with explicit
  long names for any parameter referenced in workbook command blocks.
- Avoid dynamic or runtime-generated flag names.
- When renaming/removing a CLI flag, update workbook command blocks in the same
  change and rerun the C33 validator.

## Basic vs Advanced Script Patterns

- **Basic (default):** single script, clear args, deterministic output.
- **Advanced (opt-in):** multi-step orchestration, concurrency, plugin hooks.

Always complete a basic passing version before adding advanced behavior.
