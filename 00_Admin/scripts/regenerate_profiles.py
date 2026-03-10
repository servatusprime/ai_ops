#!/usr/bin/env python3
"""Regenerate ai_ops profile-derived behavior files.

This script reads profile source YAML and writes deterministic derivative files:
- plugins/ai-ops-governance/agents/*.md
- 02_Modules/01_agent_profiles/generated/single_agent_profile_map.md
- 02_Modules/01_agent_profiles/generated/lead_agent_profile_context.md
- 02_Modules/01_agent_profiles/generated/model_tuning_summary.md
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None


SLIDERS: Tuple[str, ...] = (
    "communication_depth",
    "tone_warmth",
    "formality",
    "directness",
    "autonomy",
    "conservatism",
    "initiative",
    "deference",
)

PROFESSIONAL_SLIDERS: Tuple[str, ...] = (
    "autonomy",
    "conservatism",
    "initiative",
    "deference",
)

COMMUNICATION_SLIDERS: Tuple[str, ...] = (
    "communication_depth",
    "tone_warmth",
    "formality",
    "directness",
)

WRITE_ROLES = {"ai-ops-executor", "ai-ops-closer"}

RIDER_ARCHETYPES: Dict[str, Dict[str, int]] = {
    "logike": {
        "communication_depth": 40,
        "tone_warmth": 20,
        "formality": 75,
        "directness": 80,
        "autonomy": 55,
        "conservatism": 75,
        "initiative": 30,
        "deference": 60,
    },
    "scooter": {
        "communication_depth": 65,
        "tone_warmth": 75,
        "formality": 35,
        "directness": 45,
        "autonomy": 50,
        "conservatism": 55,
        "initiative": 60,
        "deference": 60,
    },
    "forge": {
        "communication_depth": 25,
        "tone_warmth": 35,
        "formality": 50,
        "directness": 75,
        "autonomy": 75,
        "conservatism": 45,
        "initiative": 45,
        "deference": 45,
    },
    "anchor": {
        "communication_depth": 55,
        "tone_warmth": 30,
        "formality": 70,
        "directness": 70,
        "autonomy": 25,
        "conservatism": 90,
        "initiative": 20,
        "deference": 80,
    },
    "scout": {
        "communication_depth": 75,
        "tone_warmth": 45,
        "formality": 55,
        "directness": 55,
        "autonomy": 70,
        "conservatism": 60,
        "initiative": 70,
        "deference": 55,
    },
}

FRAGMENTS = {
    "autonomy": {
        "T1": "Confirm before multi-step actions and avoid assumptions.",
        "T2": "Proceed cautiously and check in at key boundaries.",
        "T3": "Proceed on clear tasks and ask when scope is ambiguous.",
        "T4": "Operate independently within scope and report outcomes.",
        "T5": "Run with high independence and return concise completion reports.",
    },
    "conservatism": {
        "T1": "Explore broadly and tolerate high variation in approach.",
        "T2": "Favor practical speed with moderate scope flexibility.",
        "T3": "Balance speed and risk while keeping scope discipline.",
        "T4": "Prefer targeted, low-risk edits and explicit scope guardrails.",
        "T5": "Use strict scope boundaries and minimize all optional changes.",
    },
    "initiative": {
        "T1": "Avoid unsolicited suggestions and follow direct instructions only.",
        "T2": "Offer limited suggestions when blockers are likely.",
        "T3": "Suggest practical next steps when they materially reduce risk.",
        "T4": "Proactively surface improvements tied to the active objective.",
        "T5": "Consistently identify improvement opportunities with clear rationale.",
    },
    "deference": {
        "T1": "Proceed decisively with minimal confirmation overhead.",
        "T2": "Ask for confirmation at major branch points only.",
        "T3": "Present options for important decisions before execution.",
        "T4": "Prefer requestor confirmation before committing major choices.",
        "T5": "Defer major decisions and await explicit human confirmation.",
    },
}

STYLE_FRAGMENTS = {
    "communication_depth": {
        "T1": "Keep responses brief and highly compressed.",
        "T2": "Default to concise responses unless detail is requested.",
        "T3": "Balance brevity and depth based on task complexity.",
        "T4": "Include additional context when it improves execution quality.",
        "T5": "Provide full context and rationale unless explicitly constrained.",
    },
    "tone_warmth": {
        "T1": "Maintain neutral, factual language with minimal affect.",
        "T2": "Keep tone professional with limited warmth.",
        "T3": "Use balanced professional warmth.",
        "T4": "Use collaborative, supportive tone while staying precise.",
        "T5": "Use strongly supportive, relationship-forward language.",
    },
    "formality": {
        "T1": "Use informal phrasing when appropriate.",
        "T2": "Keep style mostly conversational and direct.",
        "T3": "Use balanced professional language.",
        "T4": "Prefer formal and structured phrasing.",
        "T5": "Maintain consistently formal style and strict wording.",
    },
    "directness": {
        "T1": "Use exploratory phrasing and soft suggestions.",
        "T2": "Prefer gentle recommendations over directives.",
        "T3": "Balance direct guidance with optionality.",
        "T4": "Provide clear, direct guidance and explicit actions.",
        "T5": "Use highly direct, action-first instructions.",
    },
}


@dataclass
class RoleSpec:
    description: str
    tools: List[str]
    permission_mode: str
    default_max_turns: int
    skills: List[str]
    role_summary: str
    protocol: List[str]
    model: str = "inherit"
    disallowed_tools: List[str] = None  # type: ignore[assignment]
    mcp_servers: List[str] = None  # type: ignore[assignment]
    hooks: List[str] = None  # type: ignore[assignment]
    memory: str = ""


ROLE_SPECS: Dict[str, RoleSpec] = {
    "ai-ops-planner": RoleSpec(
        description=(
            "Analyze scope, governance context, and workbook state. Produce "
            "structured plans and status summaries. Does not write files."
        ),
        tools=["Read", "Grep", "Glob", "LS"],
        permission_mode="plan",
        default_max_turns=15,
        skills=["work", "bootstrap", "work_status"],
        role_summary=(
            "Read governance files and active artifacts, then return actionable "
            "plans and status reports."
        ),
        protocol=[
            "Build scope understanding before planning actions.",
            "State assumptions and unresolved questions explicitly.",
            "Return recommendations with clear next-step options.",
        ],
    ),
    "ai-ops-executor": RoleSpec(
        description=(
            "Implement approved changes, run scripts, and execute workbook tasks "
            "within authority and scope guardrails."
        ),
        tools=["Read", "Grep", "Glob", "LS", "Write", "Edit", "Bash"],
        permission_mode="default",
        default_max_turns=30,
        skills=["work", "scratchpad", "customize"],
        role_summary=(
            "Implement approved tasks, keep edits scoped, and report outcomes with "
            "evidence."
        ),
        protocol=[
            "Follow Pre-Write Authority Guard for every write.",
            "Stop and report blockers instead of widening scope silently.",
            "Keep execution aligned to approved workbook tasks.",
        ],
    ),
    "ai-ops-reviewer": RoleSpec(
        description=(
            "Review quality, correctness, and governance compliance. Produces "
            "findings with evidence and remediation disposition."
        ),
        tools=["Read", "Grep", "Glob", "LS", "Bash"],
        permission_mode="plan",
        default_max_turns=20,
        skills=["crosscheck", "health"],
        role_summary=(
            "Run structured reviews against clarity, thrift, context, and governance."
        ),
        protocol=[
            "Build evidence ledger before writing findings.",
            "Classify finding type and remediation disposition.",
            "Return prioritized findings with concrete file references.",
        ],
    ),
    "ai-ops-researcher": RoleSpec(
        description=(
            "Gather deep codebase and artifact context, synthesize findings, and "
            "surface contradictions or missing evidence."
        ),
        tools=["Read", "Grep", "Glob", "LS", "Bash"],
        permission_mode="plan",
        default_max_turns=25,
        skills=["work"],
        role_summary=(
            "Explore broadly for context synthesis and produce structured factual reports."
        ),
        protocol=[
            "Organize findings by topic, not read order.",
            "Separate facts from inferences.",
            "Cite source artifacts for all critical findings.",
        ],
    ),
    "ai-ops-closer": RoleSpec(
        description=(
            "Finalize work sessions: validate, stage, summarize, and complete closeout "
            "operations within governance gates."
        ),
        tools=["Read", "Grep", "Glob", "LS", "Write", "Edit", "Bash"],
        permission_mode="default",
        default_max_turns=20,
        skills=["closeout", "harvest"],
        role_summary=(
            "Run closeout lane checks and produce clear completion evidence."
        ),
        protocol=[
            "Run configured validators before completion steps.",
            "Stop on blocking failures and report exact error evidence.",
            "Keep closeout reports concise and auditable.",
        ],
    ),
    "ai-ops-linter": RoleSpec(
        description=(
            "Run configured validators and linters, then return structured findings "
            "without applying fixes."
        ),
        tools=["Read", "Grep", "Glob", "LS", "Bash"],
        permission_mode="default",
        default_max_turns=15,
        skills=["lint"],
        role_summary=(
            "Execute mechanical checks and return pass/fail evidence for gate decisions."
        ),
        protocol=[
            "Run repo validators before language-specific linters when available.",
            "Return file paths, line references, and rule identifiers.",
            "Do not apply fixes from this lane.",
        ],
    ),
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_yaml(path: Path) -> Dict:
    if yaml is None:
        raise RuntimeError("PyYAML is required. Install with: pip install pyyaml")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Profile source must be a dictionary: {path}")
    return data


def dump_yaml(data: Dict) -> str:
    if yaml is None:
        raise RuntimeError("PyYAML is required. Install with: pip install pyyaml")
    return yaml.safe_dump(data, sort_keys=False)


def slider_tier(value: int) -> str:
    if value <= 20:
        return "T1"
    if value <= 40:
        return "T2"
    if value <= 60:
        return "T3"
    if value <= 80:
        return "T4"
    return "T5"


def max_turns_from_autonomy(value: int, default_turns: int) -> int:
    tier = slider_tier(value)
    if tier == "T1":
        return 5
    if tier == "T2":
        return 10
    if tier == "T3":
        return max(default_turns, 20)
    if tier == "T4":
        return max(default_turns, 30)
    return 50


def resolve_profile_source(repo_root: Path, profile_arg: str | None) -> Path:
    if profile_arg:
        return Path(profile_arg).resolve()
    per_repo = repo_root / ".ai_ops" / "local" / "profiles" / "active_crew.yaml"
    legacy_per_repo = repo_root / ".ai_ops" / "profiles" / "active_crew.yaml"
    if per_repo.exists():
        return per_repo
    if legacy_per_repo.exists():
        return legacy_per_repo
    return repo_root / "02_Modules" / "01_agent_profiles" / "base" / "default_crew.yaml"


def resolve_model_tuning_source(repo_root: Path, tuning_arg: str | None) -> Path:
    if tuning_arg:
        return Path(tuning_arg).resolve()
    return repo_root / "02_Modules" / "01_agent_profiles" / "base" / "model_tuning_manifest.yaml"


def default_model_tuning_manifest() -> Dict:
    return {
        "schema_version": "0.1.0",
        "default_model_family": "neutral",
        "model_families": {
            "neutral": {
                "status": "active",
                "notes": "Baseline portable prose with no model-specific addendum.",
                "lead_profile_addendum": "",
            },
            "claude": {
                "status": "planned",
                "notes": "Pending empirical validation.",
                "lead_profile_addendum": "",
            },
            "gpt5": {
                "status": "planned",
                "notes": "Pending empirical validation.",
                "lead_profile_addendum": "",
            },
            "gemini": {
                "status": "planned",
                "notes": "Pending empirical validation.",
                "lead_profile_addendum": "",
            },
        },
        "evidence_log": [],
    }


def validate_profile_source(profile: Dict) -> None:
    required_top = {"schema_version", "crew_preset", "lead_agent", "subagents"}
    missing = required_top - set(profile.keys())
    if missing:
        raise ValueError(f"Missing required profile keys: {sorted(missing)}")

    lead_agent = profile.get("lead_agent")
    if not isinstance(lead_agent, dict):
        raise ValueError("profile.lead_agent must be a dictionary")
    if "rider" not in lead_agent or "overrides" not in lead_agent:
        raise ValueError("profile.lead_agent must include rider and overrides")
    lead_rider = lead_agent.get("rider")
    if lead_rider is not None and not isinstance(lead_rider, str):
        raise ValueError("profile.lead_agent.rider must be a string or null")
    lead_overrides = lead_agent.get("overrides")
    if not isinstance(lead_overrides, dict):
        raise ValueError("profile.lead_agent.overrides must be a dictionary")
    if lead_rider is None and lead_overrides:
        raise ValueError("profile.lead_agent.overrides must be empty when lead rider is null")
    if lead_rider and lead_rider not in RIDER_ARCHETYPES:
        raise ValueError(f"Unknown lead rider archetype: {lead_rider}")
    for key, value in lead_overrides.items():
        if key not in SLIDERS:
            raise ValueError(f"Unknown lead slider override '{key}'")
        if not isinstance(value, int):
            raise ValueError(f"Lead slider override '{key}' must be an integer")

    subagents = profile.get("subagents")
    if not isinstance(subagents, dict):
        raise ValueError("profile.subagents must be a dictionary")
    missing_roles = set(ROLE_SPECS.keys()) - set(subagents.keys())
    if missing_roles:
        raise ValueError(f"Missing required subagent slots: {sorted(missing_roles)}")


def validate_model_tuning_manifest(manifest: Dict) -> None:
    required_top = {"schema_version", "default_model_family", "model_families", "evidence_log"}
    missing = required_top - set(manifest.keys())
    if missing:
        raise ValueError(f"Missing required model tuning keys: {sorted(missing)}")

    families = manifest.get("model_families")
    if not isinstance(families, dict) or not families:
        raise ValueError("model_tuning.model_families must be a non-empty dictionary")

    default_family = manifest.get("default_model_family")
    if not isinstance(default_family, str) or default_family not in families:
        raise ValueError("model_tuning.default_model_family must exist in model_families")

    for family, payload in families.items():
        if not isinstance(payload, dict):
            raise ValueError(f"model family '{family}' must be an object")
        status = payload.get("status")
        if status not in {"planned", "active", "deprecated"}:
            raise ValueError(
                f"model family '{family}' has invalid status '{status}' "
                "(expected planned/active/deprecated)"
            )
        addendum = payload.get("lead_profile_addendum", "")
        if not isinstance(addendum, str):
            raise ValueError(
                f"model family '{family}' lead_profile_addendum must be a string"
            )
        notes = payload.get("notes", "")
        if not isinstance(notes, str):
            raise ValueError(f"model family '{family}' notes must be a string")

    evidence_log = manifest.get("evidence_log")
    if not isinstance(evidence_log, list):
        raise ValueError("model_tuning.evidence_log must be a list")


def merge_slider_values(role_name: str, rider: str, overrides: Dict) -> Tuple[Dict[str, int], List[str]]:
    if rider not in RIDER_ARCHETYPES:
        raise ValueError(f"Unknown rider archetype: {rider}")
    sliders = dict(RIDER_ARCHETYPES[rider])
    for key, value in overrides.items():
        if key not in SLIDERS:
            raise ValueError(f"Unknown slider override '{key}' for role {role_name}")
        if not isinstance(value, int):
            raise ValueError(f"Slider override '{key}' for role {role_name} must be an integer")
        sliders[key] = max(0, min(100, value))

    warnings: List[str] = []
    if role_name in WRITE_ROLES and sliders["conservatism"] < 30:
        sliders["conservatism"] = 30
        warnings.append(
            f"{role_name}: conservatism clamped to floor 30 for write-capable role"
        )
    if sliders["deference"] < 40:
        sliders["deference"] = 40
        warnings.append(f"{role_name}: deference clamped to floor 40")
    return sliders, warnings


def build_how_you_work(sliders: Dict[str, int]) -> List[str]:
    lines: List[str] = []
    for slider in PROFESSIONAL_SLIDERS:
        value = sliders[slider]
        tier = slider_tier(value)
        fragment = FRAGMENTS[slider][tier]
        lines.append(f"- `{slider}` {value} ({tier}): {fragment}")
    return lines


def build_communication_style(sliders: Dict[str, int]) -> List[str]:
    lines: List[str] = []
    for slider in COMMUNICATION_SLIDERS:
        value = sliders[slider]
        tier = slider_tier(value)
        fragment = STYLE_FRAGMENTS[slider][tier]
        lines.append(f"- `{slider}` {value} ({tier}): {fragment}")
    return lines


def profile_comment_block(
    role_name: str,
    rider: str,
    crew_preset: str,
    source_hash: str,
    generated_at: str,
    sliders: Dict[str, int],
) -> str:
    lines = [
        "<!--",
        "Managed by ai_ops /profiles",
        f"generated_at: {generated_at}",
        f"source_hash: {source_hash}",
        f"role: {role_name}",
        f"profile_id: {rider}",
        f"crew_preset: {crew_preset}",
        "sliders:",
    ]
    for slider in SLIDERS:
        lines.append(f"  - {slider}: {sliders[slider]} ({slider_tier(sliders[slider])})")
    lines.append("-->")
    return "\n".join(lines)


def render_agent_file(
    role_name: str,
    spec: RoleSpec,
    rider: str,
    crew_preset: str,
    source_hash: str,
    generated_at: str,
    sliders: Dict[str, int],
) -> str:
    max_turns = max_turns_from_autonomy(sliders["autonomy"], spec.default_max_turns)
    title = role_name
    how_you_work_lines = build_how_you_work(sliders)
    protocol_lines = "\n".join([f"- {line}" for line in spec.protocol])
    skills_lines = "\n".join([f"  - {item}" for item in spec.skills])
    tools_lines = "\n".join([f"  - {tool}" for tool in spec.tools])
    metadata_block = profile_comment_block(
        role_name=role_name,
        rider=rider,
        crew_preset=crew_preset,
        source_hash=source_hash,
        generated_at=generated_at,
        sliders=sliders,
    )
    body_lines = "\n".join(how_you_work_lines)

    # Build optional field lines
    model_line = f"model: {spec.model}" if spec.model else "model: inherit"
    if spec.disallowed_tools:
        disallowed_lines = "\n".join(
            [f"  - {t}" for t in spec.disallowed_tools]
        )
        disallowed_block = f"disallowedTools:\n{disallowed_lines}"
    else:
        disallowed_block = "disallowedTools: null"
    if spec.mcp_servers:
        mcp_lines = "\n".join([f"  - {s}" for s in spec.mcp_servers])
        mcp_block = f"mcpServers:\n{mcp_lines}"
    else:
        mcp_block = "mcpServers: null"
    hooks_block = "hooks: null"
    if spec.hooks:
        hooks_lines = "\n".join([f"  - {h}" for h in spec.hooks])
        hooks_block = f"hooks:\n{hooks_lines}"
    memory_block = f"memory: {spec.memory}" if spec.memory else "memory: null"

    return f"""---
name: {role_name}
description: >-
  {spec.description}
tools:
{tools_lines}
{disallowed_block}
{model_line}
permissionMode: {spec.permission_mode}
maxTurns: {max_turns}
skills:
{skills_lines}
{mcp_block}
{hooks_block}
{memory_block}
---

<!-- markdownlint-disable MD013 -->
# {title}

You are the {role_name} subagent for ai_ops governance.

## Role

{spec.role_summary}

## Operating Protocol

{protocol_lines}

## How You Work

{body_lines}

## How You Report to the Lead Agent

- Return a structured summary with outcomes, evidence, and blockers.
- Include concrete file paths and line references for findings.
- Distinguish observed facts from inferred recommendations.

## Safety and Trust (Invariant)

- Follow governance authority gates before any write.
- Keep scope bounded to approved task contracts.
- Escalate blockers instead of bypassing controls.

<!-- Managed by ai_ops /profiles -->
{metadata_block}
"""


def render_single_agent_profile_map(
    generated_at: str,
    source_hash: str,
    crew_preset: str,
    rows: List[Dict[str, str]],
    warnings: List[str],
) -> str:
    generated_date = generated_at.split("T", 1)[0]
    warning_block = "\n".join([f"- {item}" for item in warnings]) if warnings else "- none"
    row_lines = "\n".join(
        [
            (
                f"| `{row['role']}` | `{row['rider']}` | {row['autonomy']} | "
                f"{row['conservatism']} | {row['initiative']} | {row['deference']} | "
                f"{row['max_turns']} | `{row['permission_mode']}` |"
            )
            for row in rows
        ]
    )
    return f"""---
title: Single-Agent Profile Map
version: 0.1.0
status: active
last_updated: {generated_date}
owner: ai_ops
generated_at: {generated_at}
source_hash: {source_hash}
---

<!-- markdownlint-disable MD013 MD025 -->
# Single-Agent Profile Map

This file is generated by `00_Admin/scripts/regenerate_profiles.py` from the
active crew profile source. It is intended for single-agent environments where
subagent delegation is not available.

## Source Summary

- crew_preset: `{crew_preset}`
- generated_at: `{generated_at}`
- source_hash: `{source_hash}`

## Functional Role Mapping

| Role | Rider | Autonomy | Conservatism | Initiative | Deference | maxTurns | permissionMode |
| --- | --- | --- | --- | --- | --- | --- | --- |
{row_lines}

## Safety Clamp Warnings

{warning_block}
"""


def render_lead_agent_profile_context(
    generated_at: str,
    source_hash: str,
    crew_preset: str,
    lead_rider: str | None,
    lead_sliders: Dict[str, int] | None,
    model_family: str,
    model_status: str,
    model_notes: str,
    model_addendum: str,
    warnings: List[str],
) -> str:
    generated_date = generated_at.split("T", 1)[0]
    warning_block = "\n".join([f"- {item}" for item in warnings]) if warnings else "- none"

    if lead_rider is None or lead_sliders is None:
        lead_state = "\n".join(
            [
                "- status: `default`",
                "- rider: `none`",
                "- behavior: native lead-agent behavior with ai_ops governance only",
            ]
        )
        communication_lines = "- not applicable"
        professional_lines = "- not applicable"
    else:
        lead_state = "\n".join(
            [
                "- status: `profiled`",
                f"- rider: `{lead_rider}`",
                "- delivery: adapter-managed secondary context (not root `AGENTS.md`/`GEMINI.md`)",
            ]
        )
        communication_lines = "\n".join(build_communication_style(lead_sliders))
        professional_lines = "\n".join(build_how_you_work(lead_sliders))

    addendum_block = model_addendum if model_addendum.strip() else "- none"

    return f"""---
title: Lead Agent Profile Context
version: 0.1.0
status: active
last_updated: {generated_date}
owner: ai_ops
generated_at: {generated_at}
source_hash: {source_hash}
---

<!-- markdownlint-disable MD013 MD025 -->
# Lead Agent Profile Context

Generated by `00_Admin/scripts/regenerate_profiles.py` from profile source
data. This file is the adapter-managed lead-profile payload and must not be
copied into root `AGENTS.md` or `GEMINI.md`.

## Source Summary

- crew_preset: `{crew_preset}`
- generated_at: `{generated_at}`
- source_hash: `{source_hash}`

## Lead Profile State

{lead_state}

## Lead Communication Style

{communication_lines}

## Lead Professional Operating Style

{professional_lines}

## Model Family Calibration

- active_model_family: `{model_family}`
- calibration_status: `{model_status}`
- calibration_notes: {model_notes}

### Model-Specific Addendum

{addendum_block}

## Safety Clamp Warnings

{warning_block}
"""


def render_model_tuning_summary(
    generated_at: str,
    source_hash: str,
    manifest_path: str,
    model_family: str,
    model_manifest: Dict,
) -> str:
    generated_date = generated_at.split("T", 1)[0]
    families = model_manifest["model_families"]
    evidence_count = len(model_manifest.get("evidence_log", []))
    rows = []
    for family_name, payload in families.items():
        notes = str(payload.get("notes", "")).strip() or "none"
        status = str(payload.get("status", "planned"))
        addendum = str(payload.get("lead_profile_addendum", "")).strip()
        addendum_state = "yes" if addendum else "no"
        rows.append(
            f"| `{family_name}` | `{status}` | `{addendum_state}` | {notes} |"
        )
    table_rows = "\n".join(rows)

    return f"""---
title: Model Tuning Summary
version: 0.1.0
status: active
last_updated: {generated_date}
owner: ai_ops
generated_at: {generated_at}
source_hash: {source_hash}
---

<!-- markdownlint-disable MD013 MD025 -->
# Model Tuning Summary

Generated by `00_Admin/scripts/regenerate_profiles.py`.

## Source

- manifest_path: `{manifest_path}`
- generated_at: `{generated_at}`
- active_model_family: `{model_family}`
- evidence_log_entries: `{evidence_count}`

## Registered Model Families

| Model family | Status | Lead addendum present | Notes |
| --- | --- | --- | --- |
{table_rows}

## Usage Notes

- Model family entries marked `planned` are placeholders until validated.
- Keep canonical behavior portable; add model-specific prose only with evidence.
- Lead profile delivery remains adapter-managed and out of root `AGENTS.md`/`GEMINI.md`.
"""


def write_text(path: Path, content: str, dry_run: bool = False) -> None:
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Regenerate ai_ops profile-derived behavior files."
    )
    parser.add_argument(
        "--profile",
        help="Optional path to profile source YAML. Defaults to active profile then factory default.",
    )
    parser.add_argument(
        "--model-family",
        help=(
            "Optional model family key from model_tuning_manifest.yaml. "
            "Defaults to manifest default_model_family."
        ),
    )
    parser.add_argument(
        "--model-tuning",
        help=(
            "Optional path to model tuning manifest YAML. "
            "Defaults to 02_Modules/01_agent_profiles/base/model_tuning_manifest.yaml."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and render outputs without writing files.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    profile_path = resolve_profile_source(repo_root, args.profile)
    model_tuning_path = resolve_model_tuning_source(repo_root, args.model_tuning)
    if not profile_path.exists():
        print(f"[FAIL] Profile source file not found: {profile_path}")
        return 1

    agents_dir = repo_root / "plugins" / "ai-ops-governance" / "agents"
    if not agents_dir.exists():
        print(f"[FAIL] Output directory missing: {agents_dir}")
        print("Run setup to create plugin skeleton before regeneration.")
        return 1

    try:
        profile = load_yaml(profile_path)
        validate_profile_source(profile)
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] Could not load profile source: {exc}")
        return 1

    model_manifest_warning: str | None = None
    if model_tuning_path.exists():
        try:
            model_manifest = load_yaml(model_tuning_path)
            validate_model_tuning_manifest(model_manifest)
        except Exception as exc:  # noqa: BLE001
            print(f"[FAIL] Could not load model tuning manifest: {exc}")
            return 1
    else:
        model_manifest = default_model_tuning_manifest()
        model_manifest_warning = (
            "model_tuning_manifest.yaml not found; using built-in neutral defaults"
        )

    generated_at = now_iso()
    profile["generated_at"] = generated_at
    source_hash = hashlib.sha256(
        json.dumps(profile, sort_keys=True).encode("utf-8")
    ).hexdigest()[:12]

    crew_preset = str(profile.get("crew_preset", "custom"))
    model_families = model_manifest["model_families"]
    selected_model_family = args.model_family or str(
        model_manifest["default_model_family"]
    )
    if selected_model_family not in model_families:
        print(
            "[FAIL] Unknown model family "
            f"'{selected_model_family}'. Available: {sorted(model_families.keys())}"
        )
        return 1
    model_payload = model_families[selected_model_family]
    model_status = str(model_payload.get("status", "planned"))
    model_notes = str(model_payload.get("notes", "none"))
    model_addendum = str(model_payload.get("lead_profile_addendum", ""))

    warnings: List[str] = []
    if model_manifest_warning:
        warnings.append(model_manifest_warning)
    map_rows: List[Dict[str, str]] = []
    written_files: List[Path] = []

    for role_name, spec in ROLE_SPECS.items():
        slot_data = profile["subagents"].get(role_name, {})
        rider = slot_data.get("rider")
        if not rider:
            print(f"[FAIL] Missing rider for slot: {role_name}")
            return 1
        overrides = slot_data.get("overrides", {})
        if not isinstance(overrides, dict):
            print(f"[FAIL] overrides for {role_name} must be an object")
            return 1

        try:
            sliders, slot_warnings = merge_slider_values(role_name, rider, overrides)
        except Exception as exc:  # noqa: BLE001
            print(f"[FAIL] {exc}")
            return 1

        warnings.extend(slot_warnings)
        rendered = render_agent_file(
            role_name=role_name,
            spec=spec,
            rider=rider,
            crew_preset=crew_preset,
            source_hash=source_hash,
            generated_at=generated_at,
            sliders=sliders,
        )
        target = agents_dir / f"{role_name}.md"
        write_text(target, rendered, dry_run=args.dry_run)
        written_files.append(target)

        map_rows.append(
            {
                "role": role_name,
                "rider": rider,
                "autonomy": str(sliders["autonomy"]),
                "conservatism": str(sliders["conservatism"]),
                "initiative": str(sliders["initiative"]),
                "deference": str(sliders["deference"]),
                "max_turns": str(
                    max_turns_from_autonomy(sliders["autonomy"], spec.default_max_turns)
                ),
                "permission_mode": spec.permission_mode,
            }
        )

    generated_root = repo_root / "02_Modules" / "01_agent_profiles" / "generated"
    map_path = generated_root / "single_agent_profile_map.md"
    map_content = render_single_agent_profile_map(
        generated_at=generated_at,
        source_hash=source_hash,
        crew_preset=crew_preset,
        rows=map_rows,
        warnings=warnings,
    )
    write_text(map_path, map_content, dry_run=args.dry_run)
    written_files.append(map_path)

    lead_data = profile["lead_agent"]
    lead_rider = lead_data.get("rider")
    lead_overrides = lead_data.get("overrides", {})
    lead_sliders: Dict[str, int] | None = None
    if lead_rider:
        try:
            lead_sliders, lead_warnings = merge_slider_values(
                role_name="lead-agent",
                rider=lead_rider,
                overrides=lead_overrides,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[FAIL] {exc}")
            return 1
        warnings.extend(lead_warnings)

    lead_context_path = generated_root / "lead_agent_profile_context.md"
    lead_context_content = render_lead_agent_profile_context(
        generated_at=generated_at,
        source_hash=source_hash,
        crew_preset=crew_preset,
        lead_rider=lead_rider,
        lead_sliders=lead_sliders,
        model_family=selected_model_family,
        model_status=model_status,
        model_notes=model_notes,
        model_addendum=model_addendum,
        warnings=warnings,
    )
    write_text(lead_context_path, lead_context_content, dry_run=args.dry_run)
    written_files.append(lead_context_path)

    model_summary_path = generated_root / "model_tuning_summary.md"
    model_summary_content = render_model_tuning_summary(
        generated_at=generated_at,
        source_hash=source_hash,
        manifest_path=model_tuning_path.relative_to(repo_root).as_posix(),
        model_family=selected_model_family,
        model_manifest=model_manifest,
    )
    write_text(model_summary_path, model_summary_content, dry_run=args.dry_run)
    written_files.append(model_summary_path)

    print("[OK] Profile regeneration completed.")
    print(f"Source: {profile_path}")
    print(f"Model family: {selected_model_family} (status: {model_status})")
    print(f"Model tuning source: {model_tuning_path}")
    print(f"Source hash: {source_hash}")
    if args.dry_run:
        print("Files validated (dry-run, no writes):")
    else:
        print("Files written:")
    for path in written_files:
        print(f"- {path.relative_to(repo_root)}")
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")
    else:
        print("Warnings: none")
    return 0


if __name__ == "__main__":
    sys.exit(main())
