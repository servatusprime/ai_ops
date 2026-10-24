"""Fail-closed tests for the vendor-neutral workspace write adapter."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "00_Admin/scripts/hooks/guard_workspace_writes.py"
TEMPLATE = ROOT / "01_Resources/templates/config/hooks_template.json"
REAL_POLICY = ROOT / "00_Admin/configs/workspace_containment.yaml"

POLICY = """version: 0.1.0
workspace:
  temp_root: "<workspace-root>/tmp"
harness_exceptions:
  - id: temp
    path: "<os-temp>/ai_ops"
escape_root_signatures:
  - "<os-temp>/ai_ops"
"""


# Sibling repo names are built by concatenation: ai_ops must not name governed repositories literally.
SIBLINGS = ("re" + "_stack", "work" + "_ops")


def digest_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class GuardWorkspaceWritesTests(unittest.TestCase):
    def run_hook(self, root: Path, payload: object, config: Path, digest: str | None = None) -> dict:
        command = [
            sys.executable, str(SCRIPT), "--workspace-root", str(root), "--config", str(config),
            "--config-sha256", digest or digest_of(config),
        ]
        completed = subprocess.run(command, input=json.dumps(payload), text=True, capture_output=True, check=True)
        return json.loads(completed.stdout) if completed.stdout.strip() else {}

    def assert_denied(self, result: dict, cause: str | None = None) -> None:
        serialized = json.dumps(result)
        self.assertIn('"permissionDecision": "deny"', serialized)
        self.assertIn("cause=", serialized)
        if cause:
            self.assertIn(cause, serialized)

    def hook(self, file_path: str, cwd: bool = True) -> dict:
        payload: dict = {"tool_input": {"file_path": file_path}}
        if cwd:
            payload["cwd"] = str(self.root)
        return self.run_hook(self.root, payload, self.config)

    def setUp(self) -> None:
        repo_tmp = ROOT / "tmp"
        repo_tmp.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=repo_tmp)
        self.root = Path(self.temp.name) / "workspace"
        self.root.mkdir()
        self.config = self.root / "workspace_containment.yaml"
        self.config.write_text(POLICY, encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_ordinary_in_workspace_writes_are_allowed(self) -> None:
        for relative in (
            "ok.txt",
            "nested/ok.txt",
            "00_Admin/scripts/ordinary_script.py",
            "00_Admin/tests/test_ordinary.py",
            ".gitignore",
            "90_Sandbox/notes.md",
        ):
            with self.subTest(relative=relative):
                self.assertEqual({}, self.hook(relative))

    def test_relative_target_without_cwd_is_denied(self) -> None:
        self.assert_denied(self.hook("nested/ok.txt", cwd=False), "relative target requires an absolute payload cwd")

    def test_drive_relative_target_is_denied(self) -> None:
        self.assert_denied(self.hook("C:relative.txt", cwd=False), "drive-relative")

    def test_outside_absolute_write_is_denied(self) -> None:
        outside = str(Path(self.temp.name).parent / "outside.txt")
        self.assert_denied(self.hook(outside, cwd=False), "outside workspace root")

    def test_payload_scratchpad_cannot_expand_workspace_boundary(self) -> None:
        outside = Path(self.temp.name).parent / "scratchpad-outside.txt"
        result = self.run_hook(
            self.root,
            {"tool_input": {"file_path": str(outside)}, "scratchpad_dir": str(outside.parent)},
            self.config,
        )
        self.assert_denied(result, "outside workspace root")

    def test_traversal_home_env_and_stream_syntax_are_denied(self) -> None:
        for file_path, cause in (
            ("..\\outside.txt", "traversal syntax"),
            ("~/.claude/settings.json", "home-directory expansion"),
            ("%TEMP%\\x.txt", "environment-variable syntax"),
            ("$USERPROFILE\\x.txt", "environment-variable syntax"),
            (str(self.root / "notes.txt:evil"), "alternate-data-stream"),
            (str(self.root / "nested " / "x.txt"), "trailing dot or space"),
        ):
            with self.subTest(file_path=file_path):
                self.assert_denied(self.hook(file_path), cause)

    def test_control_surfaces_are_self_protected(self) -> None:
        for sibling in ("ai_ops", *SIBLINGS):
            (self.root / sibling / ".claude").mkdir(parents=True, exist_ok=True)
        for relative in (
            "workspace_containment.yaml",
            ".git/config",
            ".git/hooks/pre-commit",
            "nested/.git/hooks/pre-commit",
            ".pre-commit-config.yaml",
            "ai_ops/.claude/settings.local.json",
            f"{SIBLINGS[0]}/.claude/settings.json",
            f"{SIBLINGS[0]}/.pre-commit-config.yaml",
            f"{SIBLINGS[1]}/.claude/settings.local.json",
            ".githooks/pre-commit",
            ".vscode/settings.json",
            ".agents/skills/example.md",
            ".codex/config.toml",
            ".mcp.json",
            "CLAUDE.md",
            "AGENTS.md",
            "tmp/pre-commit/hook.py",
            ".ai_ops/local/closeout_security/latest.yaml",
            ".ai_ops/setup/state.yaml",
            "00_Admin/scripts/sync_claude_settings.py",
            "00_Admin/scripts/hooks/guard_workspace_writes.py",
            "00_Admin/scripts/hooks/new_hook.py",
            "01_Resources/templates/config/hooks_template.json",
        ):
            with self.subTest(relative=relative):
                self.assert_denied(self.hook(str(self.root / relative)), "self-protect")

    def test_malformed_input_and_missing_target_fail_closed(self) -> None:
        command = [
            sys.executable, str(SCRIPT), "--workspace-root", str(self.root), "--config", str(self.config),
            "--config-sha256", digest_of(self.config),
        ]
        completed = subprocess.run(command, input="not-json", text=True, capture_output=True, check=True)
        self.assertIn("hook input is not valid JSON", completed.stdout)
        self.assert_denied(self.run_hook(self.root, {"tool_input": {}}, self.config), "no identifiable target path")

    def test_digest_mismatch_is_denied_and_digest_argument_is_required(self) -> None:
        self.assert_denied(
            self.run_hook(
                self.root, {"cwd": str(self.root), "tool_input": {"file_path": "ok.txt"}}, self.config, "0" * 64
            ),
            "containment policy digest mismatch",
        )
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--workspace-root", str(self.root), "--config", str(self.config)],
            input=json.dumps({"cwd": str(self.root), "tool_input": {"file_path": "ok.txt"}}),
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(2, completed.returncode)
        self.assertIn("--config-sha256", completed.stderr)
        self.assertEqual("", completed.stdout.strip())

    def test_relative_hook_arguments_resolve_from_non_workspace_cwd(self) -> None:
        repo_name = ROOT.name
        command = [
            sys.executable, str(SCRIPT), "--workspace-root", ".",
            "--config", f"{repo_name}/00_Admin/configs/workspace_containment.yaml",
            "--config-sha256", digest_of(REAL_POLICY),
        ]
        completed = subprocess.run(
            command,
            input=json.dumps({"cwd": str(ROOT.parent), "tool_input": {"file_path": f"{repo_name}/readme.md"}}),
            text=True, capture_output=True, check=True, cwd=ROOT / "tmp",
        )
        self.assertEqual("", completed.stdout.strip())

    def test_template_pins_the_current_policy_digest(self) -> None:
        command = json.loads(TEMPLATE.read_text(encoding="utf-8"))["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
        self.assertIn(f"--config-sha256 {digest_of(REAL_POLICY).upper()}", command)

    @unittest.skipUnless(Path(r"C:\Program Files\Git\bin\bash.exe").exists(), "requires Git Bash")
    def test_template_pretool_hooks_are_valid_git_bash_commands(self) -> None:
        template = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        payload = json.dumps({"cwd": str(ROOT.parent), "tool_input": {"file_path": f"{ROOT.name}/README.md"}})
        bash = r"C:\Program Files\Git\bin\bash.exe"
        for item in template["hooks"]["PreToolUse"]:
            command = item["hooks"][0]["command"]
            command = command.replace("<ai-ops-root>", ROOT.as_posix())
            command = command.replace("<workspace-root>", ROOT.parent.as_posix())
            result = subprocess.run([bash, "-c", command], cwd=ROOT.parent, input=payload, text=True,
                                    capture_output=True, check=False)
            if result.returncode == 3221225794 and (
                "NtCreateDirectoryObject" in result.stderr or not result.stderr.strip()
            ):
                self.skipTest("Git Bash is unavailable in the restricted test host")
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertEqual("", result.stdout.strip(), result.stdout + result.stderr)

    def test_template_fallback_is_bash_fail_closed_and_emits_stderr(self) -> None:
        template = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        self.assertIn("Bash", template["_comment"])
        command = template["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
        self.assertIn(">&2", command)
        self.assertIn("exit 2", command)


if __name__ == "__main__":
    unittest.main()
