#!/usr/bin/env python
"""
C33 validator: detect CLI contract drift between workbook command fences and
Python argparse definitions.

The validator scans fenced code blocks in workbook markdown files, extracts
`python <script>.py ...` command lines, and checks long flags (`--flag`) used in
those commands against flags declared via `add_argument("--flag", ...)` in the
target script.

Current scope limitations (intentional C33 MVP behavior):
- Does not evaluate `python -c ...` inline commands.
- Does not evaluate `python -m ...` module execution.
- CWD tracking only supports literal-path location commands (`Push-Location`,
  `Pop-Location`, `Set-Location`, `cd`, `chdir`, `pushd`, `popd`, `sl`).
  Dynamic path expressions (for example variables) are not resolved.
"""

from __future__ import annotations

import argparse
import ast
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Set, Tuple


@dataclass
class CommandRef:
    workbook: Path
    line_no: int
    raw: str
    script_token: str
    flags: List[str]
    execution_root: Path
    command_cwd: Path


def parse_front_matter_execution_root(text: str, repo_root: Path) -> Path:
    if not text.startswith("---"):
        return repo_root
    lines = text.splitlines()
    end_idx = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_idx = idx
            break
    if end_idx is None:
        return repo_root

    for line in lines[1:end_idx]:
        stripped = line.strip()
        if not stripped.startswith("execution_root:"):
            continue
        value = stripped.split(":", 1)[1].strip()
        if not value:
            return repo_root
        # Handle comments and quoted scalar values.
        value = value.split("#", 1)[0].strip().strip('"').strip("'")
        if not value:
            return repo_root
        return (repo_root / value).resolve()
    return repo_root


def iter_fenced_blocks(text: str) -> Iterable[Tuple[int, List[str]]]:
    in_fence = False
    block_start = 0
    block_lines: List[str] = []
    for idx, line in enumerate(text.splitlines(), start=1):
        if line.strip().startswith("```"):
            if in_fence:
                yield block_start, block_lines
                block_lines = []
                in_fence = False
            else:
                in_fence = True
                block_start = idx + 1
            continue
        if in_fence:
            block_lines.append(line)


def fold_continuations(lines: Sequence[str], start_line: int) -> Iterable[Tuple[int, str]]:
    active_line = None
    parts: List[str] = []
    for offset, raw in enumerate(lines):
        line_no = start_line + offset
        stripped = raw.rstrip()
        if not stripped:
            if parts:
                yield active_line if active_line is not None else line_no, " ".join(parts).strip()
                parts = []
                active_line = None
            continue
        if active_line is None:
            active_line = line_no
        continuation = stripped.endswith("`") or stripped.endswith("\\")
        if continuation:
            stripped = stripped[:-1].rstrip()
        parts.append(stripped)
        if not continuation:
            yield active_line, " ".join(parts).strip()
            parts = []
            active_line = None
    if parts:
        yield active_line if active_line is not None else start_line, " ".join(parts).strip()


def tokenize_command(command: str) -> List[str]:
    try:
        return shlex.split(command, posix=False)
    except ValueError:
        return command.split()


def normalize_flag(token: str) -> str | None:
    if not token.startswith("--") or token == "--":
        return None
    if "=" in token:
        token = token.split("=", 1)[0]
    return token


def split_command_segments(command: str) -> List[str]:
    # Keep parsing simple: split on unquoted semicolons for chained commands.
    parts: List[str] = []
    current: List[str] = []
    quote: str | None = None
    for char in command:
        if quote is not None:
            current.append(char)
            if char == quote:
                quote = None
            continue
        if char in {"'", '"'}:
            quote = char
            current.append(char)
            continue
        if char == ";":
            segment = "".join(current).strip()
            if segment:
                parts.append(segment)
            current = []
            continue
        current.append(char)
    tail = "".join(current).strip()
    if tail:
        parts.append(tail)
    return parts


def extract_location_target(tokens: Sequence[str]) -> str | None:
    if len(tokens) < 2:
        return None
    idx = 1
    while idx < len(tokens):
        token = tokens[idx]
        lower = token.lower()
        if lower in {"-path", "-literalpath"} and idx + 1 < len(tokens):
            return tokens[idx + 1]
        if token.startswith("-"):
            idx += 1
            continue
        return token
    return None


def resolve_location_target(token: str, current_cwd: Path) -> Path | None:
    cleaned = token.strip().strip('"').strip("'")
    if not cleaned or cleaned.startswith("$"):
        return None
    target = Path(cleaned)
    if target.is_absolute():
        return target.resolve()
    return (current_cwd / target).resolve()


def apply_location_command(tokens: Sequence[str], cwd_stack: List[Path]) -> bool:
    command = tokens[0].lower()
    if command in {"pop-location", "popd"}:
        if len(cwd_stack) > 1:
            cwd_stack.pop()
        return True

    if command in {"push-location", "pushd", "set-location", "cd", "chdir", "sl"}:
        target = extract_location_target(tokens)
        if target is None:
            return True
        resolved = resolve_location_target(target, cwd_stack[-1])
        if resolved is None:
            return True
        if command in {"push-location", "pushd"}:
            cwd_stack.append(resolved)
        else:
            cwd_stack[-1] = resolved
        return True
    return False


def extract_python_commands(workbook: Path, repo_root: Path) -> List[CommandRef]:
    text = workbook.read_text(encoding="utf-8")
    execution_root = parse_front_matter_execution_root(text, repo_root)
    refs: List[CommandRef] = []

    for block_start, block_lines in iter_fenced_blocks(text):
        cwd_stack: List[Path] = [execution_root]
        for line_no, command in fold_continuations(block_lines, block_start):
            stripped = command.strip()
            if not stripped or stripped.startswith("#"):
                continue
            for segment in split_command_segments(stripped):
                tokens = tokenize_command(segment)
                if not tokens:
                    continue

                if apply_location_command(tokens, cwd_stack):
                    continue

                if tokens[0].lower() not in {"python", "python3", "py"}:
                    continue
                if len(tokens) < 2:
                    continue
                script_idx = 1
                if tokens[1] == "-m":
                    # Module execution isn't validated by this C33 MVP.
                    continue
                script_token = tokens[script_idx]
                if not script_token.lower().endswith(".py"):
                    continue

                flags: List[str] = []
                for token in tokens[script_idx + 1 :]:
                    normalized = normalize_flag(token)
                    if normalized:
                        flags.append(normalized)

                refs.append(
                    CommandRef(
                        workbook=workbook,
                        line_no=line_no,
                        raw=segment,
                        script_token=script_token,
                        flags=flags,
                        execution_root=execution_root,
                        command_cwd=cwd_stack[-1],
                    )
                )
    return refs


def resolve_script_path(ref: CommandRef, repo_root: Path) -> Path | None:
    token_path = Path(ref.script_token)
    candidates: List[Path] = []
    if token_path.is_absolute():
        candidates.append(token_path)
    else:
        candidates.extend(
            [
                (ref.command_cwd / token_path).resolve(),
                (ref.execution_root / token_path).resolve(),
                (ref.workbook.parent / token_path).resolve(),
                (repo_root / token_path).resolve(),
            ]
        )
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def extract_argparse_flags(script_path: Path) -> Set[str]:
    text = script_path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(script_path))
    flags: Set[str] = {"--help"}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        func_name = None
        if isinstance(func, ast.Attribute):
            func_name = func.attr
        elif isinstance(func, ast.Name):
            func_name = func.id
        if func_name != "add_argument":
            continue
        for arg in node.args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                value = arg.value
                if value.startswith("--"):
                    flags.add(value)
    return flags


def classify_unknown_flags(command_flags: Sequence[str], valid_flags: Set[str]) -> List[str]:
    unknown = []
    for flag in command_flags:
        if flag not in valid_flags:
            unknown.append(flag)
    return unknown


def run_validator(
    workbooks: Sequence[Path],
    repo_root: Path,
    missing_script_mode: str,
    parse_failure_mode: str,
) -> int:
    errors: List[str] = []
    warnings: List[str] = []
    checked_commands = 0

    for workbook in workbooks:
        refs = extract_python_commands(workbook, repo_root)
        for ref in refs:
            script_path = resolve_script_path(ref, repo_root)
            if script_path is None:
                msg = (
                    f"C33 {'ERROR' if missing_script_mode == 'error' else 'WARN'}: "
                    f"{ref.workbook}:{ref.line_no} cannot resolve script '{ref.script_token}'"
                )
                (errors if missing_script_mode == "error" else warnings).append(msg)
                continue

            try:
                valid_flags = extract_argparse_flags(script_path)
            except Exception as exc:  # noqa: BLE001
                msg = (
                    f"C33 {'ERROR' if parse_failure_mode == 'error' else 'WARN'}: "
                    f"{ref.workbook}:{ref.line_no} failed to parse '{script_path}': {exc}"
                )
                (errors if parse_failure_mode == "error" else warnings).append(msg)
                continue

            unknown = classify_unknown_flags(ref.flags, valid_flags)
            if unknown:
                errors.append(
                    "C33 ERROR: "
                    f"{ref.workbook}:{ref.line_no} unknown flag(s) {unknown} "
                    f"for script {script_path}"
                )
            checked_commands += 1

    for message in warnings:
        print(message)
    for message in errors:
        print(message)

    print(
        "C33 SUMMARY: "
        f"workbooks={len(workbooks)} checked_commands={checked_commands} "
        f"warnings={len(warnings)} errors={len(errors)}"
    )
    return 1 if errors else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate workbook Python CLI flags against argparse declarations."
    )
    parser.add_argument(
        "--workbook",
        action="append",
        required=True,
        help="Workbook markdown path. Repeat for multiple files.",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root used to resolve relative paths (default: current directory).",
    )
    parser.add_argument(
        "--missing-script",
        choices=["warning", "error"],
        default="warning",
        help="How to treat unresolved script paths (default: warning).",
    )
    parser.add_argument(
        "--parse-failure",
        choices=["warning", "error"],
        default="warning",
        help="How to treat Python parse failures for target scripts (default: warning).",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    repo_root = Path(args.repo_root).resolve()
    workbooks = [Path(path).resolve() for path in args.workbook]
    return run_validator(
        workbooks=workbooks,
        repo_root=repo_root,
        missing_script_mode=args.missing_script,
        parse_failure_mode=args.parse_failure,
    )


if __name__ == "__main__":
    raise SystemExit(main())
