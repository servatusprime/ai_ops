#!/usr/bin/env python3
"""Template: Python script scaffold for ai_ops and sibling repos.

Usage:
    python <script_name>.py --input <input_path> --output-dir <output_dir>
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

LOG = logging.getLogger(__name__)

CONTRACT = {
    "id": "template_script_id",
    "filename": "<script_name>.py",
    "inputs": ["<input_path>"],
    "outputs": ["<output_dir_or_file>"],
    "crs": "",
    "idempotent": True,
    "qgis_required": False,
}


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="TODO: Replace with script-specific description.",
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Input file path.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Output directory path.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root used for run manifest output.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser.parse_args()


def setup_logging(verbose: bool) -> None:
    """Configure logging level and format."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def validate_paths(input_path: Path, output_dir: Path) -> tuple[Path, Path]:
    """Resolve and validate paths before execution."""
    resolved_input = input_path.expanduser().resolve()
    resolved_output = output_dir.expanduser().resolve()

    if not resolved_input.exists():
        raise FileNotFoundError(f"Input path not found: {resolved_input}")

    resolved_output.mkdir(parents=True, exist_ok=True)
    return resolved_input, resolved_output


def list_files_excluding_paths(source_dir: Path, excluded_paths: set[Path] | None = None) -> list[Path]:
    """List files under a directory, excluding explicit paths.

    Use this helper when packaging/bundling to avoid self-including output files.
    """
    excluded = {p.resolve() for p in (excluded_paths or set())}
    files: list[Path] = []
    for candidate in source_dir.rglob("*"):
        if not candidate.is_file():
            continue
        if candidate.resolve() in excluded:
            continue
        files.append(candidate)
    return files


def run(input_path: Path, output_dir: Path) -> int:
    """Execute script logic.

    Returns:
        0 on success, non-zero on failure.
    """
    LOG.info("Starting script.")
    LOG.info("Input: %s", input_path)
    LOG.info("Output dir: %s", output_dir)

    # TODO: Implement script-specific logic here.
    # Keep filesystem paths via pathlib.Path and avoid hard-coded machine paths.
    #
    # Safety checklist:
    # 1) If filtering multiple geometry types (Point/MultiPoint, etc.), make
    #    sure downstream field access supports all allowed types.
    # 2) If scanning output trees, exclude current output artifacts explicitly.
    # 3) If CONTRACT["idempotent"] is True, verify reruns fully refresh outputs.

    LOG.info("Completed successfully.")
    return 0


def write_run_manifest(
    project_root: Path,
    exit_code: int,
    inputs: dict[str, str],
    outputs: list[str],
) -> Path:
    """Write run manifest under admin/run_logs."""
    logs_dir = project_root / "admin" / "run_logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    manifest = {
        "script_id": CONTRACT["id"],
        "filename": CONTRACT["filename"],
        "timestamp_utc": ts,
        "status": "success" if exit_code == 0 else "failed",
        "exit_code": exit_code,
        "inputs": inputs,
        "outputs": outputs,
    }
    manifest_path = logs_dir / f"run_{CONTRACT['id']}_{ts}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path


def main() -> int:
    """Program entrypoint."""
    args = parse_args()
    setup_logging(verbose=args.verbose)

    try:
        input_path, output_dir = validate_paths(args.input, args.output_dir)
        rc = run(input_path=input_path, output_dir=output_dir)
        manifest_path = write_run_manifest(
            project_root=args.project_root.expanduser().resolve(),
            exit_code=rc,
            inputs={"input": str(input_path)},
            outputs=[str(output_dir)],
        )
        LOG.info("Run manifest written: %s", manifest_path)
        return rc
    except Exception as exc:  # noqa: BLE001
        LOG.exception("Unhandled error: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
