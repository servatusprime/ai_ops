"""Scratch-repository tests for the HEAD-bound closeout hook."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
HOOK_SOURCE = ROOT / "00_Admin/scripts/hooks/validate_closeout_security_head.py"
POLICY_SOURCE = ROOT / "00_Admin/configs/closeout_security_tiers.yaml"
PREPASS_SOURCE = ROOT / "00_Admin/scripts/closeout_security_prepass.py"
VALIDATOR_SOURCE = ROOT / "00_Admin/scripts/validate_closeout_security_receipt.py"
TARGET_PATHS_SOURCE = ROOT / "00_Admin/scripts/target_paths.py"


class CloseoutSecurityHeadTests(unittest.TestCase):
    def _git(self, repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(repo), *args],
            check=check,
            capture_output=True,
            text=True,
        )

    def _fixture(self) -> tuple[tempfile.TemporaryDirectory[str], Path, Path, Path]:
        temp_dir = tempfile.TemporaryDirectory()
        repo = Path(temp_dir.name)
        policy = repo / "00_Admin/configs/closeout_security_tiers.yaml"
        validator = repo / "00_Admin/scripts/validate_closeout_security_receipt.py"
        target_paths = repo / "00_Admin/scripts/target_paths.py"
        hook = repo / "00_Admin/scripts/hooks/validate_closeout_security_head.py"
        policy.parent.mkdir(parents=True)
        validator.parent.mkdir(parents=True)
        hook.parent.mkdir(parents=True)
        target_paths.write_text("# scratch target-paths shim\n", encoding="utf-8")
        policy.write_text(
            'version: "1.0.0"\nruleset_version: "1.0.0"\n'
            'forced_t2_files:\n  - "00_Admin/scripts/target_paths.py"\n',
            encoding="utf-8",
        )
        validator.write_text(
            """from pathlib import Path
import sys
import yaml
args = sys.argv[1:]
if '--first-landing' not in args:
    raise SystemExit(2)
receipt = Path(args[args.index('--receipt') + 1])
config = Path(args[args.index('--config') + 1])
try:
    data = yaml.safe_load(config.read_text(encoding='utf-8')) or {}
    receipt_data = yaml.safe_load(receipt.read_text(encoding='utf-8')) or {}
except Exception:
    raise SystemExit(1)
valid = (
    receipt.is_file()
    and config.is_file()
    and '00_Admin/scripts/target_paths.py' in data.get('forced_t2_files', [])
    and receipt_data.get('first_landing') is True
    and receipt_data.get('repo_root') == str(Path(args[args.index('--repo-root') + 1]).resolve())
)
raise SystemExit(0 if valid else 1)
""",
            encoding="utf-8",
        )
        shutil.copyfile(HOOK_SOURCE, hook)
        self._git(repo, "init", "--quiet")
        self._git(repo, "config", "user.name", "Closeout Hook Tests")
        self._git(repo, "config", "user.email", "tests@example.invalid")
        self._git(repo, "add", ".")
        self._git(repo, "commit", "--quiet", "-m", "baseline")
        return temp_dir, repo, policy, hook

    def _stage_policy(self, repo: Path, policy: Path, version: str, ruleset_version: str | None = None) -> None:
        ruleset_version = ruleset_version or version
        policy.write_text(
            f'version: "{version}"\nruleset_version: "{ruleset_version}"\n'
            'forced_t2_files:\n  - "00_Admin/scripts/target_paths.py"\n',
            encoding="utf-8",
        )
        gate_file = repo / "00_Admin/scripts/closeout_security_prepass.py"
        gate_file.parent.mkdir(parents=True, exist_ok=True)
        gate_file.write_text("changed gate code\n", encoding="utf-8")
        self._git(repo, "add", "--", str(policy.relative_to(repo)), str(gate_file.relative_to(repo)))

    def _real_fixture(self) -> tuple[tempfile.TemporaryDirectory[str], Path, Path, Path]:
        temp_dir = tempfile.TemporaryDirectory()
        repo = Path(temp_dir.name)
        for relative, source in (
            ("00_Admin/configs/closeout_security_tiers.yaml", POLICY_SOURCE),
            ("00_Admin/scripts/closeout_security_prepass.py", PREPASS_SOURCE),
            ("00_Admin/scripts/validate_closeout_security_receipt.py", VALIDATOR_SOURCE),
            ("00_Admin/scripts/target_paths.py", TARGET_PATHS_SOURCE),
            ("00_Admin/scripts/hooks/validate_closeout_security_head.py", HOOK_SOURCE),
        ):
            destination = repo / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
        (repo / "changed.txt").write_text("baseline\n", encoding="utf-8")
        self._git(repo, "init", "--quiet")
        self._git(repo, "config", "user.name", "Closeout Hook Tests")
        self._git(repo, "config", "user.email", "tests@example.invalid")
        self._git(repo, "add", ".")
        self._git(repo, "commit", "--quiet", "-m", "baseline")
        return (
            temp_dir,
            repo,
            repo / "00_Admin/configs/closeout_security_tiers.yaml",
            repo / "00_Admin/scripts/hooks/validate_closeout_security_head.py",
        )

    def _run_hook(self, repo: Path, receipt: Path, first_landing_receipt: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(repo / "00_Admin/scripts/hooks/validate_closeout_security_head.py"),
                "--repo-root",
                str(repo),
                "--receipt",
                str(receipt),
                "--first-landing-receipt",
                str(first_landing_receipt),
                "--staged",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_policy_bump_with_gate_edit_and_no_receipt_is_blocked(self) -> None:
        temp_dir, repo, policy, _hook = self._fixture()
        try:
            self._stage_policy(repo, policy, "1.1.0")
            result = self._run_hook(
                repo,
                repo / ".ai_ops/local/closeout_security/latest.yaml",
                repo / ".ai_ops/local/closeout_security/first_landing.yaml",
            )
            self.assertNotEqual(0, result.returncode)
            self.assertIn("first-landing receipt", result.stderr)
        finally:
            temp_dir.cleanup()

    def test_valid_first_landing_receipt_passes(self) -> None:
        temp_dir, repo, policy, _hook = self._fixture()
        try:
            self._stage_policy(repo, policy, "1.1.0")
            receipt = repo / ".ai_ops/local/closeout_security/first_landing.yaml"
            receipt.parent.mkdir(parents=True)
            receipt.write_text(
                yaml.safe_dump(
                    {"first_landing": True, "repo_root": str(repo.resolve())}, sort_keys=False
                ),
                encoding="utf-8",
            )
            result = self._run_hook(repo, repo / "missing.yaml", receipt)
            self.assertEqual(0, result.returncode, result.stderr)
        finally:
            temp_dir.cleanup()

    def test_policy_downgrade_is_blocked(self) -> None:
        temp_dir, repo, policy, _hook = self._fixture()
        try:
            self._stage_policy(repo, policy, "0.9.0")
            receipt = repo / ".ai_ops/local/closeout_security/first_landing.yaml"
            receipt.parent.mkdir(parents=True)
            receipt.write_text(
                yaml.safe_dump(
                    {"first_landing": True, "repo_root": str(repo.resolve())}, sort_keys=False
                ),
                encoding="utf-8",
            )
            result = self._run_hook(repo, repo / "missing.yaml", receipt)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("downgrade", result.stderr)
        finally:
            temp_dir.cleanup()

    def test_ruleset_downgrade_is_blocked_when_policy_version_increases(self) -> None:
        temp_dir, repo, policy, _hook = self._fixture()
        try:
            self._stage_policy(repo, policy, "1.1.0", "0.9.0")
            receipt = repo / ".ai_ops/local/closeout_security/first_landing.yaml"
            receipt.parent.mkdir(parents=True)
            receipt.write_text("valid first landing\n", encoding="utf-8")
            result = self._run_hook(repo, repo / "missing.yaml", receipt)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("downgrade", result.stderr)
        finally:
            temp_dir.cleanup()

    def test_duplicate_policy_keys_are_blocked(self) -> None:
        temp_dir, repo, policy, _hook = self._fixture()
        try:
            policy.write_text(
                'version: "1.1.0"\nversion: "0.1.0"\n'
                'ruleset_version: "1.1.0"\n'
                'forced_t2_files:\n  - "00_Admin/scripts/target_paths.py"\n',
                encoding="utf-8",
            )
            gate_file = repo / "00_Admin/scripts/closeout_security_prepass.py"
            gate_file.write_text("changed gate code\n", encoding="utf-8")
            self._git(repo, "add", "00_Admin/configs/closeout_security_tiers.yaml", str(gate_file.relative_to(repo)))
            receipt = repo / ".ai_ops/local/closeout_security/first_landing.yaml"
            receipt.parent.mkdir(parents=True)
            receipt.write_text("valid first landing\n", encoding="utf-8")
            result = self._run_hook(repo, repo / "missing.yaml", receipt)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("valid HEAD-bound version baseline", result.stderr)
        finally:
            temp_dir.cleanup()

    def test_real_reviewer_read_receipt_passes_first_landing_gate(self) -> None:
        temp_dir, repo, policy, hook = self._real_fixture()
        try:
            policy_text = policy.read_text(encoding="utf-8")
            policy.write_text(
                policy_text.replace('version: "0.8.0"', 'version: "0.9.0"', 1).replace(
                    'ruleset_version: "0.8.0"', 'ruleset_version: "0.9.0"', 1
                ),
                encoding="utf-8",
            )
            (repo / "changed.txt").write_text("changed\n", encoding="utf-8")
            self._git(repo, "add", "00_Admin/configs/closeout_security_tiers.yaml", "changed.txt")
            receipt = repo / ".ai_ops/local/closeout_security/first_landing.yaml"
            packet = repo / ".ai_ops/local/closeout_security/first_landing_packet.md"
            prepass = subprocess.run(
                [
                    sys.executable,
                    str(repo / "00_Admin/scripts/closeout_security_prepass.py"),
                    "--repo-root", str(repo), "--source", "staged",
                    "--receipt-path", str(receipt), "--packet-path", str(packet),
                    "00_Admin/configs/closeout_security_tiers.yaml", "changed.txt",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, prepass.returncode, prepass.stderr)
            data = yaml.safe_load(receipt.read_text(encoding="utf-8"))
            snapshot_rows = []
            for row in data["rows"]:
                row.update(
                    {
                        "coverage": "fully_reviewed",
                        "reviewer": "Primary",
                        "reviewer_model": "maximum",
                        "reviewer_runtime": "test",
                        "review_method": "full-file-plus-diff",
                        "disposition": "pass",
                    }
                )
                if row["prepass_status"] == "candidate":
                    row["finding_refs"] = row.get("finding_refs") or ["TEST-CANDIDATE"]
                    row["coverage_notes"] = (
                        str(row.get("coverage_notes", "")) + "; candidate_resolution=resolved"
                    ).lstrip("; ")
                if row["tier"] == "T2":
                    row.update({"independent_pass": True, "independent_reviewer": "Sol"})
                    snapshot_rows.append(
                        {
                            "path": row["path"],
                            "sha256": row["sha256"],
                            "mode": row["mode"],
                            "reviewer": "Sol",
                            "disposition": "pass",
                        }
                    )
            snapshot = repo / ".ai_ops/local/closeout_security/first_landing_snapshot.yaml"
            snapshot.write_text(
                yaml.safe_dump(
                    {
                        "snapshot_version": "1.0.0",
                        "repo_root": str(repo.resolve()),
                        "base_head": data["base_head"],
                        "scope_lock_sha256": data["scope_lock_sha256"],
                        "independent_reviewer": "Sol",
                        "rows": snapshot_rows,
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            snapshot_hash = hashlib.sha256(snapshot.read_bytes()).hexdigest()
            for row in data["rows"]:
                if row["tier"] == "T2":
                    row["independent_evidence"] = (
                        f"snapshot={snapshot.relative_to(repo).as_posix()}; evidence_sha256={snapshot_hash}"
                    )
            data.pop("receipt_sha256", None)
            data["receipt_sha256"] = hashlib.sha256(
                yaml.safe_dump(data, sort_keys=True).encode("utf-8")
            ).hexdigest()
            receipt.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(hook),
                    "--repo-root", str(repo),
                    "--receipt", str(repo / "missing.yaml"),
                    "--first-landing-receipt", str(receipt),
                    "--staged",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, result.returncode, result.stderr)
        finally:
            temp_dir.cleanup()


if __name__ == "__main__":
    unittest.main()
