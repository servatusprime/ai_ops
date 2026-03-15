---
title: Guide: File Placement (ai_ops)
version: 0.2.4
status: active
license: Apache-2.0
last_updated: 2026-03-14
owner: ai_ops
---

# File Placement Guide

**Scope:** Repo-agnostic guidance. Replace `<work_repo>` with your target repo root.

## Purpose

Define explicit rules for where files belong in the repository. Reduces ambiguity for AI agents and humans when creating
or organizing content.

## Core Principle: Context Downstream

**Place information as close as possible to where it's used.**

This minimizes agent cognitive load by loading only necessary context at each scope level.

## Module Documentation Pattern

**Standard pattern**: `02_Modules/<module>/docs/` with optional subfolders:

- `docs/specs/` - Formal specifications
- `docs/guides/` - Explanatory documentation
- `docs/runbooks/` - Procedural workflows (optional; not all modules include runbooks yet)
- `docs/contracts/` - Module-level contracts (optional)

**Example (ASCII tree)**:

```text
<work_repo>/02_Modules/gis_workflow/
|-- docs/
|   |-- specs/
|   |   `-- spec_gis_workflow.md
|   `-- guides/
|       `-- guide_layer_naming.md
```

This keeps "guide", "spec", "runbook" as artifact types, not competing root folders.

## Placement Heuristic

Ask: **"How many different contexts need this information?"**

| Answer | Location | Examples |
| --- | --- | --- |
| **All contexts** | `00_Admin/policies/` or `00_Admin/specs/` | Naming conventions, git workflow, status values |
| **Multiple modules** | `00_Admin/guides/` or `01_Resources/` | AI Ops Stack, repo structure, document templates |
| **Single module** | `02_Modules/<module>/docs/` | GIS layer naming, module-specific scenario patterns |
| **Single operation** | Co-located with operation | Tool usage docs, script parameters |

## By Content Type

### Policies (Hard Rules)

**Location**: `00_Admin/policies/`

**Characteristics**:

- Uses MUST/MUST NOT language
- Enforced by requestor review/judgment
- Violations require context to evaluate
- Changes via governance process

**Examples**:

- `policy_naming_conventions.md`
- `policy_git_workflow_conventions.md`
- `policy_status_values.md`

### Specs (Descriptive Requirements)

**Location**: `00_Admin/specs/` (cross-cutting) or `02_Modules/<module>/docs/specs/` (module-specific)

**Characteristics**:

- Descriptive requirements document
- May or may not be enforced
- Defines WHAT should be true
- Technical/structural requirements
- Versioned and stable

**Examples**:

- `00_Admin/specs/spec_repo_metadata_standard.md`
- `<work_repo>/02_Modules/gis_workflow/docs/specs/spec_gis_workflow.md`

**Note**: Specs are not automatically validated. See Contracts below for enforced specs.

### Contracts (Machine-Enforced Specs)

**Location**: `<work_repo>/01_Resources/<domain_core>/contracts/` (engine-level) or
`02_Modules/<module>/docs/contracts/` (module-level)

**Characteristics**:

- **Specs with machine-enforced validation** (key distinction)
- Binary pass/fail validation
- Data schemas, interface definitions
- Versioned with breaking change management
- Has associated validator code

**One-liner**: "Contracts are specs with machine-enforced checks."

**Examples**:

- `<work_repo>/01_Resources/<domain_core>/contracts/spec_contract_zle_to_fle_v0_1_0.md`
- `schema_zle_fle_exchange_v0_1_0.yaml` (schema = contract)

### Guides (Explanatory Documentation)

**Location**: `00_Admin/guides/` (cross-cutting) or `02_Modules/<module>/docs/guides/` (module-specific)

**Characteristics**:

- Explanatory, instructional
- Uses SHOULD/RECOMMENDED language
- Provides context and examples
- Evolves with practice

**Examples**:

- `00_Admin/guides/ai_operations/guide_ai_operations_stack.md`
- `00_Admin/guides/architecture/guide_repository_structure.md`
- `<work_repo>/02_Modules/gis_workflow/docs/guides/guide_gis_data_source_discovery.md`

### Runbooks (Reusable Procedures)

**Location**: `00_Admin/runbooks/` (cross-cutting) or `02_Modules/<module>/docs/runbooks/` (module-specific)

**Characteristics**:

- Reusable execution workflows
- Step-by-step procedures
- Parameterized for different contexts
- Used repeatedly

**Examples**:

- `00_Admin/runbooks/rb_repo_health_review.md`
- `00_Admin/runbooks/rb_commit_push_streamlining_01.md`

Run-family containers:

- Runbundle (group of runbooks for one bounded run lane):
  `00_Admin/runbooks/run_program_<id>/run_bundles/rnb_<bundle_name>/`
  or module-local equivalents.
- Runprogram (program-level run-family coordination):
  `00_Admin/runbooks/run_program_<id>/` or
  `02_Modules/<module>/docs/runbooks/run_program_<id>/`.

### Workbooks (Single-Run Execution)

**Location**: `90_Sandbox/ai_workbooks/`

**Characteristics**:

- Single-use, committed execution plan
- Immutable after approval
- Specific assumptions and scope
- Archived after execution

**Examples**:

- `90_Sandbox/ai_workbooks/wb_ai_ops_vocab_repo_org_01.md`
- `90_Sandbox/ai_workbooks/wb_sandbox_cleanup_02_execute.md`

Work-family containers:

- Workbundle (group of workbook + companion artifacts):
  `90_Sandbox/ai_workbooks/wb_<id>_<YYYY-MM-DD>/`
  or `.../work_program_<id>/work_packets/wb_<id>_<YYYY-MM-DD>/`.
- Workprogram (program-level work-family coordination):
  `90_Sandbox/ai_workbooks/work_program_<id>/`.
- Pipeline artifacts are optional queue mirrors and should be co-located with
  the bundle/program root; execution spine remains gate/authority source when
  both exist.

## By Scope

### Cross-Cutting (Affects All Modules)

**Location**: `00_Admin/`

**Test**: Would ALL modules/projects be affected by changes to this?

**Examples**:

- Naming conventions
- Git workflow
- AI Operations Stack terminology
- Repository structure

### Shared Across Multiple Modules

**Location**: `01_Resources/` or `00_Admin/guides/`

**Test**: Would SOME modules/projects reference this?

**Examples**:

- Document templates (`01_Resources/templates/`)
- Data source catalogs (`<work_repo>/01_Resources/data_sources/`)
- Glossary (`<work_repo>/01_Resources/guides/glossary.md`)

### Module-Specific

**Location**: `02_Modules/<module>/`

**Test**: Does only ONE module need this?

**Examples**:

- GIS canonical layer ID pattern
- Module-specific scenario naming
- Module-specific workbook structure

### Project-Specific

**Location**: `<work_repo>/Projects/<project>/`

**Test**: Does only THIS project need this?

**Canonical suitcase layout**:

```text
<work_repo>/Projects/<project>/
  admin/run_logs/
  docs/
  inputs/{data,gis_project,resources/{connections,layouts,styles}}
  outputs/exports/{pdf,shp,points,reports}
```

**Examples**:

- Project-specific configuration
- Project execution logs
- Project deliverables
- Project metadata contract (`project_metadata.yaml`) with web-bridge keys
  (`project_id`, `storage_prefix`, `crs`, `aoi_source`,
  `data_contract_version`)

## By Lifecycle Tier

### Governance (Permanent, Slow-Changing)

**Location**: `00_Admin/policies/`, `00_Admin/specs/`, `00_Admin/decisions/`

**Characteristics**:

- Changes via deliberate governance process
- Affects future work
- Permanent retention

**Examples**:

- Policies, specs, contracts
- Promoted decisions from decision_ledger.md
- Architectural intent maps

### Reference (Stable, Evolving)

**Location**: `00_Admin/guides/`, `01_Resources/`

**Characteristics**:

- Evolves with practice
- Long-term retention
- Archived when superseded

**Examples**:

- Guides, runbooks, templates
- Data catalogs, glossaries

### Commitment (Frozen for Execution)

**Location**: `90_Sandbox/ai_workbooks/`

**Characteristics**:

- Immutable after approval
- Single-run execution
- Archived after completion

**Examples**:

- Workbooks, execution spines

### Ephemeral (Temporary, Disposable)

**Location**: `00_Admin/logs/`, `90_Sandbox/health_reports/`, `90_Sandbox/`

**Characteristics**:

- Changes frequently
- Short-term retention
- Can be purged or archived

**Examples**:

- Execution logs, audit traces
- Temporary analysis, draft artifacts

## Operational Surface Boundaries

Use these contracts to reduce overlap and placement drift:

- `00_Admin/scripts/`: reusable executable helpers for core workflows.
  Domain-specific executables belong in `<work_repo>/tools/`.
- `00_Admin/tooling/`: tooling docs/index for core surfaces only.
  Domain-specific tooling docs/manifests belong in
  `<work_repo>/00_Admin/tooling/`.
- `01_Resources/prompts/`: reusable prompt assets.
- `00_Admin/runbooks/`: executable operational playbooks.
- `00_Admin/scripts/`: script helpers with explicit runbook/workflow consumers.
- `00_Admin/tests/`: validator behavior checks and executable contract tests.
- `01_Agents/` (optional): control-plane metadata only (registry, bindings,
  runtime maps); user-selected local runtime values belong under
  `.ai_ops/local/**`.

Every retained surface should have explicit owner, trigger, and consumer.

## Special Cases

### Prompts

**Two locations based on purpose:**

**Admin-level prompts**: `00_Admin/prompts/`

- Repository governance/operations
- Audit and maintenance

**Workflow starter prompts**: `<work_repo>/01_Resources/prompts/`

- Human-initiated workflows
- Reusable across projects
- Organized by workflow family or domain (for example `analysis/`, `design/`, `modeling/`)
- Example: `prompts/design/prompt_gemini_concept_styling.md`

**Module-specific prompts**: `02_Modules/<module>/docs/prompts/`

- Only when needed for specific operations
- Co-located with the operations that use them

### Templates vs Examples

**Templates**: `01_Resources/templates/`

- Blank starting points
- To be copied and filled in
- Example: `templates/documents/spec-template.md`

**Examples**: `02_Modules/<module>/examples/` or sandbox workbundle draft examples under
`90_Sandbox/ai_workbooks/`

- Filled-in demonstrations
- Reference implementations
- Example: Sample GeoJSON, example workbook

**When to consult examples:**

| Trigger | Action |
| --- | --- |
| Creating a new artifact type | Check module `examples/` first; if none exist, use sandbox draft examples. |
| First time using a module | Check `<module>/examples/` for usage patterns. |
| Unclear on format or structure | Prefer examples over inferring from templates. |
| Authoring a workflow or command wrapper | Check `01_Resources/templates/workflows/` for patterns. |

If no example exists, note the gap and consider creating one after successful implementation.

Repository preference: keep temporary sample artifacts in sandbox workbundles rather than a canonical
samples folder under `01_Resources/`.

**Note**: Templates are in `01_Resources/`, NOT `00_Admin/templates/` (which does not exist).

### Planning Outputs vs Templates vs Workbooks

**Planning Outputs**: required commitment framing (assumptions, risks, success
criteria, planning checklist) embedded in workbooks/runbooks.

- Location: inside active workbook/runbook artifacts.

**Template**: reusable blank scaffold for authoring.

- Location: `01_Resources/templates/`
- Example: `01_Resources/templates/workflows/wb_template_generic.md`

**Workbook**: single-run execution artifact (`wb_` prefix).

- Location: `90_Sandbox/ai_workbooks/`
- Example: `90_Sandbox/ai_workbooks/wb_repo_consistency_cleanup_01.md`

### Research vs Reports

**Research**: `00_Admin/research/`

- Exploratory analysis
- Vendor evaluations
- Background investigation
- Example: `research/vendor_case_a/`

**Reports (persistent)**: `00_Admin/reports/`

- Permanent sweep summaries
- Long-lived governance reports

**Reports (run-scoped)**: `90_Sandbox/health_reports/`

- Health check outputs (`/health`)
- On-demand audit runs
- Ephemeral; manually purged

### Decisions vs Audit

**Decisions**: `00_Admin/decisions/`

- Permanent governance decisions
- Architectural intent
- Promoted from workbooks
- Example: `decision_ledger.md`, `<work_repo>/00_Admin/decisions/intent_structure_map.yaml`

**Audit (run-scoped)**: `90_Sandbox/health_reports/`

- Temporary audit artifacts
- Traces, sentinels, reflections
- Can be archived/purged
- Example: `repo_audit_reflection.md`

## Decision Tree

```text
START: New file needs placement
    |
    v
Is this a single-run execution plan?
    YES -> 90_Sandbox/ai_workbooks/
    NO  |
        v
Is this module-specific or project-specific?
    MODULE  -> 02_Modules/<module>/docs/
    PROJECT -> <work_repo>/Projects/<project>/
    NEITHER |
            v
What type of artifact?
    POLICY    -> 00_Admin/policies/
    SPEC      -> 00_Admin/specs/
    CONTRACT  -> <work_repo>/01_Resources/<domain_core>/contracts/
    GUIDE     -> 00_Admin/guides/
    RUNBOOK   -> 00_Admin/runbooks/
    TEMPLATE  -> 01_Resources/templates/
    LOG       -> 00_Admin/logs/
    DECISION  -> 00_Admin/decisions/
    AUDIT     -> 90_Sandbox/health_reports/
    REPORT (persistent) -> 00_Admin/reports/
    REPORT (run-scoped) -> 90_Sandbox/health_reports/
    RESEARCH  -> 00_Admin/research/
    PROMPT    -> [See Special Cases above]
```

## Anti-Patterns

### Do not: Put module-specific rules in global policies

**Example**: GIS layer naming pattern in `policy_naming_conventions.md`

**Do instead**: Reference the module guide from global policy

```markdown
## Module-Specific Naming
Modules MAY define additional naming conventions:
- GIS: See <work_repo>/02_Modules/gis_workflow/docs/guides/guide_layer_naming.md
```

### Do not: Duplicate content across locations

**Example**: Same glossary terms in both `<work_repo>/01_Resources/guides/glossary.md` and module docs

**Do instead**: Single canonical glossary, modules reference it

### Do not: Mix lifecycle tiers in same directory

**Example**: Permanent decisions and temporary audits both in `/context/`

**Do instead**: Separate by lifecycle (decisions/ vs reports/audit/)

### Do not: Create directories without clear purpose

**Example**: Empty `templates/metadata/` folder containing only a README.md placeholder

**Do instead**: Do not pre-create directories as empty placeholders. Create the
directory only when the first real governed artifact is placed there. Document
optional directory patterns in the parent README or in
`guide_repository_structure.md §3.0.1` instead of using placeholder READMEs.

The following are known optional directories that follow creation-on-first-real-asset policy:

- `00_Admin/prompts/` — create when first admin-level prompt artifact is placed
- `01_Resources/guides/` — create when first cross-cutting resource guide is placed
- `01_Resources/templates/metadata/` — create when first template metadata sidecar is placed

## Examples

### Good Placement: Context Downstream

**Global naming rule** (all contexts need it):

```text
Location: 00_Admin/policies/policy_naming_conventions.md
Content: "Use snake_case for all file names"
```

**GIS-specific naming** (GIS module needs it):

```text
Location: <work_repo>/02_Modules/gis_workflow/docs/guides/guide_layer_naming.md
Content: "Canonical layer IDs: <scope>_<category>_<specific>__<id>"
```

**Tool-specific usage** (only this tool needs it):

```text
Location: In script docstring or <work_repo>/02_Modules/gis_workflow/operations/README.md
Content: "op_validate_layer_metadata.py expects path and outputs pass/fail"
```

### Bad Placement: Upstream Bloat

**Bad**: Put every module's naming rules in global policy

```text
00_Admin/policies/policy_naming_conventions.md:
- General snake_case rule
- GIS layer ID pattern
- Module-specific scenario naming
- Module-specific workbook structure
- (50+ module-specific rules)
```

**Good**: Global policy + module references

```text
00_Admin/policies/policy_naming_conventions.md:
- General snake_case rule
- Reference to module-specific guides

<work_repo>/02_Modules/gis_workflow/docs/guides/guide_layer_naming.md:
- GIS layer ID pattern

<work_repo>/02_Modules/<module>/docs/guides/guide_scenario_naming.md:
- Module-specific scenario naming
```

## Validation Questions

When placing a file, ask yourself:

1. **Scope**: How many contexts need this? (All, multiple, one)
2. **Type**: What kind of artifact is this? (Policy, guide, spec, etc.)
3. **Lifecycle**: How permanent is this? (Governance, reference, ephemeral)
4. **Audience**: Who/what consumes this? (Humans, agents, specific module)
5. **Downstream**: Can this live closer to where it's used?

If answers are unclear, default to **more specific** (downstream) rather than global.

## Future Evolution

As the repository grows:

- These rules may be formalized into automated validation
- Additional heuristics may be needed for complex cases
- Folder structure may evolve based on observed patterns

**Philosophy**: Build on evidence, not anticipation. Add complexity when problems emerge.
