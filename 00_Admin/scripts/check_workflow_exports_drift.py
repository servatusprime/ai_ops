#!/usr/bin/env python3
"""Check drift between workflow export manifest and current files."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from typing import List

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None

PRIMARY_MANIFEST_REL = Path(".ai_ops/exports/manifest.yaml")


def sha12(path: Path) -> str:
    # Normalize line endings so manifest source hashes are stable across
    # Windows and Unix checkout styles.
    text = path.read_text(encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check workflow export manifest drift against source and generated files."
    )
    parser.add_argument(
        "--manifest",
        default=PRIMARY_MANIFEST_REL.as_posix(),
        help=f"Path to export manifest (default: {PRIMARY_MANIFEST_REL.as_posix()}).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return exit code 1 when drift is found.",
    )
    parser.add_argument(
        "--require-manifest",
        action="store_true",
        help="Return exit code 1 when manifest is missing.",
    )
    args = parser.parse_args()

    if yaml is None:
        print("[FAIL] PyYAML is required. Install with: pip install pyyaml")
        return 2

    repo_root = Path(__file__).resolve().parents[2]
    manifest_path = (repo_root / args.manifest).resolve()

    if not manifest_path.exists():
        message = f"[INFO] Export manifest not found: {manifest_path}"
        if args.require_manifest:
            print(message.replace("[INFO]", "[FAIL]"))
            return 1
        print(message)
        return 0

    try:
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] Could not parse manifest: {exc}")
        return 2

    workflows = manifest.get("workflows", [])
    if not isinstance(workflows, list):
        print("[FAIL] Manifest 'workflows' must be a list")
        return 2

    source_drift: List[str] = []
    output_drift: List[str] = []
    manifest_targets = set()
    manifest_targets_raw = manifest.get("targets", [])
    if isinstance(manifest_targets_raw, list):
        for target in manifest_targets_raw:
            if isinstance(target, str):
                manifest_targets.add(target)

    for workflow in workflows:
        if not isinstance(workflow, dict):
            output_drift.append("invalid workflow entry type")
            continue

        source_rel = workflow.get("source")
        source_hash = workflow.get("source_sha256_12")
        if isinstance(source_rel, str) and isinstance(source_hash, str):
            source_path = repo_root / source_rel
            if not source_path.exists():
                source_drift.append(f"missing source: {source_rel}")
            else:
                current = sha12(source_path)
                if current != source_hash:
                    source_drift.append(
                        f"source changed: {source_rel} (manifest={source_hash}, current={current})"
                    )

        outputs = workflow.get("outputs", [])
        if not isinstance(outputs, list):
            output_drift.append(f"{workflow.get('workflow', '<unknown>')}: outputs not a list")
            continue

        output_kinds = set()
        for output in outputs:
            if not isinstance(output, dict):
                output_drift.append("invalid output entry type")
                continue
            out_rel = output.get("path")
            out_hash = output.get("sha256_12")
            out_kind = output.get("kind", "output")
            if isinstance(out_kind, str):
                output_kinds.add(out_kind)
            if not isinstance(out_rel, str) or not isinstance(out_hash, str):
                output_drift.append(f"invalid output record: {output}")
                continue
            out_path = repo_root / out_rel
            if not out_path.exists():
                output_drift.append(f"missing {out_kind}: {out_rel}")
                continue
            current_out_hash = sha12(out_path)
            if current_out_hash != out_hash:
                output_drift.append(
                    f"stale {out_kind}: {out_rel} (manifest={out_hash}, current={current_out_hash})"
                )

        required_output_kinds = {"plugin_command", "plugin_skill"}
        if "claude" in manifest_targets:
            required_output_kinds.add("claude_skill")
        if "codex" in manifest_targets:
            required_output_kinds.add("codex_skill_primary")
        missing_output_kinds = sorted(required_output_kinds - output_kinds)
        if missing_output_kinds:
            workflow_name = workflow.get("workflow", "<unknown>")
            output_drift.append(
                f"{workflow_name}: manifest missing output kinds: {', '.join(missing_output_kinds)}"
            )

    total_drift = len(source_drift) + len(output_drift)

    print("[Workflow Export Drift Check]")
    print(f"Manifest: {manifest_path.relative_to(repo_root)}")
    print(f"Source drift: {len(source_drift)}")
    print(f"Output drift: {len(output_drift)}")
    print(f"Total drift findings: {total_drift}")

    if source_drift:
        print("\n[Source Drift]")
        for item in source_drift:
            print(f"- {item}")

    if output_drift:
        print("\n[Output Drift]")
        for item in output_drift:
            print(f"- {item}")

    if total_drift == 0:
        print("\n[OK] No workflow export drift detected.")
        return 0

    print("\n[DRIFT] Regenerate exports with:")
    print("- python 00_Admin/scripts/generate_workflow_exports.py")
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
