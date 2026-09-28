"""Static permission-rule classification for the portable Claude settings."""

from __future__ import annotations

import fnmatch
import importlib.util
import json
import unittest
from pathlib import Path

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

    def test_local_read_workflows_remain_allowed(self) -> None:
        for command in (
            "git status --short",
            "git diff --check",
            "git log -1 --oneline",
            "rg --files",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.classify("Bash", command), "allow")

    def test_other_existing_local_git_mutations_remain_allowed_by_scope(self) -> None:
        # Task 2.4 gates checkout/reset/rm/commit/push and network access.
        # Keep the existing add/merge/stash/mv approvals to avoid expanding the
        # separately recorded four-command removal decision.
        for command in (
            "git add file.txt",
            "git merge topic",
            "git stash push -m sample",
            "git mv old.txt new.txt",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.classify("Bash", command), "allow")

    def test_force_push_deny_precedes_prompt_rules(self) -> None:
        self.assertEqual(self.classify("Bash", "git push --force origin main"), "deny")

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

    def test_workspace_template_and_current_project_target_have_no_permission_drift(self) -> None:
        script = ROOT / "00_Admin" / "scripts" / "sync_claude_settings.py"
        spec = importlib.util.spec_from_file_location("sync_claude_settings_drift", script)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        template_allow, template_ask, template_deny = module.extract_permissions(
            self.settings
        )
        workspace_root = ROOT.parent
        config_path = ROOT / ".ai_ops" / "local" / "config.yaml"
        targets = [workspace_root / ".claude" / "settings.json"]
        if config_path.exists():
            targets.extend(
                repo_root / ".claude" / "settings.json"
                for repo_root in module.load_work_repos(config_path, workspace_root)
            )
        for target_path in targets:
            if not target_path.is_file():
                continue
            with self.subTest(target=target_path.name):
                target = module.load_json(target_path)
                status, drift, _ = module.check_target(
                    template_allow, template_ask, template_deny, target
                )
                self.assertIn(status, {module.STATUS_LOCAL_ADDS, module.STATUS_CLEAN}, drift)
                self.assertEqual(drift, [])

if __name__ == "__main__":
    unittest.main()
