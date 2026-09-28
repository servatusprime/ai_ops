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
- VS015 rejects arbitrary configured executables and altered trusted-tool hashes,
  while the pinned markdownlint command passes a legitimate fixture.

Exit 0 = every fixture behaved as expected; nonzero otherwise. No network, no writes
outside the system temp dir.
"""
from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
VALIDATOR = os.path.normpath(os.path.join(HERE, "..", "validate_repo_rules.py"))
CONFIG = os.path.normpath(os.path.join(HERE, "..", "..", "configs", "validator", "validator_config.yaml"))
PROFILE_GENERATOR = os.path.normpath(os.path.join(HERE, "..", "regenerate_profiles.py"))

failures: list[str] = []


def load():
    spec = importlib.util.spec_from_file_location("rsv_under_test", VALIDATOR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_profile_generator():
    spec = importlib.util.spec_from_file_location("profiles_under_test", PROFILE_GENERATOR)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
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


def run_markdownlint(mod, params: dict, repo_root: str) -> list[str]:
    fd, path = tempfile.mkstemp(suffix=".md", dir=repo_root)
    os.close(fd)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("# Fixture\n\nBody.\n")
    errs: list[str] = []
    try:
        mod.check_markdownlint([path], errs, params, repo_root)
    finally:
        os.remove(path)
    return errs


def run_lexical_reparse_fixture(mod) -> bool:
    root = tempfile.mkdtemp(prefix="validator-reparse-")
    try:
        root_path = os.path.abspath(root)
        target = os.path.join(root_path, "target")
        junction = os.path.join(root_path, "link")
        os.makedirs(target)
        with open(os.path.join(target, "safe.txt"), "w", encoding="utf-8") as handle:
            handle.write("safe\n")
        result = subprocess.run(
            ["cmd.exe", "/c", "mklink", "/J", junction, target],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return False
        try:
            mod._validate_repo_path(os.path.join(junction, "safe.txt"), root_path, label="fixture")
        except ValueError as exc:
            return "reparse" in str(exc).lower()
        return False
    finally:
        shutil.rmtree(root, ignore_errors=True)


def run_vs036_override_fixtures(mod) -> tuple[bool, bool]:
    """Prove target config cannot execute in-root or traversal helper overrides."""
    with tempfile.TemporaryDirectory(prefix="validator-vs036-target-") as sandbox:
        root = os.path.join(sandbox, "target_repo")
        os.makedirs(root)
        marker = os.path.join(root, "executed.txt")
        outside = sandbox
        in_root_script = os.path.join(root, "chosen_validator.py")
        traversal_script = os.path.join(outside, "chosen_generator.py")
        payload = f"from pathlib import Path\nPath({marker!r}).write_text('executed')\n"
        for path in (in_root_script, traversal_script):
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(payload)

        trusted_scripts = os.path.dirname(os.path.abspath(mod.__file__))
        fixed_pair = {
            os.path.normcase(os.path.join(trusted_scripts, "validate_run_family_graph.py")),
            os.path.normcase(os.path.join(trusted_scripts, "generate_run_family_views.py")),
        }

        def probe(params: dict) -> bool:
            errors: list[str] = []
            seen: list[list[str]] = []

            def fake_run(command, **kwargs):
                seen.append(command)
                return subprocess.CompletedProcess(command, 0, "", "")

            with mock.patch.object(mod.subprocess, "run", side_effect=fake_run):
                mod.check_run_family_graph_contract(params, root, errors)
            launched = {os.path.normcase(command[1]) for command in seen}
            return (
                not errors
                and len(seen) == 2
                and launched == fixed_pair
                and not os.path.exists(marker)
            )

        in_root_safe = probe(
            {"validator_script": os.path.basename(in_root_script),
             "generator_script": os.path.basename(in_root_script)}
        )
        traversal_safe = probe(
            {"validator_script": os.path.relpath(in_root_script, root),
             "generator_script": os.path.relpath(traversal_script, root)}
        )
        return in_root_safe, traversal_safe


def run_vs036_reparse_fixture(mod) -> bool:
    """Reject a fixed helper reached through a reparse-linked trusted subtree."""
    with tempfile.TemporaryDirectory(prefix="validator-vs036-reparse-") as temp:
        trusted_root = os.path.join(temp, "trusted_aiops")
        admin = os.path.join(trusted_root, "00_Admin")
        scripts_link = os.path.join(admin, "scripts")
        external_scripts = os.path.join(temp, "external_scripts")
        os.makedirs(admin)
        os.makedirs(external_scripts)
        for name in ("validate_run_family_graph.py", "generate_run_family_views.py"):
            with open(os.path.join(external_scripts, name), "w", encoding="utf-8") as handle:
                handle.write("raise SystemExit(0)\n")
        result = subprocess.run(
            ["cmd.exe", "/c", "mklink", "/J", scripts_link, external_scripts],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return False

        original_file = mod.__file__
        mod.__file__ = os.path.join(scripts_link, "validate_repo_rules.py")
        errors: list[str] = []
        calls: list[list[str]] = []

        def fake_run(command, **kwargs):
            calls.append(command)
            return subprocess.CompletedProcess(command, 0, "", "")

        try:
            with mock.patch.object(mod.subprocess, "run", side_effect=fake_run):
                mod.check_run_family_graph_contract({}, trusted_root, errors)
            return not calls and len(errors) == 1 and "reparse" in errors[0].lower()
        finally:
            mod.__file__ = original_file


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

    # 5. VS015 command identity and offline package integrity
    live_config = mod.parse_config(CONFIG)
    markdownlint_params = next(
        rule["params"] for rule in live_config["rules"] if rule.get("id") == "VS015"
    )
    repo_root = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
    check(
        "VS015 legitimate pinned markdownlint fixture -> pass",
        not run_markdownlint(mod, markdownlint_params, repo_root),
    )
    arbitrary = dict(markdownlint_params)
    arbitrary["command"] = "python"
    check(
        "VS015 rejects arbitrary configured executable",
        any("unsupported validator command" in item for item in run_markdownlint(mod, arbitrary, repo_root)),
    )
    altered = dict(markdownlint_params)
    altered["trusted_entrypoint_sha256"] = "0" * 64
    check(
        "VS015 rejects altered trusted executable",
        any("hash mismatch" in item for item in run_markdownlint(mod, altered, repo_root)),
    )

    # 6. Profile hook IDs reject free-form command injection and preserve the
    # reviewed reviewer write guard during serialization.
    profiles = load_profile_generator()
    legitimate_hook = {
        "PreToolUse": [
            {
                "matcher": "Edit|Write",
                "hooks": [{"type": "command", "command_id": "reviewer_write_guard_v1"}],
            }
        ]
    }
    try:
        profiles._validate_hook_contract(legitimate_hook, "fixture")
        rendered = profiles.render_hooks_block(None, legitimate_hook)
        legitimate_ok = "command:" in rendered and "command_id" not in rendered and "REVIEWER GUARD" in rendered
    except Exception:
        legitimate_ok = False
    check("profile approved hook ID serializes the reviewed guard", legitimate_ok)
    malicious_hook = {
        "PreToolUse": [
            {
                "matcher": "Edit|Write",
                "hooks": [{"type": "command", "command": "powershell -Command Write-Host injected"}],
            }
        ]
    }
    try:
        profiles._validate_hook_contract(malicious_hook, "fixture")
        malicious_rejected = False
    except ValueError:
        malicious_rejected = True
    check("profile free-form command hook is rejected", malicious_rejected)
    check("validator rejects lexical junction before resolution", run_lexical_reparse_fixture(mod))

    # 7. VS036 must ignore target-config helper overrides and reject reparse paths.
    in_root_safe, traversal_safe = run_vs036_override_fixtures(mod)
    check("VS036 ignores an in-root configured helper override", in_root_safe)
    check("VS036 ignores a traversal configured helper override", traversal_safe)
    check("VS036 rejects a reparse-linked trusted helper tree", run_vs036_reparse_fixture(mod))
    vs036_errors: list[str] = []
    trusted_repo = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
    mod.check_run_family_graph_contract({}, trusted_repo, vs036_errors)
    check("VS036 fixed default helper pair passes on ai_ops", not vs036_errors)

    # 8. config parse + empty-rules fail-closed guard
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
