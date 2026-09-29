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

import hashlib
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


def run_portable_directory_hash_fixture(mod) -> bool:
    """Require case-sensitive POSIX ordering regardless of the host OS."""
    with tempfile.TemporaryDirectory(prefix="validator-package-hash-") as root:
        # This ordering differs from Windows normcase() ordering.
        contents = {"Z.txt": b"upper\n", "a.txt": b"lower\n"}
        for name, content in contents.items():
            with open(os.path.join(root, name), "wb") as handle:
                handle.write(content)

        expected = hashlib.sha256()
        for name in ("Z.txt", "a.txt"):
            relative = name.encode("utf-8")
            content = contents[name]
            expected.update(relative)
            expected.update(b"\0")
            expected.update(len(content).to_bytes(8, "big"))
            expected.update(content)
        return mod._sha256_directory(root) == expected.hexdigest()


def run_generated_bin_hash_fixtures(mod) -> tuple[bool, bool, bool]:
    """Ignore only generated node_modules/.bin contents while rejecting other links."""
    with tempfile.TemporaryDirectory(prefix="validator-package-bin-") as root:
        package_root = os.path.join(root, "node_modules", "markdownlint-cli")
        generated_bin = os.path.join(package_root, "node_modules", ".bin")
        payload = os.path.join(package_root, "lib", "payload.js")
        bin_link_target = os.path.join(root, "generated-bin-target")
        os.makedirs(bin_link_target)
        os.makedirs(generated_bin)
        os.makedirs(os.path.dirname(payload))
        if not make_directory_link(os.path.join(generated_bin, "linked-tool"), bin_link_target):
            return False, False, False
        with open(payload, "wb") as handle:
            handle.write(b"dependency payload\n")
        with open(os.path.join(generated_bin, "markdownlint"), "wb") as handle:
            handle.write(b"POSIX symlink target A\n")
        with open(os.path.join(generated_bin, "markdownlint.cmd"), "wb") as handle:
            handle.write(b"Windows shim A\n")
        initial_hash = mod._sha256_directory(root)
        with open(os.path.join(generated_bin, "markdownlint"), "wb") as handle:
            handle.write(b"POSIX symlink target B with different bytes\n")
        with open(os.path.join(generated_bin, "markdownlint.ps1"), "wb") as handle:
            handle.write(b"Another generated Windows shim\n")
        generated_contents_ignored = mod._sha256_directory(root) == initial_hash

        elsewhere = os.path.join(root, "node_modules", "payload", "linked-dir")
        target = os.path.join(root, "link-target")
        os.makedirs(os.path.dirname(elsewhere))
        os.makedirs(target)
        link_created = make_directory_link(elsewhere, target)
        try:
            mod._sha256_directory(root)
        except ValueError as exc:
            outside_bin_link_rejected = "reparse" in str(exc).lower()
        else:
            outside_bin_link_rejected = False
        return (
            generated_contents_ignored,
            link_created and outside_bin_link_rejected,
            run_bin_directory_link_fixture(mod),
        )


def run_bin_directory_link_fixture(mod) -> bool:
    """Reject a linked node_modules/.bin directory before pruning its entries."""
    with tempfile.TemporaryDirectory(prefix="validator-package-bin-link-") as root:
        node_modules = os.path.join(root, "node_modules")
        target = os.path.join(root, "external-bin-target")
        os.makedirs(node_modules)
        os.makedirs(target)
        if not make_directory_link(os.path.join(node_modules, ".bin"), target):
            return False
        try:
            mod._sha256_directory(root)
        except ValueError as exc:
            return "reparse" in str(exc).lower()
        return False


def run_lexical_reparse_fixture(mod) -> bool:
    root = tempfile.mkdtemp(prefix="validator-reparse-")
    try:
        root_path = os.path.abspath(root)
        target = os.path.join(root_path, "target")
        junction = os.path.join(root_path, "link")
        os.makedirs(target)
        with open(os.path.join(target, "safe.txt"), "w", encoding="utf-8") as handle:
            handle.write("safe\n")
        if not make_directory_link(junction, target):
            return False
        try:
            mod._validate_repo_path(os.path.join(junction, "safe.txt"), root_path, label="fixture")
        except ValueError as exc:
            return "reparse" in str(exc).lower()
        return False
    finally:
        shutil.rmtree(root, ignore_errors=True)


def make_directory_link(link: str, target: str) -> bool:
    """Create a directory link using the platform's native mechanism."""
    if os.name == "nt":
        result = subprocess.run(
            ["cmd.exe", "/c", "mklink", "/J", link, target],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0
    try:
        os.symlink(target, link, target_is_directory=True)
    except OSError:
        return False
    return True


def run_ci_markdownlint_resolver_fixtures(mod) -> tuple[bool, bool, bool, bool, bool, bool, bool]:
    """Exercise the CI resolver without trusting the host's Node installation."""
    with tempfile.TemporaryDirectory(prefix="validator-ci-markdownlint-") as temp:
        runner_root = os.path.join(temp, "toolcache")
        install_prefix = os.path.join(runner_root, "node", "24.21.0", "x64")
        bin_dir = os.path.join(install_prefix, "bin")
        workspace = os.path.join(temp, "workspace")
        install_root = os.path.join(workspace, ".github", "tools", "markdownlint")
        package_root = os.path.join(install_root, "node_modules", "markdownlint-cli")
        os.makedirs(bin_dir)
        os.makedirs(package_root)
        os.makedirs(install_root, exist_ok=True)
        node_path = os.path.join(bin_dir, "node")
        entrypoint = os.path.join(package_root, "markdownlint.js")
        package_file = os.path.join(package_root, "package.json")
        with open(node_path, "wb") as handle:
            handle.write(b"fixture node executable\n")
        with open(entrypoint, "wb") as handle:
            handle.write(b"fixture markdownlint entrypoint\n")
        with open(package_file, "w", encoding="utf-8") as handle:
            handle.write('{"version":"0.47.0"}\n')
        lockfile = os.path.join(install_root, "package-lock.json")
        lock_content = b'{"lockfileVersion":3,"packages":{}}\n'
        with open(lockfile, "wb") as handle:
            handle.write(lock_content)

        params = {
            "trusted_ci_node_root": "runner_tool_cache",
            "trusted_ci_node_version": "24.21.0",
            "trusted_ci_node_sha256": mod._sha256_file(node_path),
            "trusted_entrypoint_sha256": mod._sha256_file(entrypoint),
            "trusted_package_version": "0.47.0",
            "trusted_ci_install_root": ".github/tools/markdownlint",
            "trusted_ci_lockfile_sha256": mod._sha256_lf_text_file(lockfile),
        }
        trusted_env = {
            "GITHUB_ACTIONS": "true",
            "CI": "true",
            "RUNNER_TOOL_CACHE": runner_root,
            "GITHUB_WORKSPACE": workspace,
        }
        version_result = subprocess.CompletedProcess(
            [node_path, "--version"], 0, "v24.21.0\n", ""
        )

        def resolve(candidate: str, candidate_params: dict, env: dict) -> tuple[bool, str]:
            try:
                with (
                    mock.patch.dict(os.environ, env, clear=False),
                    mock.patch.object(mod.shutil, "which", return_value=candidate),
                    mock.patch.object(mod.subprocess, "run", return_value=version_result),
                ):
                    resolved = mod._resolve_trusted_ci_markdownlint(candidate_params)
                return resolved == [os.path.abspath(node_path), entrypoint], ""
            except ValueError as exc:
                return False, str(exc)

        legitimate, _ = resolve(node_path, params, trusted_env)
        with open(lockfile, "wb") as handle:
            handle.write(lock_content.replace(b"\n", b"\r\n"))
        crlf_legitimate, _ = resolve(node_path, params, trusted_env)
        with open(lockfile, "wb") as handle:
            handle.write(lock_content)
        altered = dict(params)
        altered["trusted_ci_node_sha256"] = "0" * 64
        _, altered_error = resolve(node_path, altered, trusted_env)
        _, environment_error = resolve(
            node_path,
            params,
            {**trusted_env, "GITHUB_ACTIONS": "false"},
        )
        linked_bin = os.path.join(runner_root, "linked-bin")
        link_created = make_directory_link(linked_bin, bin_dir)
        _, link_error = resolve(os.path.join(linked_bin, "node"), params, trusted_env)
        outside_dependency = os.path.join(temp, "outside-dependency")
        os.makedirs(outside_dependency)
        linked_dependency = os.path.join(install_root, "node_modules", "linked-dependency")
        dependency_link_created = make_directory_link(linked_dependency, outside_dependency)
        _, dependency_link_error = resolve(node_path, params, trusted_env)
        with open(lockfile, "a", encoding="utf-8") as handle:
            handle.write("tampered\n")
        _, lock_error = resolve(node_path, params, trusted_env)
        return (
            legitimate,
            crlf_legitimate,
            "Node executable hash mismatch" in altered_error,
            "lockfile hash mismatch" in lock_error,
            "restricted to GitHub Actions" in environment_error,
            link_created and ("crosses" in link_error or "link" in link_error),
            dependency_link_created and "reparse" in dependency_link_error.lower(),
        )


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
        if not make_directory_link(scripts_link, external_scripts):
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
    check("VS015 package-tree hash uses portable case-sensitive ordering", run_portable_directory_hash_fixture(mod))
    generated_bin_ignored, package_link_rejected, linked_bin_rejected = run_generated_bin_hash_fixtures(mod)
    check("VS015 omits only generated node_modules/.bin contents", generated_bin_ignored)
    check("VS015 still rejects reparse links elsewhere in the package", package_link_rejected)
    check("VS015 rejects a reparse-linked node_modules/.bin directory", linked_bin_rejected)
    live_markdownlint_errors = run_markdownlint(mod, markdownlint_params, repo_root)
    check(
        "VS015 legitimate pinned markdownlint fixture -> pass",
        not live_markdownlint_errors,
    )
    if live_markdownlint_errors:
        for error in live_markdownlint_errors:
            print(f"    VS015 diagnostic: {error}")
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

    (
        ci_legitimate,
        ci_crlf_legitimate,
        ci_hash_rejected,
        ci_lock_rejected,
        ci_env_rejected,
        ci_link_rejected,
        ci_dependency_link_rejected,
    ) = run_ci_markdownlint_resolver_fixtures(mod)
    check("VS015 CI resolver accepts exact pinned artifacts", ci_legitimate)
    check("VS015 CI lockfile hash accepts LF and CRLF checkouts", ci_crlf_legitimate)
    check("VS015 CI resolver rejects altered Node executable", ci_hash_rejected)
    check("VS015 CI resolver rejects altered dependency lockfile", ci_lock_rejected)
    check("VS015 CI resolver rejects spoofed CI environment", ci_env_rejected)
    check("VS015 CI resolver rejects linked Node path", ci_link_rejected)
    check("VS015 CI resolver rejects linked sibling dependency", ci_dependency_link_rejected)

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
