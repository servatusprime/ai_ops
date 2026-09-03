# Pull Request

## Summary

## Scope

## Changes

## Validation

Note: `pre-commit run --all-files` does NOT run the `stages: [manual]` hooks
(`ai-ops-validator`, `ai-ops-pending-check`) -- checking that box alone does
not cover repo-rules validation. The `validate_repo_rules.py` line below is
required separately; it is not redundant with the line above it.

- [ ] Not run (explain why)
- [ ] `pre-commit run --all-files`
- [ ] `python 00_Admin/scripts/validate_repo_rules.py --config 00_Admin/configs/validator/validator_config.yaml`
- [ ] `markdownlint <paths>`

## Authority

- [ ] Level 0 (read-only)
- [ ] Level 1 (single atomic edit)
- [ ] Level 2 (2-5 related edits)
- [ ] Level 3 (workbook-executed)
- [ ] Level 4 (policy/spec/architecture; requires work proposal)

## Checklist

- [ ] Scope matches approved workbook or request
- [ ] Evidence recorded in workbook or logs
- [ ] Crosscheck completed or explicitly deferred
- [ ] No protected-path edits without approval
