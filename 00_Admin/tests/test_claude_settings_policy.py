"""Static permission-rule classification for the portable Claude settings."""

from __future__ import annotations

import fnmatch
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SETTINGS_PATH = ROOT / "01_Resources" / "templates" / "config" / "settings_global_template.json"


def _matches(rule: str, tool: str, value: str = "") -> bool:
    if "(" not in rule:
        return rule == tool
    name, specifier = rule[:-1].split("(", 1)
    if name != tool:
        return False
    if specifier.endswith(":*"):
        specifier = specifier[:-2] + "*"
    return fnmatch.fnmatchcase(value, specifier)


class ClaudeSettingsPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        cls.permissions = cls.settings["permissions"]

    def classify(self, tool: str, value: str = "") -> str:
        rules = self.permissions
        if any(_matches(rule, tool, value) for rule in rules["deny"]):
            return "deny"
        if any(_matches(rule, tool, value) for rule in rules.get("ask", [])):
            return "ask"
        if any(_matches(rule, tool, value) for rule in rules["allow"]):
            return "allow"
        return "prompt"

    def test_gated_git_mutation_and_network_forms_prompt(self) -> None:
        commands = (
            "git push origin main",
            "git -C repo push origin main",
            "git commit -m sample",
            "git -c core.safecrlf=true reset --hard",
            "git checkout main",
            "git -C repo clean -fd",
            "git rm tracked.txt",
            "git -C repo rm tracked.txt",
            "git fetch origin",
            "git -C repo fetch origin",
            "git --git-dir=repo/.git pull origin main",
            "git clone https://example.invalid/repo.git",
            "git ls-remote origin",
            "git -C repo ls-remote origin",
            "git submodule update --init",
            "git -C repo submodule update --remote",
            "git remote update",
            "git -C repo remote prune origin",
            "git send-pack origin refs/heads/main",
            "git receive-pack repo.git",
            "git upload-pack repo.git",
            "git http-fetch object-id https://example.invalid/repo",
            "git http-push https://example.invalid/repo refs/heads/main",
            "git archive --remote=origin main",
            "git-remote-https origin https://example.invalid/repo",
        )
        for command in commands:
            with self.subTest(command=command):
                self.assertEqual(self.classify("Bash", command), "ask")

    def test_named_external_tools_prompt(self) -> None:
        for command in (
            "gh pr merge 123",
            "curl https://example.invalid",
            "powershell -NoProfile -Command Get-Location",
            "pwsh -Command Get-Location",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.classify("Bash", command), "ask")
        self.assertEqual(self.classify("PowerShell", "Get-Location"), "ask")

    def test_interpreters_and_hook_runner_require_approval(self) -> None:
        for command in (
            "python 00_Admin/scripts/validate_repo_rules.py",
            "python3 -m pytest",
            "node tool.js",
            "npm ci",
            "pip install -r requirements.txt",
            "conda run -n ai_ops python tool.py",
            "pre-commit run --all-files",
            '"C:/Python311/python.exe" -m pytest',
            'env "C:/Node/node.exe" tool.js',
            'pre-commit.exe run --all-files',
        ):
            with self.subTest(command=command):
                self.assertNotEqual(self.classify("Bash", command), "allow")

    def test_local_read_workflows_remain_allowed(self) -> None:
        for command in (
            "git status --short",
            "git diff --check",
            "git log -1 --oneline",
            "rg --files",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.classify("Bash", command), "allow")

    def test_other_existing_local_git_mutations_remain_approval_gated(self) -> None:
        # Merge and stash are approval-gated in the current portable template;
        # add and mv remain locally allowed by scope.
        for command in (
            "git add file.txt",
            "git mv old.txt new.txt",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.classify("Bash", command), "allow")
        for command in ("git merge topic", "git stash push -m sample"):
            with self.subTest(command=command):
                self.assertEqual(self.classify("Bash", command), "ask")

    def test_force_push_deny_precedes_prompt_rules(self) -> None:
        self.assertEqual(self.classify("Bash", "git push --force origin main"), "deny")

    def test_closeout_gate_bypass_routes_are_denied_and_bundled_flags_are_approval_gated(self) -> None:
        for command in (
            "git commit --no-verify -m bypass",
            "git commit -n -m bypass",
            "git commit -m bypass --no-verify",
            "git commit -am bypass -n",
            "git -C repo commit --no-verify -m bypass",
            "git -c core.hooksPath=/dev/null commit",
            "git push --no-verify origin main",
            "git push origin main --no-verify",
            "git -C repo push --no-verify origin main",
            "git commit --amend --no-edit -n",
            "git config core.hooksPath .git/hooks",
            "git -C repo config core.hooksPath .git/hooks",
            "git config CORE.HOOKSPATH .git/hooks",
            "git config --global core.hooksPath .git/hooks",
            "git -C repo config --global core.hooksPath .git/hooks",
            "git update-ref refs/heads/main HEAD~1",
            "git -C repo update-ref refs/heads/main HEAD~1",
            "git show --output=packet.txt HEAD",
            "git diff --output=packet.txt",
            "git log --output=packet.txt",
            "SKIP=ai-ops-closeout-security git commit -m bypass",
            "git commit -sn -m bypass",
            "git commit -vnm bypass",
            "git commit -qn -m bypass",
        ):
            with self.subTest(command=command):
                expected = "ask" if command in {
                    "git commit -sn -m bypass",
                    "git commit -vnm bypass",
                    "git commit -qn -m bypass",
                } else "deny"
                self.assertEqual(self.classify("Bash", command), expected)
        self.assertEqual(self.classify("Bash", "git commit -m ordinary"), "ask")
        self.assertEqual(self.classify("Bash", "git push origin main"), "ask")
        for command in ("git push -n origin main",):
            self.assertEqual(self.classify("Bash", command), "ask")
        for command in (
            "python 00_Admin/scripts/example.py --output=report.json",
            "python tool.py --output out.obj",
            "python -m pytest -k SKIP=1",
        ):
            with self.subTest(command=command):
                self.assertNotEqual(self.classify("Bash", command), "deny")
        for command in (
            'git commit -m "Harden closeout-security gate and guard"',
            "git log --grep=commit",
            "git branch --format='%(refname)'",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.classify("Bash", command), "ask")

    def test_synchronizer_flags_and_drops_prompt_gated_git_allows(self) -> None:
        script = ROOT / "00_Admin" / "scripts" / "sync_claude_settings.py"
        spec = importlib.util.spec_from_file_location("sync_claude_settings", script)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        allow, ask, deny = module.extract_permissions(self.settings)
        conflicting = (
            "Bash(git rm:*)",
            "Bash(git fetch:*)",
            "Bash(git ls-remote:*)",
            "Bash(gh:*)",
            "Bash(gh pr merge:*)",
            "Bash(curl:*)",
            "Bash(curl -I:*)",
            "Bash(powershell:*)",
            "Bash(powershell -NoProfile:*)",
            "Bash(pwsh:*)",
            "PowerShell",
            "PowerShell(Get-ChildItem *)",
            "Bash(python:*)",
            "Bash(pre-commit run:*)",
            'Bash("C:/Python311/python.exe" -m pytest:*)',
            'Bash(env "C:/Node/node.exe" tool.js:*)',
            "Bash(pre-commit.exe run:*)",
        )
        for rule in conflicting:
            with self.subTest(rule=rule):
                target = {
                    "permissions": {
                        "allow": allow + [rule],
                        "ask": ask,
                        "deny": deny,
                    }
                }
                status, drift, _ = module.check_target(allow, ask, deny, target)
                self.assertEqual(status, module.STATUS_DRIFT)
                self.assertTrue(
                    any("ask-overlap local additions" in line for line in drift)
                )

                merged = module.build_merged(allow, ask, deny, target)
                self.assertNotIn(rule, merged["permissions"]["allow"])

    def test_missing_containment_config_does_not_log_resolved_path(self) -> None:
        script = ROOT / "00_Admin" / "scripts" / "sync_claude_settings.py"
        spec = importlib.util.spec_from_file_location("sync_claude_settings_log", script)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            template = workspace / "ai_ops" / "01_Resources" / "templates" / "config"
            target = workspace / ".claude"
            template.mkdir(parents=True)
            target.mkdir(parents=True)
            (template / "settings_global_template.json").write_text(
                json.dumps({"permissions": {"allow": [], "ask": [], "deny": []}}),
                encoding="utf-8",
            )
            (target / "settings.json").write_text(
                json.dumps({"permissions": {"allow": [], "ask": [], "deny": []}}),
                encoding="utf-8",
            )

            with patch.object(sys, "argv", [
                "sync_claude_settings.py",
                "--check",
                "--workspace-root",
                str(workspace),
            ]), patch.object(module.LOG, "error") as log_error:
                result = module.main()

            self.assertEqual(result, 1)
            messages = [
                " ".join(str(arg) for arg in call.args)
                for call in log_error.call_args_list
            ]
            self.assertTrue(any("containment config not found" in message for message in messages))
            self.assertTrue(all(str(workspace) not in message for message in messages))

    def test_malformed_containment_config_does_not_log_resolved_path(self) -> None:
        script = ROOT / "00_Admin" / "scripts" / "sync_claude_settings.py"
        spec = importlib.util.spec_from_file_location("sync_claude_settings_invalid_log", script)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            template = workspace / "ai_ops" / "01_Resources" / "templates" / "config"
            containment = workspace / "ai_ops" / "00_Admin" / "configs"
            target = workspace / ".claude"
            template.mkdir(parents=True)
            containment.mkdir(parents=True)
            target.mkdir(parents=True)
            (template / "settings_global_template.json").write_text(
                json.dumps({"permissions": {"allow": [], "ask": [], "deny": []}}),
                encoding="utf-8",
            )
            (target / "settings.json").write_text(
                json.dumps({"permissions": {"allow": [], "ask": [], "deny": []}}),
                encoding="utf-8",
            )
            (containment / "workspace_containment.yaml").write_text(
                "overlay_allowlist:\n  allow: invalid\n",
                encoding="utf-8",
            )

            with patch.object(sys, "argv", [
                "sync_claude_settings.py",
                "--check",
                "--workspace-root",
                str(workspace),
            ]), patch.object(module.LOG, "error") as log_error:
                result = module.main()

            self.assertEqual(result, 1)
            messages = [
                " ".join(str(arg) for arg in call.args)
                for call in log_error.call_args_list
            ]
            self.assertTrue(any("invalid containment config" in message for message in messages))
            self.assertTrue(all(str(workspace) not in message for message in messages))

    def test_containment_resolution_error_does_not_log_resolved_path(self) -> None:
        script = ROOT / "00_Admin" / "scripts" / "sync_claude_settings.py"
        spec = importlib.util.spec_from_file_location("sync_claude_settings_resolution_log", script)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            template = workspace / "ai_ops" / "01_Resources" / "templates" / "config"
            target = workspace / ".claude"
            template.mkdir(parents=True)
            target.mkdir(parents=True)
            (template / "settings_global_template.json").write_text(
                json.dumps({"permissions": {"allow": [], "ask": [], "deny": []}}),
                encoding="utf-8",
            )
            (target / "settings.json").write_text(
                json.dumps({"permissions": {"allow": [], "ask": [], "deny": []}}),
                encoding="utf-8",
            )

            original_resolve = module.resolve
            resolve_calls = 0

            def fail_containment_resolution(path: str | Path, root: Path) -> Path:
                nonlocal resolve_calls
                resolve_calls += 1
                if resolve_calls == 3:
                    raise ValueError(f"configured path escapes workspace root: {root / str(path)}")
                return original_resolve(path, root)

            with patch.object(sys, "argv", [
                "sync_claude_settings.py",
                "--check",
                "--workspace-root",
                str(workspace),
            ]), patch.object(module, "resolve", side_effect=fail_containment_resolution), patch.object(
                module.LOG, "error"
            ) as log_error:
                result = module.main()

            self.assertEqual(result, 1)
            messages = [
                " ".join(str(arg) for arg in call.args)
                for call in log_error.call_args_list
            ]
            self.assertTrue(any("could not be resolved" in message for message in messages))
            self.assertTrue(all(str(workspace) not in message for message in messages))

    def test_project_overlay_keeps_local_runner_allow_and_template_gates(self) -> None:
        script = ROOT / "00_Admin" / "scripts" / "sync_claude_settings.py"
        spec = importlib.util.spec_from_file_location("sync_claude_settings_overlay", script)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        runner_allow = 'Bash("C:/Program Files/GIS/bin/python-gis.bat" scripts/*:*)'
        project_only = "Bash(git ls-files:*)"
        existing = {
            "projectSetting": {"preserve": True},
            "permissions": {
                "allow": [runner_allow, project_only, "Bash(git push:*)"],
                "ask": ["Bash(git -C:*)"],
                "deny": ["Bash(local-secret-reader:*)"],
            },
        }
        template_allow, template_ask, template_deny = module.extract_permissions(
            self.settings
        )
        merged = module.build_merged(
            template_allow, template_ask, template_deny, existing
        )
        perms = merged["permissions"]

        self.assertIn(runner_allow, perms["allow"])
        self.assertIn(project_only, perms["allow"])
        self.assertNotIn("Bash(git push:*)", perms["allow"])
        self.assertIn("Bash(git push:*)", perms["ask"])
        self.assertIn("Bash(git -C:*)", perms["ask"])
        self.assertIn("Bash(local-secret-reader:*)", perms["deny"])
        self.assertEqual(merged["projectSetting"], {"preserve": True})

    def test_overlay_allowlist_rejects_shell_and_absolute_path_additions(self) -> None:
        script = ROOT / "00_Admin" / "scripts" / "sync_claude_settings.py"
        spec = importlib.util.spec_from_file_location("sync_claude_settings_overlay_guard", script)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        allowlist = {
            "Bash(bash .ai_ops/setup/*.sh:*)",
            "Bash(bash ai_ops/.ai_ops/setup/*.sh:*)",
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            settings = root / ".claude" / "settings.json"
            overlay = settings.parent / "settings.local.json"
            settings.parent.mkdir()
            settings.write_text("{}", encoding="utf-8")
            overlay.write_text(
                json.dumps({"permissions": {"allow": [
                    "Bash(bash .ai_ops/setup/*.sh:*)",
                    "Bash(python -:*)",
                    "Bash(sed -i:*)",
                    "Bash(/c/tmp/*:*)",
                ]}}),
                encoding="utf-8",
            )
            drift = module.check_overlay(settings, root, allowlist)
            self.assertEqual(["  overlay allowlist additions (3)"], drift)
            overlay.write_text(
                json.dumps({"permissions": {"allow": [
                    "Bash(bash .ai_ops/setup/*.sh:*)",
                    "Bash(bash ai_ops/.ai_ops/setup/*.sh:*)",
                ]}}),
                encoding="utf-8",
            )
            self.assertEqual(module.check_overlay(settings, root, allowlist), [])

    def test_resolve_trusted_accepts_case_or_short_name_aliases(self) -> None:
        script = ROOT / "00_Admin" / "scripts" / "sync_claude_settings.py"
        spec = importlib.util.spec_from_file_location("sync_claude_settings_alias_guard", script)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            raw_root = Path(tmp)
            root = raw_root.resolve()
            settings = root / ".claude" / "settings.json"
            settings.parent.mkdir()
            settings.write_text("{}", encoding="utf-8")
            alias_roots = [raw_root]
            if os.name == "nt":
                alias_roots.append(Path(str(root).upper()))
            for alias_root in alias_roots:
                with self.subTest(alias_root=alias_root):
                    alias_settings = alias_root / ".claude" / "settings.json"
                    resolved = module.resolve_trusted(
                        alias_settings, root, label="settings", must_exist=True
                    )
                    self.assertEqual(resolved, settings)

    def test_settings_targets_report_missing_security_denies_in_a_temp_workspace(self) -> None:
        script = ROOT / "00_Admin" / "scripts" / "sync_claude_settings.py"
        spec = importlib.util.spec_from_file_location("sync_claude_settings_drift", script)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        template_allow, template_ask, template_deny = module.extract_permissions(
            self.settings
        )
        required_denies = [
            "Bash(*git*commit* --no-verif*)",
            "Bash(*git*commit* -n)",
            "Bash(*git*commit* -n *)",
            "Bash(*git*push* --no-verif*)",
            "Bash(*git*config*--global*)",
            "Bash(*git*update-ref *)",
        ]
        with tempfile.TemporaryDirectory() as directory:
            workspace_root = Path(directory) / "workspace"
            target_path = workspace_root / "repo" / ".claude" / "settings.json"
            target_path.parent.mkdir(parents=True)
            target_path.write_text(
                json.dumps({"permissions": {"allow": [], "ask": [], "deny": []}}),
                encoding="utf-8",
            )
            target = module.load_json(target_path)
            status, drift, _ = module.check_target(
                template_allow, template_ask, template_deny, target
            )
            self.assertEqual(module.STATUS_DRIFT, status, drift)
            drift_text = "\n".join(drift)
            self.assertIn("deny missing", drift_text)
            self.assertIn("deny missing (", drift_text)
            for rule in required_denies:
                self.assertNotIn(rule, drift_text)

    def test_bulk_target_rejects_reparse_point_parent(self) -> None:
        script = ROOT / "00_Admin" / "scripts" / "sync_claude_settings.py"
        spec = importlib.util.spec_from_file_location("sync_claude_settings_reparse", script)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as temp_dir:
            if os.name != "nt":
                self.skipTest("directory junctions are a Windows-specific probe")
            workspace = Path(temp_dir) / "workspace"
            repo = workspace / "repo"
            inside = repo / "junction-target"
            repo.mkdir(parents=True)
            inside.mkdir()
            link = repo / ".claude"
            created = subprocess.run(
                ["cmd.exe", "/c", "mklink", "/J", str(link), str(inside)],
                capture_output=True,
                text=True,
                check=False,
            )
            if created.returncode:
                self.skipTest(f"directory junction creation unavailable: {created.stderr.strip()}")
            try:
                with self.assertRaises(ValueError):
                    module.resolve_trusted(
                        repo / ".claude" / "settings.json",
                        repo,
                        label="settings target",
                        must_exist=False,
                    )
            finally:
                link.rmdir()

if __name__ == "__main__":
    unittest.main()
