---
title: test_manifests_readme
version: 0.2.0
status: active
author: chatgpt
owner: ai_ops
created: 2026-02-25
updated: 2026-02-28
ai_generated: true
core_doc_exempt: false
---

# Test Manifests

Test fixtures for bootstrap validation lanes (see [rb_bootstrap.md](../../../runbooks/rb_bootstrap.md)).

## Valid Manifests

### valid_minimal.yaml

Historical aiops.yaml fixture — retained for reference. Bootstrap now uses AGENTS.md.

Original: Minimal valid manifest with only required fields:

- version (semantic version string)
- manifest_version (semantic version string)
- data_version (semantic version string)
- bootstrap.read_order (array of file paths)

Use for: Testing minimal endpoint contract (TS-16).

### valid_full.yaml

Historical aiops.yaml fixture — retained for reference. Bootstrap now uses AGENTS.md.

Original: Complete manifest with all optional fields populated:

- bootstrap.bootstrap_guide
- bootstrap.bootstrap_guide_min_version
- bootstrap.fallback_rules
- work_context
- customizations
- resource_resolution
- workspace

Use for: Testing full feature set, verifying optional field handling.

## Invalid Manifests

### invalid_syntax.yaml

Invalid YAML syntax:

- Missing closing bracket in list
- Incorrect indentation

Use for: Testing YAML parse error handling (TS-04)

Expected behavior: Agent detects parse error, enters safe-mode, reports line number

### invalid_schema.yaml

Valid YAML but missing required fields:

- No `version`
- No `manifest_version`
- No `data_version`
- No `bootstrap` section

Use for: Testing schema validation (TS-04, TS-12)

Expected behavior: Agent validates schema, reports missing required fields, enters safe-mode

### invalid_paths.yaml

Valid schema but references non-existent files:

- NONEXISTENT_FILE.md in required_reading
- invalid_directory/ in scan_paths
- Missing profile and script files

Use for: Testing path validation

Expected behavior: Agent warns about missing files, may continue with available files or enter safe-mode depending on criticality

### invalid_legacy_work_context_keys.yaml

Valid YAML, but uses deprecated `work_context` fields:

- `active_work_programs` (deprecated)
- `checkpoints[].packet_id` (deprecated)

Use for: Testing hard-cutover schema behavior for `work_context`.

Expected behavior: Schema validation fails on additional/deprecated keys.

## Testing Usage

To test manifest validation:

### Historical: aiops.yaml schema validation

The dedicated `aiops.yaml` schema file has been removed from active governance.
These fixtures are retained only as historical bootstrap artifacts.

**Bootstrap testing** (copy manifest to root):

```powershell
# Copy test manifest to repo root
# Bootstrap now uses AGENTS.md as primary entry point.
# aiops.yaml fixtures are retained as historical reference only.
```

Note: `op_validate_config.py` validates customization configs, not manifests.
Dedicated manifest validator script is a future enhancement.

## References

- [rb_bootstrap.md](../../../runbooks/rb_bootstrap.md) - Bootstrap validation scenarios (including fixture lane)
- [guide_bootstrap_self_repair.md](../../../guides/ai_operations/guide_bootstrap_self_repair.md) - Recovery workflows
