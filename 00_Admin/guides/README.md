---
title: Guides Index
version: 1.0.3
status: active
license: Apache-2.0
created: 2026-01-13
last_updated: 2026-03-04
owner: ai_ops
description: Navigation for guides organized by topic
---

<!-- markdownlint-disable-next-line MD025 -->
# Guides Index

Guides are explanatory documentation (SHOULD/RECOMMENDED) that evolve with practice.

## Navigation by Topic

### AI Operations (Critical for Agents)

Location: `ai_operations/`

- `guide_ai_operations_stack.md` - Master guide (axes, roles, handoffs)
- `guide_workflows.md` - Intent/Commitment/Execution
- `guide_contracts.md` - Verification-first contracts
- `guide_ai_ops_vocabulary.md` - Canonical terminology
- `guide_bootstrap_verification_checklist.md` - Bootstrap verification for Level 3+ work
- `guide_authority_decision_tree.md` - Authority level determination flowchart
- `guide_work_proposals.md` - Level 4 work proposal requirements
- `guide_execution_spines.md` - Execution spine structure and gates
- `guide_work_programs.md` - Workprogram orchestration guidance
- `guide_run_programs.md` - Runprogram orchestration guidance
- `guide_workflow_registries.md` - Registry patterns for work/run programs
- `guide_feedback_intake.md` - Intake and triage loop for feedback
- `guide_alignment_notes.md` - Cross-guide/policy alignment note pattern
- `guide_parallel_execution.md` - Guardrails for safe parallel execution
- `guide_ai_compatibility_matrix.md` - Capability matrix for AI tools and lanes
- `guide_ai_facing_protocol.md` - AI-facing communication protocol reference
- `guide_bootstrap_self_repair.md` - Bootstrap drift diagnosis and self-repair flow
- `guide_capability_certification.md` - Certification checks for bootstrap readiness
- `guide_command_workflows.md` - Command-to-workflow mapping and execution model
- `guide_design_tests.md` - Design test patterns for governance content quality
- `guide_execution_orchestration.md` - Execution lifecycle and orchestration guidance
- `guide_multi_agent_coordination.md` - Coordination rules for concurrent agents
- `guide_native_command_comparison.md` - Comparative reference for native command lanes
- `guide_repository_indices.md` - Repository index design and maintenance guidance
- `guide_scratchpad_usage.md` - Scratchpad usage patterns and guardrails
- `guide_skills_commands_classification.md` - Classification reference for skills and commands

Start here if you are an AI agent.

### Architecture and Structure

Location: `architecture/`

- `guide_repository_structure.md` - Directory layout and purpose
- `guide_aiops_agent_endpoint.md` - Agent endpoint contract and onboarding paths
- `guide_bootstrap_algorithm.md` - Bootstrap decision tree and fallback rules
- `guide_design_and_philosophy.md` - Design goals and operating philosophy for ai_ops
- `guide_naming_conventions.md` - File and folder naming rules
- `guide_naming_architecture.md` - Module IDs and canonical tokens
- `guide_file_placement.md` - Where files belong (context locality)
- `guide_environment_and_mode_selection.md` - Execution environment decision tree

### Authoring and Formatting

Location: `authoring/`

- `guide_markdown_authoring.md` - Markdown rules and conventions
- `guide_yaml_authoring.md` - YAML structure and validation
- `guide_json_authoring.md` - JSON formatting rules
- `guide_python_authoring.md` - Python coding standards
- `guide_sql_authoring.md` - SQL formatting and style
- `guide_spec.md` - How to write specifications
- `guide_prompt_authoring.md` - Prompt design patterns
- `guide_readme_authoring.md` - README authoring conventions
- `guide_runbooks.md` - Runbook authoring and structure
- `guide_workbooks.md` - Workbook creation and execution
- `guide_ai_assistants.md` - Working with external AI outputs
- `guide_changelog_conventions.md` - Changelog placement and entry pattern
- `guide_requirements_matrix.md` - Requirements matrix structure and cadence

### Tooling and Environment

Location: `tooling/`

- `guide_environment_setup.md` - Development environment configuration
- `guide_markdownlint_handling.md` - Lint execution and fallback handling
- Sandbox workbook workflow guidance now lives in `authoring/guide_ai_assistants.md`

### Other Guides

Root level:

- `guide_ide_extensions.md` - IDE extensions and behavior standards
- `guide_ide_config.md` - Deprecated compatibility pointer
- Runbooks index: `00_Admin/runbooks/README.md`

## Guide Characteristics

All guides:

- Use SHOULD/RECOMMENDED language
- Provide context and examples
- Evolve with practice
- Are versioned
- Archived when superseded

## Reading Strategy

For agents (systematic):

1. Start with AI Operations guides
2. Read Architecture guides for structure
3. Consult Authoring guides per artifact type
4. Reference Tooling guides as needed

For humans (exploratory):

- Browse by topic
- Use search for specific questions
- Bookmark frequently referenced guides

## Module-Specific Guides

Global guides live here. Module-specific guides live in:

- `02_Modules/<module>/docs/guides/`

Examples:

- GIS layer naming: `../<work_repo>/02_Modules/gis_workflow/docs/guides/`
- Module scenario guidance: `../<work_repo>/02_Modules/<module>/docs/guides/`
- Desktop GIS authoring: `../<work_repo>/02_Modules/gis_workflow/docs/guides/guide_gis_desktop_authoring.md`

## See Also

- Policies: `00_Admin/policies/README.md` (hard rules)
- Specs: `00_Admin/specs/README.md` (requirements)
- Runbooks: `00_Admin/runbooks/` (procedures)
