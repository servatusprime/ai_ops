#!/usr/bin/env python
"""Run the HEAD copy of the closeout receipt validator from pre-commit."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

VALIDATOR = "00_Admin/scripts/validate_closeout_security_receipt.py"
POLICY = "00_Admin/configs/closeout_security_tiers.yaml"
FORCED_PREFIXES = (
    ".ai_ops/workflows/",
    "00_Admin/configs/",
    "00_Admin/policies/",
    "00_Admin/specs/",
    "plugins/",
    ".claude/",
    ".agents/",
    "01_Resources/templates/config/",
    ".githooks/",
)
FORCED_FILES = {"AGENTS.md", "CLAUDE.md", ".pre-commit-config.yaml", "SECURITY.md"}
SECURITY_FILES = {
    "00_Admin/scripts/closeout_security_prepass.py",
    "00_Admin/scripts/validate_closeout_security_receipt.py",
    "00_Admin/scripts/target_paths.py",
    "00_Admin/scripts/check_outside_writes.py",
    "00_Admin/scripts/hooks/guard_workspace_writes.py",
    "00_Admin/scripts/hooks/validate_closeout_security_head.py",
    "00_Admin/configs/closeout_security_tiers.yaml",
}


def head_text(repo: Path, path: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), "show", f"HEAD:{path}"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        raise SystemExit(result.stderr.decode(errors="replace").strip())
    return result.stdout.decode("utf-8")


def receipt_header(path: Path) -> tuple[str, str] | None:
    text = path.read_text(encoding="utf-8")
    repo = re.search(r"^repo_root:\s*(.+)$", text, re.MULTILINE)
    head = re.search(r"^base_head:\s*([0-9a-f]{40})$", text, re.MULTILINE)
    return (repo.group(1).strip().strip('"\''), head.group(1)) if repo and head else None


def staged_paths(repo: Path) -> set[str]:
    result = subprocess.run(
        ["git", "-C", str(repo), "diff", "--cached", "--name-only", "--no-renames", "--"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        raise SystemExit(result.stderr.strip() or "closeout-security-hook: cannot inspect staged paths")
    return {line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()}


def security_paths(paths: set[str]) -> set[str]:
    return {
        path
        for path in paths
        if path in FORCED_FILES
        or path in SECURITY_FILES
        or any(path.startswith(prefix) for prefix in FORCED_PREFIXES)
    }


def trusted_validator_present(repo: Path) -> bool:
    return subprocess.run(
        ["git", "-C", str(repo), "cat-file", "-e", f"HEAD:{VALIDATOR}"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0


class _UniqueKeyLoader(yaml.SafeLoader):
    """Reject duplicate YAML keys instead of silently accepting the last one."""


def _construct_unique_mapping(loader: _UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False) -> dict:
    mapping: dict = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ValueError(f"duplicate YAML key: {key}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def _policy_versions(text: str) -> tuple[str, str] | None:
    try:
        policy = yaml.load(text, Loader=_UniqueKeyLoader) or {}
    except (ValueError, yaml.YAMLError):
        return None
    if not isinstance(policy, dict):
        return None
    version = policy.get("version")
    ruleset = policy.get("ruleset_version")
    if not isinstance(version, str) or not isinstance(ruleset, str):
        return None
    return version.strip(), ruleset.strip()


def _version_key(value: str) -> tuple[int, ...] | None:
    parts = value.split(".")
    if not parts or any(not part.isdigit() for part in parts):
        return None
    return tuple(int(part) for part in parts)


def staged_policy_state(repo: Path, paths: set[str]) -> str:
    """Classify a staged canonical policy change without trusting staged code."""

    if POLICY not in paths:
        return "unchanged"
    result = subprocess.run(
        ["git", "-C", str(repo), "show", f":{POLICY}"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        return "invalid"
    staged = result.stdout.decode("utf-8", errors="replace")
    try:
        head = head_text(repo, POLICY)
    except SystemExit:
        return "missing-baseline"
    staged_versions = _policy_versions(staged)
    head_versions = _policy_versions(head)
    if staged_versions is None or head_versions is None:
        return "invalid"
    if staged_versions == head_versions:
        return "unchanged"
    staged_keys = tuple(_version_key(value) for value in staged_versions)
    head_keys = tuple(_version_key(value) for value in head_versions)
    if any(value is None for value in staged_keys + head_keys):
        return "invalid"
    if any(staged_key < head_key for staged_key, head_key in zip(staged_keys, head_keys, strict=True)):
        return "downgrade"
    return "upgrade"


def _run_validator(
    repo: Path,
    receipt: Path,
    *,
    commit_msg_file: Path | None = None,
    first_landing: bool = False,
) -> int:
    with tempfile.TemporaryDirectory() as tmp:
        validator = Path(tmp) / "validate_closeout_security_receipt.py"
        validator.write_text(head_text(repo, VALIDATOR), encoding="utf-8")
        target_paths = Path(tmp) / "target_paths.py"
        target_paths.write_text(head_text(repo, "00_Admin/scripts/target_paths.py"), encoding="utf-8")
        command = [
            sys.executable,
            str(validator),
            "--repo-root",
            str(repo),
            "--receipt",
            str(receipt),
            "--gate",
            "--staged",
        ]
        if first_landing:
            command.extend(["--first-landing", "--config", str(repo / POLICY)])
        elif commit_msg_file:
            command.extend(["--commit-msg-file", str(commit_msg_file)])
        return subprocess.run(command, check=False).returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument(
        "--first-landing-receipt",
        type=Path,
        default=Path(".ai_ops/local/closeout_security/first_landing.yaml"),
    )
    parser.add_argument("--staged", action="store_true")
    parser.add_argument("--commit-msg-file", type=Path)
    args = parser.parse_args()
    repo = args.repo_root.resolve()
    receipt = (repo / args.receipt).resolve() if not args.receipt.is_absolute() else args.receipt.resolve()
    paths = staged_paths(repo)
    protected = security_paths(paths)
    trusted = trusted_validator_present(repo)
    policy_state = staged_policy_state(repo, paths)
    if policy_state in {"invalid", "missing-baseline"}:
        print(
            "closeout-security-hook: staged canonical policy has no valid HEAD-bound version baseline",
            file=sys.stderr,
        )
        return 1
    if policy_state == "downgrade":
        print("closeout-security-hook: staged closeout-security policy downgrade is blocked", file=sys.stderr)
        return 1
    if policy_state == "upgrade":
        if not trusted:
            print(
                "closeout-security-hook: first landing requires the HEAD validator; none is present",
                file=sys.stderr,
            )
            return 1
        first_landing_receipt = args.first_landing_receipt
        env_receipt = os.environ.get("AI_OPS_FIRST_LANDING_RECEIPT")
        if env_receipt:
            first_landing_receipt = Path(env_receipt)
        if not first_landing_receipt.is_absolute():
            first_landing_receipt = repo / first_landing_receipt
        first_landing_receipt = first_landing_receipt.resolve()
        if not first_landing_receipt.exists():
            print(
                "closeout-security-hook: first-landing receipt is missing",
                file=sys.stderr,
            )
            return 1
        return _run_validator(repo, first_landing_receipt, first_landing=True)
    has_trailer = False
    if args.commit_msg_file:
        message = args.commit_msg_file.read_text(encoding="utf-8")
        matches = [line.strip() for line in message.splitlines() if line.strip().startswith("Closeout-Security:")]
        if not matches:
            if protected and trusted:
                print(
                    "closeout-security-hook: staged security-governed paths require "
                    "a Closeout-Security trailer",
                    file=sys.stderr,
                )
                return 1
            print("closeout-security-hook: no trailer; ordinary commit is unchanged")
            return 0
        has_trailer = True
    if not receipt.exists():
        if has_trailer:
            print("closeout-security-hook: trailer present but receipt is missing", file=sys.stderr)
            return 1
        if protected and trusted:
            print(
                "closeout-security-hook: staged security-governed paths require a current receipt",
                file=sys.stderr,
            )
            return 1
        print("closeout-security-hook: no receipt; ordinary commit is unchanged")
        return 0
    header = receipt_header(receipt)
    current_head = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    if not has_trailer and (not header or header != (str(repo), current_head)):
        if protected and trusted:
            print(
                "closeout-security-hook: staged security-governed paths require a current receipt",
                file=sys.stderr,
            )
            return 1
        print("closeout-security-hook: receipt is for another repo or HEAD; ordinary commit is unchanged")
        return 0
    return _run_validator(repo, receipt, commit_msg_file=args.commit_msg_file)


if __name__ == "__main__":
    raise SystemExit(main())
