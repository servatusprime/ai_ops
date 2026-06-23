#!/usr/bin/env python3
"""Fixture runner for validate_repo_rules.py status/checklist behavior.

Proves, in-process against the sibling validator module:
- the live config parses >0 rules and an empty-rules config exits nonzero (fail-closed);
- the canonical five status values pass VS003 and any other value fails;
- fenced ``` # comments are not counted as H1 (count_h1);
- VS035: completed/active workbooks with unexplained open checklist items fail,
  planned/stub are exempt, and a fully-checked workbook passes;
- the exact R-6 forward-handoff allowance passes only for its listed open items,
  and every malformed/stale/over-broad allowance fails.

Exit 0 = every fixture behaved as expected; nonzero otherwise. No network, no writes
outside the system temp dir.
"""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
VALIDATOR = os.path.normpath(os.path.join(HERE, "..", "validate_repo_rules.py"))
CONFIG = os.path.normpath(os.path.join(HERE, "..", "..", "configs", "validator", "validator_config.yaml"))

failures: list[str] = []


def load():
    spec = importlib.util.spec_from_file_location("rsv_under_test", VALIDATOR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check(name: str, cond: bool) -> None:
    print(f"  [{'ok  ' if cond else 'FAIL'}] {name}")
    if not cond:
        failures.append(name)


def _tmp(text: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".md")
    os.close(fd)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    return path


def wb(status: str, body: str, allowance: str = "") -> str:
    return f"---\ntitle: T\nid: wb_fix_01\nstatus: {status}\n{allowance}---\n\n# Title\n\n{body}\n"


def run_vs035(mod, text: str) -> list[str]:
    path = _tmp(text)
    errs: list[str] = []
    try:
        mod.check_status_vs_checklist([path], errs, "VS035")
    finally:
        os.remove(path)
    return errs


def run_vs003(mod, status: str) -> list[str]:
    path = _tmp(f"---\nstatus: {status}\n---\n# T\n")
    errs: list[str] = []
    try:
        mod.check_status_values([path], errs)
    finally:
        os.remove(path)
    return errs


def main() -> int:
    mod = load()

    # 1. status enum (VS003)
    for good in ["planned", "stub", "active", "completed", "deprecated"]:
        check(f"VS003 accepts '{good}'", not run_vs003(mod, good))
    for bad in ["complete", "final", "draft_noncanonical", "superseded"]:
        check(f"VS003 rejects '{bad}'", bool(run_vs003(mod, bad)))

    # 2. count_h1 fenced-code awareness
    check("count_h1 ignores fenced # comments", mod.count_h1("# Real\n\n```\n# fake\n```\n") == 1)

    # 3. VS035 base behavior
    check("VS035 completed + open item -> fail", bool(run_vs035(mod, wb("completed", "- [ ] do thing"))))
    check("VS035 active + open item -> fail", bool(run_vs035(mod, wb("active", "- [ ] do thing"))))
    check("VS035 planned + open item -> exempt", not run_vs035(mod, wb("planned", "- [ ] do thing")))
    check("VS035 stub + open item -> exempt", not run_vs035(mod, wb("stub", "- [ ] do thing")))
    check("VS035 completed + all checked -> pass", not run_vs035(mod, wb("completed", "- [x] done")))

    # 4. R-6 forward-handoff allowance: exact pass + every failure mode
    good = (
        "checklist_allowance:\n  kind: forward_handoff\n  target_artifact: wb_fix_01\n"
        "  open_items:\n    - do thing\n  rationale: ownership moves to M5\n"
    )
    check("R-6 exact allowance -> pass", not run_vs035(mod, wb("completed", "- [ ] do thing", good)))
    bad_kind = (
        "checklist_allowance:\n  kind: sideways\n  target_artifact: wb_fix_01\n"
        "  open_items:\n    - do thing\n  rationale: x\n"
    )
    check("R-6 unsupported kind -> fail", bool(run_vs035(mod, wb("completed", "- [ ] do thing", bad_kind))))
    missing_target = (
        "checklist_allowance:\n  kind: forward_handoff\n  open_items:\n    - do thing\n  rationale: x\n"
    )
    check("R-6 missing target -> fail", bool(run_vs035(mod, wb("completed", "- [ ] do thing", missing_target))))
    unknown_target = (
        "checklist_allowance:\n  kind: forward_handoff\n  target_artifact: wb_other\n"
        "  open_items:\n    - do thing\n  rationale: x\n"
    )
    check("R-6 unknown target -> fail", bool(run_vs035(mod, wb("completed", "- [ ] do thing", unknown_target))))
    empty_rationale = (
        "checklist_allowance:\n  kind: forward_handoff\n  target_artifact: wb_fix_01\n"
        "  open_items:\n    - do thing\n  rationale:\n"
    )
    check("R-6 empty rationale -> fail", bool(run_vs035(mod, wb("completed", "- [ ] do thing", empty_rationale))))
    dupe = (
        "checklist_allowance:\n  kind: forward_handoff\n  target_artifact: wb_fix_01\n"
        "  open_items:\n    - do thing\n    - do thing\n  rationale: x\n"
    )
    check("R-6 duplicate items -> fail", bool(run_vs035(mod, wb("completed", "- [ ] do thing", dupe))))
    stale = (
        "checklist_allowance:\n  kind: forward_handoff\n  target_artifact: wb_fix_01\n"
        "  open_items:\n    - nonexistent item\n  rationale: x\n"
    )
    check("R-6 listed-but-not-open -> fail", bool(run_vs035(mod, wb("completed", "- [ ] do thing", stale))))
    over_broad = (
        "checklist_allowance:\n  kind: forward_handoff\n  target_artifact: wb_fix_01\n"
        "  open_items:\n    - do thing\n  rationale: x\n"
    )
    check(
        "R-6 unlisted open item still fails",
        bool(run_vs035(mod, wb("completed", "- [ ] do thing\n- [ ] other thing", over_broad))),
    )

    # 5. config parse + empty-rules fail-closed guard
    check("live config parses >0 rules", len(mod.parse_config(CONFIG).get("rules", [])) > 0)
    empty_cfg = _tmp("version: 0\nrules:\n")
    try:
        proc = subprocess.run(
            [sys.executable, VALIDATOR, "--config", empty_cfg],
            capture_output=True,
            text=True,
            cwd=os.path.normpath(os.path.join(HERE, "..", "..", "..")),
        )
        check("empty-rules config exits nonzero (fail-closed)", proc.returncode != 0)
    finally:
        os.remove(empty_cfg)

    if failures:
        print(f"\nFIXTURE FAILURES: {len(failures)} -> {failures}")
        return 1
    print("\nALL FIXTURES BEHAVED AS EXPECTED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
