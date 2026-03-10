#!/usr/bin/env python3
"""Generate a markdown scorecard from the future work registry YAML."""

from __future__ import annotations

from argparse import ArgumentParser
from datetime import date
from pathlib import Path
from typing import Any

import yaml


def _norm(value: Any, default: str = "-") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _escape_cell(value: Any) -> str:
    return _norm(value).replace("|", "\\|")


def _priority_rank(priority: str) -> int:
    order = {"high": 0, "medium": 1, "low": 2}
    return order.get(priority.lower(), 9)


def _read_registry(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Registry root must be a mapping: {path}")
    return data


def _build_rows(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        fw_id = _norm(entry.get("id"))
        if fw_id == "-" or fw_id.startswith("fw_YYYY"):
            continue
        rows.append(entry)
    rows.sort(
        key=lambda item: (
            _priority_rank(_norm(item.get("priority"), "medium")),
            _norm(item.get("next_review"), "9999-99-99"),
            _norm(item.get("id")),
        )
    )
    return rows


def _render_markdown(registry_path: Path, rows: list[dict[str, Any]]) -> str:
    today = date.today().isoformat()
    lines: list[str] = [
        "---",
        "title: Future Work Scorecard",
        "version: 0.1.0",
        "status: active",
        f"updated: '{today}'",
        f"source_registry: {registry_path.as_posix()}",
        "generated_by: 00_Admin/scripts/generate_future_work_scorecard.py",
        "---",
        "",
        "<!-- markdownlint-disable-next-line MD025 -->",
        "# Future Work Scorecard",
        "",
        "> Auto-generated. Do not edit manually; update the registry and regenerate.",
        "",
        "<!-- markdownlint-disable MD013 -->",
        "| ID | Title | Domain | Repo | Priority | Benefit | Effort | Readiness | Deferred Risk | Next Review |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]

    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_cell(row.get("id")),
                    _escape_cell(row.get("title")),
                    _escape_cell(row.get("domain")),
                    _escape_cell(row.get("target_repo")),
                    _escape_cell(row.get("priority")),
                    _escape_cell(row.get("benefit")),
                    _escape_cell(row.get("effort")),
                    _escape_cell(row.get("readiness")),
                    _escape_cell(row.get("risk_if_deferred")),
                    _escape_cell(row.get("next_review")),
                ]
            )
            + " |"
        )

    if not rows:
        lines.append("| - | No active entries | - | - | - | - | - | - | - | - |")

    lines.append("<!-- markdownlint-enable MD013 -->")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Registry and scorecard should be updated together in the same change.",
            "- Use `python ai_ops/00_Admin/scripts/generate_future_work_scorecard.py` after registry edits.",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = ArgumentParser(description="Generate future work scorecard markdown.")
    parser.add_argument(
        "--registry",
        default="ai_ops/00_Admin/backlog/future_work_registry.yaml",
        help="Path to future work registry YAML.",
    )
    parser.add_argument(
        "--output",
        default="ai_ops/00_Admin/backlog/future_work_scorecard.md",
        help="Path to generated markdown scorecard.",
    )
    args = parser.parse_args()

    registry_path = Path(args.registry)
    output_path = Path(args.output)
    data = _read_registry(registry_path)
    entries = data.get("entries", [])
    if not isinstance(entries, list):
        raise ValueError("Registry 'entries' must be a list.")
    rows = _build_rows(entries)
    content = _render_markdown(registry_path, rows)
    output_path.write_text(content + "\n", encoding="utf-8", newline="\n")
    print(f"Generated {output_path} from {registry_path} ({len(rows)} rows).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
