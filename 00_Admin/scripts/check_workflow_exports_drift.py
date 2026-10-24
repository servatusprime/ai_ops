#!/usr/bin/env python3
"""Check drift between workflow export manifest and current files.

Two independent checks are performed:

1. Manifest-vs-disk drift (original check): does each output file's current
   hash match what manifest.yaml *claims* it should be? This catches simple
   staleness (forgot to regenerate) but can be defeated by a coordinated edit
   that changes an output file and its manifest entry together.
2. Source-vs-disk verification (added 2026-08-26, SEC-AIOPS-004): independently
   re-renders each output from the current .ai_ops/workflows/*.md source --
   via a subprocess call to generate_workflow_exports.py --dry-run
   --print-manifest, which never reads or trusts manifest.yaml -- and compares
   that freshly-rendered hash against the *actual on-disk output file*. This
   closes the gap check 1 cannot: it cannot be fooled by tampering with
   manifest.yaml, because it never consults it.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None

PRIMARY_MANIFEST_REL = Path(".ai_ops/exports/manifest.yaml")
EXPECTED_SOURCE_ROOT_REL = Path(".ai_ops/workflows")
GENERATOR_REL = Path("00_Admin/scripts/generate_workflow_exports.py")
_REPARSE_POINT = 0x400


def _is_reparse_point(path: Path) -> bool:
    try:
        info = path.lstat()
    except OSError:
        return False
    return path.is_symlink() or bool(getattr(info, "st_file_attributes", 0) & _REPARSE_POINT)


def safe_repo_path(repo_root: Path, raw_path: str, *, label: str) -> Path:
    """Resolve a manifest path only after lexical and resolved containment checks."""
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise ValueError(f"{label} must be a non-empty relative path")
    lexical_root = repo_root.resolve(strict=True)
    lexical_path = Path(os.path.abspath(os.fspath(repo_root / raw_path)))
    try:
        relative = lexical_path.relative_to(lexical_root)
    except ValueError as exc:
        raise ValueError(f"{label} escapes repository root: {raw_path}") from exc

    current = lexical_root
    for part in relative.parts:
        current = current / part
        if os.path.lexists(os.fspath(current)) and _is_reparse_point(current):
            raise ValueError(f"{label} crosses a symlink/reparse point: {raw_path}")

    resolved = lexical_path.resolve(strict=False)
    try:
        resolved.relative_to(lexical_root)
    except ValueError as exc:
        raise ValueError(f"{label} resolves outside repository root: {raw_path}") from exc
    return resolved


def sha12(path: Path) -> str:
    # Normalize line endings so manifest source hashes are stable across
    # Windows and Unix checkout styles.
    text = path.read_text(encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def independently_rendered_manifest(
    repo_root: Path, targets: List[str], scope: str, codex_compat: bool = False
) -> Optional[Dict]:
    """Run the generator in --dry-run --print-manifest mode and parse its
    freshly-rendered manifest. Returns None on any failure (subprocess error,
    unparsable output) -- callers must treat that as "could not verify", not
    as a clean result."""
    cmd = [
        sys.executable,
        str(repo_root / GENERATOR_REL),
        "--dry-run",
        "--print-manifest",
        "--targets",
        *targets,
        "--scope",
        scope,
    ]
    if codex_compat:
        # The compatibility mirror is an explicit generation option rather
        # than a target. Preserve that option during independent rendering so
        # the check verifies the same governed surface recorded in the
        # manifest instead of reporting every .codex output as phantom.
        cmd.append("--codex-compat")
    try:
        result = subprocess.run(
            cmd, cwd=repo_root, capture_output=True, text=True, timeout=60
        )
    except Exception:  # noqa: BLE001
        return None
    if result.returncode != 0:
        return None
    stdout = result.stdout
    begin = stdout.find("---MANIFEST-BEGIN---")
    end = stdout.find("---MANIFEST-END---")
    if begin == -1 or end == -1 or end <= begin:
        return None
    yaml_text = stdout[begin + len("---MANIFEST-BEGIN---") : end]
    try:
        return yaml.safe_load(yaml_text) or {}
    except Exception:  # noqa: BLE001
        return None


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
    try:
        manifest_path = safe_repo_path(repo_root, args.manifest, label="manifest path")
    except ValueError as exc:
        print(f"[FAIL] Invalid manifest path: {exc}")
        return 2

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

    source_root_rel = manifest.get("source_root", EXPECTED_SOURCE_ROOT_REL.as_posix())
    discovered_sources: set[str] = set()
    try:
        normalized_source_root = (
            source_root_rel.replace("\\", "/") if isinstance(source_root_rel, str) else None
        )
        if normalized_source_root != EXPECTED_SOURCE_ROOT_REL.as_posix():
            source_drift.append(
                "manifest source_root must equal "
                f"{EXPECTED_SOURCE_ROOT_REL.as_posix()} (got {source_root_rel!r})"
            )
        # Source discovery is anchored to the generator's canonical source root,
        # never to a manifest-controlled directory that could be empty.
        source_root = safe_repo_path(
            repo_root,
            EXPECTED_SOURCE_ROOT_REL.as_posix(),
            label="canonical workflow source_root",
        )
        if source_root.is_dir():
            discovered_sources = {
                path.relative_to(repo_root).as_posix()
                for path in source_root.glob("*.md")
                if os.path.lexists(os.fspath(path))
                and (path.is_file() or _is_reparse_point(path))
            }
        else:
            source_drift.append(f"missing source root: {source_root_rel}")
    except (TypeError, ValueError) as exc:
        source_drift.append(f"invalid source root: {exc}")

    manifest_sources: List[str] = []
    duplicate_sources: set[str] = set()

    for workflow in workflows:
        if not isinstance(workflow, dict):
            output_drift.append("invalid workflow entry type")
            continue

        source_rel = workflow.get("source")
        source_hash = workflow.get("source_sha256_12")
        if isinstance(source_rel, str):
            normalized_source = source_rel.replace("\\", "/")
            if normalized_source in manifest_sources:
                duplicate_sources.add(normalized_source)
            manifest_sources.append(normalized_source)
        if isinstance(source_rel, str) and isinstance(source_hash, str):
            try:
                source_path = safe_repo_path(repo_root, source_rel, label="manifest source")
            except ValueError as exc:
                source_drift.append(f"invalid source: {exc}")
                source_path = None
            if source_path is None:
                pass
            elif not source_path.exists():
                source_drift.append(f"missing source: {source_rel}")
            else:
                current = sha12(source_path)
                if current != source_hash:
                    source_drift.append(
                        f"source changed: {source_rel} (manifest={source_hash}, current={current})"
                    )

    if duplicate_sources:
        source_drift.extend(
            f"duplicate manifest source: {source}" for source in sorted(duplicate_sources)
        )
    manifest_source_set = set(manifest_sources)
    for missing_source in sorted(discovered_sources - manifest_source_set):
        source_drift.append(f"manifest missing workflow source: {missing_source}")
    for extra_source in sorted(manifest_source_set - discovered_sources):
        source_drift.append(f"manifest has undiscovered workflow source: {extra_source}")

    # Continue with per-workflow output checks after the source-set contract.
    for workflow in workflows:
        if not isinstance(workflow, dict):
            continue

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
            try:
                out_path = safe_repo_path(repo_root, out_rel, label="manifest output")
            except ValueError as exc:
                output_drift.append(f"invalid output: {exc}")
                continue
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
            # The companion file carries required, schema-validated fields.
            required_output_kinds.add("codex_skill_primary_openai_yaml")
        missing_output_kinds = sorted(required_output_kinds - output_kinds)
        if missing_output_kinds:
            workflow_name = workflow.get("workflow", "<unknown>")
            output_drift.append(
                f"{workflow_name}: manifest missing output kinds: {', '.join(missing_output_kinds)}"
            )

    # Independent re-render verification (SEC-AIOPS-004): never consults
    # manifest.yaml, so it cannot be fooled by a manifest that was tampered
    # in sync with an output file.
    render_drift: List[str] = []
    render_check_skipped = False
    scope = manifest.get("scope")
    manifest_targets_list = sorted(manifest_targets) if manifest_targets else []
    if not isinstance(scope, str) or not manifest_targets_list:
        render_check_skipped = True
    else:
        manifest_has_codex_compat = any(
            isinstance(output, dict)
            and output.get("kind") in {"codex_skill_compat", "codex_skill_compat_openai_yaml"}
            for workflow in workflows
            if isinstance(workflow, dict)
            for output in workflow.get("outputs", [])
            if isinstance(workflow.get("outputs", []), list)
        )
        rendered = independently_rendered_manifest(
            repo_root,
            manifest_targets_list,
            scope,
            codex_compat=manifest_has_codex_compat,
        )
        if rendered is None:
            render_check_skipped = True
        else:
            rendered_workflows = {
                w.get("workflow"): w
                for w in rendered.get("workflows", [])
                if isinstance(w, dict)
            }
            for workflow in workflows:
                if not isinstance(workflow, dict):
                    continue
                name = workflow.get("workflow")
                rendered_wf = rendered_workflows.get(name)
                if rendered_wf is None:
                    render_drift.append(f"{name}: not present in independently-rendered manifest")
                    continue
                rendered_outputs = {
                    o.get("path"): o.get("sha256_12")
                    for o in rendered_wf.get("outputs", [])
                    if isinstance(o, dict)
                }
                for output in workflow.get("outputs", []):
                    if not isinstance(output, dict):
                        continue
                    out_rel = output.get("path")
                    if not isinstance(out_rel, str):
                        continue
                    try:
                        out_path = safe_repo_path(repo_root, out_rel, label="rendered output")
                    except ValueError as exc:
                        render_drift.append(f"invalid rendered output: {exc}")
                        continue
                    expected_hash = rendered_outputs.get(out_rel)
                    if expected_hash is None:
                        render_drift.append(
                            f"{out_rel}: not present in independently-rendered manifest"
                        )
                        continue
                    if not out_path.exists():
                        continue  # already reported as missing in output_drift above
                    actual_hash = sha12(out_path)
                    if actual_hash != expected_hash:
                        render_drift.append(
                            f"phantom canon: {out_rel} does not match what its declared "
                            f"source (.ai_ops/workflows/{name}.md) actually renders to "
                            f"(independently-rendered={expected_hash}, on-disk={actual_hash}). "
                            f"manifest.yaml's own recorded hash for this path may agree with "
                            f"the on-disk file -- that would mean the manifest was tampered "
                            f"in sync with the file, not that the file is correct."
                        )

    total_drift = len(source_drift) + len(output_drift) + len(render_drift)

    print("[Workflow Export Drift Check]")
    print(f"Manifest: {manifest_path.relative_to(repo_root)}")
    print(f"Source drift: {len(source_drift)}")
    print(f"Output drift: {len(output_drift)}")
    if render_check_skipped:
        print("Independent re-render check: SKIPPED (could not run generator or parse its output)")
    else:
        print(f"Independent re-render drift: {len(render_drift)}")
    print(f"Total drift findings: {total_drift}")

    if source_drift:
        print("\n[Source Drift]")
        for item in source_drift:
            print(f"- {item}")

    if output_drift:
        print("\n[Output Drift]")
        for item in output_drift:
            print(f"- {item}")

    if render_drift:
        print("\n[Independent Re-Render Drift]")
        for item in render_drift:
            print(f"- {item}")

    if render_check_skipped:
        print(
            "\n[UNVERIFIED] The independent re-render check could not run (generator "
            "subprocess failed or its output could not be parsed). This is NOT the "
            "same as a clean result -- manifest-vs-disk drift may look clean while "
            "the phantom-canon check that would catch a tampered manifest never ran. "
            "Fix whatever broke the generator invocation before trusting this report."
        )
        return 1 if args.strict else 0

    if total_drift == 0:
        print("\n[OK] No workflow export drift detected (including independent re-render verification).")
        return 0

    print("\n[DRIFT] Regenerate exports with:")
    print("- python 00_Admin/scripts/generate_workflow_exports.py")
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
