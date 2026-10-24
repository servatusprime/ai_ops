---
title: Orphaned Scripts - Archived 2026-08-26
version: 0.1.0
status: active
owner: ai_ops
---

# Orphaned Scripts - Archived 2026-08-26

Scripts confirmed to have zero live references anywhere in the repo (no
pre-commit hook, no CI workflow, no other script, no guide/spec/workflow
cross-reference), found during an Opus-led orphaned-file audit.

- `op_load_profile.py` -- a rider/crew profile loader stub from the repo's
  initial commit (`fa49d0e`, single commit in its whole history). Superseded
  by the real, wired-in profile system: `00_Admin/scripts/regenerate_profiles.py`
  (deterministic profile-derived behavior file generation, run via the
  `release-quality gate` and the `/profiles` skill). Referenced a
  `02_Modules/01_agent_profiles/profiles/` path pattern that the real system
  never adopted; profile schema notes in the docstring were never completed.
