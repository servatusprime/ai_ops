#!/usr/bin/env python
"""Validate a closeout security receipt against repository bytes.

The validator is intentionally stricter than the pre-pass.  In gate mode it
requires complete full-file coverage, checks staged blobs, enforces the T2
floor, and rejects development-only worktree receipts.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
from pathlib import Path
from typing import Any, NoReturn

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment diagnostic
    raise SystemExit("PyYAML is required; install it before running the validator") from exc


ROOT = Path(__file__).resolve().parents[2]
MIN_FORCED_T2_PREFIXES = (
    ".ai_ops/workflows/",
    "00_Admin/configs/",
    "00_Admin/policies/",
    "00_Admin/specs/",
    "01_Resources/templates/config/",
)
MIN_FORCED_T2_FILES = (
    "AGENTS.md",
    "CLAUDE.md",
    ".pre-commit-config.yaml",
    "SECURITY.md",
    "00_Admin/scripts/closeout_security_prepass.py",
    "00_Admin/scripts/validate_closeout_security_receipt.py",
    "00_Admin/scripts/check_outside_writes.py",
    "00_Admin/scripts/hooks/guard_workspace_writes.py",
    "00_Admin/scripts/hooks/validate_closeout_security_head.py",
)


def fail(message: str) -> "NoReturn":
    raise SystemExit(f"closeout-security-validator: {message}")


def git_bytes(repo: Path, spec: str) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(repo), "show", spec],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode:
        fail(f"cannot read {spec}: {completed.stderr.decode(errors='replace').strip()}")
    return completed.stdout


def git_head(repo: Path) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode:
        fail(completed.stderr.strip())
    return completed.stdout.strip()


def head_path_exists(repo: Path, path: str) -> bool:
    completed = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "-e", f"HEAD:{path}"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.returncode == 0


def safe_path(value: str) -> str:
    path = value.replace("\\", "/").strip()
    while path.startswith("./"):
        path = path[2:]
    candidate = Path(path)
    if not path or path.startswith("/") or re.match(r"^[A-Za-z]:", path) or ".." in candidate.parts:
        fail(f"unsafe receipt path: {value!r}")
    return path


def include_hash(paths: list[str]) -> str:
    return hashlib.sha256("\n".join(sorted(paths)).encode("utf-8")).hexdigest()


def staged_records(repo: Path) -> dict[str, str]:
    completed = subprocess.run(
        ["git", "-C", str(repo), "diff", "--cached", "--name-status", "--no-renames", "--diff-filter=ACDMRTUXB"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode:
        fail(f"cannot inspect staged paths: {completed.stderr.strip()}")
    records: dict[str, str] = {}
    for line in completed.stdout.splitlines():
        status, _, path = line.partition("\t")
        if status and path:
            records[safe_path(path)] = status[0]
    return records


def validate_shape(receipt: dict[str, Any]) -> None:
    required = {
        "receipt_version", "repo_root", "base_head", "source", "include_set_sha256",
        "tiers_config_version", "ruleset_version", "estimated_tokens_total",
        "packet_files", "packet_estimated_tokens", "packet_sha256", "rows",
    }
    missing = sorted(required - set(receipt))
    if missing:
        fail(f"receipt missing fields: {', '.join(missing)}")
    top_allowed = required | {"receipt_sha256"}
    unknown_top = sorted(set(receipt) - top_allowed)
    if unknown_top:
        fail(f"receipt has unknown fields: {', '.join(unknown_top)}")
    if receipt.get("source") not in {"head", "staged", "worktree"}:
        fail("receipt source is invalid")
    if not isinstance(receipt.get("estimated_tokens_total"), int) or receipt["estimated_tokens_total"] < 0:
        fail("estimated_tokens_total must be a non-negative integer")
    if not all(
        isinstance(receipt.get(key), list)
        for key in ("packet_files", "packet_estimated_tokens", "packet_sha256")
    ):
        fail("packet files, token counts, and digests must be lists")
    if len(receipt["packet_files"]) != len(receipt["packet_estimated_tokens"]) or (
        len(receipt["packet_files"]) != len(receipt["packet_sha256"])
    ):
        fail("packet file, token-count, and digest lists must have equal length")
    if not all(isinstance(value, str) and value for value in receipt["packet_files"]):
        fail("packet_files must contain non-empty strings")
    if not receipt["packet_files"] or not all(
        re.fullmatch(r"[0-9a-f]{64}", str(value)) for value in receipt["packet_sha256"]
    ):
        fail("packet_sha256 must contain one lowercase digest per packet")
    if not isinstance(receipt.get("rows"), list) or not receipt["rows"]:
        fail("receipt rows must be a non-empty list")
    row_allowed = {
        "path", "sha256", "revision_basis", "file_kind", "tier", "coverage",
        "prepass_status", "reviewer", "reviewer_model", "reviewer_runtime",
        "review_method", "independent_pass", "chunk_count", "disposition",
        "finding_refs", "coverage_notes",
    }
    for row in receipt["rows"]:
        if not isinstance(row, dict):
            fail("receipt row must be a mapping")
        unknown = sorted(set(row) - row_allowed)
        if unknown:
            fail(f"receipt row has unknown fields: {', '.join(unknown)}")
        for key in (
            "path",
            "sha256",
            "revision_basis",
            "reviewer",
            "reviewer_model",
            "reviewer_runtime",
            "review_method",
        ):
            if not isinstance(row.get(key), str) or not row[key]:
                fail(f"receipt row field {key} is required")
        if row.get("file_kind") not in {"text", "binary", "generated", "deleted", "unsupported"}:
            fail(f"unsupported file_kind in receipt row: {row.get('path')}")
        if row.get("tier") not in {"T0", "T1", "T2"}:
            fail(f"invalid tier in receipt row: {row.get('path')}")
        if row.get("coverage") not in {"fully_reviewed", "partially_reviewed", "unsupported", "not_reviewed"}:
            fail(f"invalid coverage in receipt row: {row.get('path')}")
        if row.get("disposition") not in {"pass", "needs_work", "escalate", "pending"}:
            fail(f"invalid disposition in receipt row: {row.get('path')}")
        if (
            not isinstance(row.get("independent_pass"), bool)
            or not isinstance(row.get("chunk_count"), int)
            or row["chunk_count"] < 1
        ):
            fail(f"review attestation fields are invalid: {row.get('path')}")


def load_config(repo: Path, config_path: Path | None) -> dict[str, Any]:
    target = config_path or (repo / "00_Admin/configs/closeout_security_tiers.yaml")
    if target.exists():
        return yaml.safe_load(target.read_text(encoding="utf-8")) or {}
    raw = git_bytes(repo, "HEAD:00_Admin/configs/closeout_security_tiers.yaml")
    return yaml.safe_load(raw.decode("utf-8")) or {}


def load_staged_config(repo: Path, config_path: Path) -> dict[str, Any]:
    try:
        relative = config_path.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        fail("first-landing policy must be inside the repository")
    if relative != "00_Admin/configs/closeout_security_tiers.yaml":
        fail("first-landing policy must be the canonical closeout security policy")
    raw = git_bytes(repo, f":{relative}")
    return yaml.safe_load(raw.decode("utf-8")) or {}


def load_head_config(repo: Path) -> dict[str, Any]:
    raw = git_bytes(repo, "HEAD:00_Admin/configs/closeout_security_tiers.yaml")
    return yaml.safe_load(raw.decode("utf-8")) or {}


def forced_t2(path: str, config: dict[str, Any]) -> bool:
    files = set(config.get("forced_t2_files", [])) | set(MIN_FORCED_T2_FILES)
    prefixes = tuple(config.get("forced_t2_prefixes", [])) + MIN_FORCED_T2_PREFIXES
    return path in files or any(path.startswith(prefix) for prefix in prefixes)


def source_bytes(repo: Path, path: str, source: str, file_kind: str) -> tuple[bytes, str]:
    if file_kind == "deleted":
        return git_bytes(repo, f"HEAD:{path}"), f"HEAD:{path}"
    if source == "head":
        return git_bytes(repo, f"HEAD:{path}"), f"HEAD:{path}"
    if source == "staged":
        return git_bytes(repo, f":{path}"), f":{path}"
    target = (repo / Path(path)).resolve()
    try:
        target.relative_to(repo.resolve())
    except ValueError:
        fail(f"worktree path escapes repository: {path}")
    return target.read_bytes(), f"worktree:{path}"


def parse_packet_sections(data: bytes) -> list[dict[str, Any]]:
    text = data.decode("utf-8")
    headers = list(re.finditer(r"(?m)^## `([^`]+)`\n", text))
    sections: list[dict[str, Any]] = []
    for index, header in enumerate(headers):
        section = text[header.start() : headers[index + 1].start() if index + 1 < len(headers) else len(text)]
        sha_match = re.search(r"(?m)^- sha256: `([0-9a-f]{64})`$", section)
        chunk_match = re.search(r"(?m)^chunk: (\d+)/(\d+)$", section)
        content_sha_match = re.search(r"(?m)^content_sha256: `([0-9a-f]{64})`$", section)
        bytes_match = re.search(r"(?m)^content_bytes: (\d+)$", section)
        chars_match = re.search(r"(?m)^content_chars: (\d+)$", section)
        if not all((sha_match, chunk_match, content_sha_match, bytes_match, chars_match)):
            fail(f"reviewer packet section is missing binding metadata: {header.group(1)}")
        chars = int(chars_match.group(1))
        marker = "```text\n"
        marker_pos = section.find(marker)
        payload: str | None = None
        if marker_pos >= 0:
            start = marker_pos + len(marker)
            payload = section[start : start + chars]
            if len(payload) != chars or not section[start + chars :].startswith("\n```"):
                fail(f"reviewer packet content length is invalid: {header.group(1)}")
        elif chars:
            fail(f"reviewer packet omits content for {header.group(1)}")
        sections.append(
            {
                "path": safe_path(header.group(1)),
                "sha256": sha_match.group(1),
                "chunk": int(chunk_match.group(1)),
                "chunk_count": int(chunk_match.group(2)),
                "content_sha256": content_sha_match.group(1),
                "content_bytes": int(bytes_match.group(1)),
                "content_chars": chars,
                "content": payload,
            }
        )
    if not sections:
        fail("reviewer packet contains no file sections")
    return sections


def canonical_receipt(receipt: dict[str, Any]) -> bytes:
    copy = dict(receipt)
    copy.pop("receipt_sha256", None)
    return yaml.safe_dump(copy, sort_keys=True).encode("utf-8")


def check_trailer(trailer: str, disposition: str, include_digest: str, receipt_digest: str) -> None:
    match = re.fullmatch(r"Closeout-Security:\s+(\S+)\s+(\S+)\s+(\S+)", trailer.strip())
    if not match:
        fail("trailer format is invalid; expected Closeout-Security: <disposition> <include-set-hash> <receipt-digest>")
    if match.group(1) != disposition or match.group(2) != include_digest or match.group(3) != receipt_digest:
        fail("trailer does not match the validated receipt")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--gate", action="store_true", help="apply real closeout admission rules")
    parser.add_argument("--staged", action="store_true", help="validate against staged blobs")
    parser.add_argument(
        "--first-landing",
        action="store_true",
        help="allow the explicit staged policy for the first landing only",
    )
    parser.add_argument("--trailer")
    parser.add_argument("--commit-msg-file", type=Path)
    parser.add_argument("--discard", action="store_true", help="discard the supplied machine-local receipt")
    args = parser.parse_args()
    if args.commit_msg_file:
        try:
            lines = args.commit_msg_file.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            fail(f"cannot read commit message file: {exc}")
        trailers = [line.strip() for line in lines if line.strip().startswith("Closeout-Security:")]
        if len(trailers) != 1:
            fail("commit message must contain exactly one Closeout-Security trailer")
        args.trailer = trailers[0]
    if args.discard:
        receipt_path = args.receipt.resolve()
        if receipt_path == (args.repo_root.resolve() / ".ai_ops/local/closeout_security/latest.yaml"):
            receipt_path.unlink(missing_ok=True)
            print("DISCARDED closeout security receipt")
            return 0
        fail("--discard is limited to .ai_ops/local/closeout_security/latest.yaml")
    try:
        receipt = yaml.safe_load(args.receipt.read_text(encoding="utf-8")) or {}
    except OSError as exc:
        fail(f"cannot read receipt: {exc}")
    if not isinstance(receipt, dict):
        fail("receipt root must be a mapping")
    if receipt.get("receipt_version") != "0.1.0":
        fail("unsupported receipt_version")
    validate_shape(receipt)
    repo = args.repo_root.resolve()
    if args.gate and not args.staged:
        fail("real gate mode requires --staged so the receipt covers the commit slug")
    if args.gate and args.config and not args.first_landing:
        fail("real gate mode binds policy to HEAD; --config requires --first-landing")
    if args.first_landing and (not args.gate or not args.staged or not args.config):
        fail("--first-landing requires --gate, --staged, and an explicit --config")
    source = "staged" if args.staged else str(receipt["source"])
    if args.gate and source == "worktree":
        fail("development-only source=worktree receipt is rejected in real gate mode")
    if source not in {"head", "staged", "worktree"}:
        fail(f"unsupported receipt source: {source}")
    if str(receipt["repo_root"]) != str(repo):
        fail("receipt repo_root does not match current repository")
    if str(receipt["base_head"]) != git_head(repo):
        fail("receipt base_head does not match current HEAD")
    if not re.fullmatch(r"[0-9a-f]{40}", str(receipt["base_head"])):
        fail("receipt base_head is not a lowercase commit SHA")
    if not re.fullmatch(r"[0-9a-f]{64}", str(receipt["include_set_sha256"])):
        fail("receipt include_set_sha256 is not a lowercase SHA-256")
    if args.first_landing:
        config_path = (repo / args.config).resolve() if not args.config.is_absolute() else args.config.resolve()
        if head_path_exists(repo, "00_Admin/configs/closeout_security_tiers.yaml"):
            fail("--first-landing is only valid before the canonical policy exists on HEAD")
        staged = staged_records(repo)
        if staged.get("00_Admin/configs/closeout_security_tiers.yaml") not in {"A", "M"}:
            fail("--first-landing requires the canonical policy to be staged")
        config = load_staged_config(repo, config_path)
    elif args.gate:
        config = load_head_config(repo)
    else:
        config = load_config(repo, args.config)
    if str(receipt.get("tiers_config_version")) != str(config.get("version")):
        fail("receipt tiers_config_version does not match the active policy")
    if str(receipt.get("ruleset_version")) != str(config.get("ruleset_version")):
        fail("receipt ruleset_version does not match the active policy")
    packet = config.get("packet", {})
    packet_budget = int(packet.get("estimated_tokens_per_packet", 20000))
    session_budget = int(packet.get("session_token_budget", 100000))
    packet_tokens = [int(value) for value in receipt["packet_estimated_tokens"]]
    if any(value > packet_budget for value in packet_tokens):
        fail(f"packet token cap exceeded: max={packet_budget}")
    if int(receipt["estimated_tokens_total"]) > session_budget or sum(packet_tokens) > session_budget:
        fail(f"session token cap exceeded: max={session_budget}")
    actual_packet_tokens: list[int] = []
    packet_sections: list[dict[str, Any]] = []
    for packet_path, recorded_sha in zip(receipt["packet_files"], receipt["packet_sha256"], strict=False):
        target = Path(str(packet_path))
        if not target.is_absolute():
            target = repo / target
        target = target.resolve()
        try:
            target.relative_to(repo)
        except ValueError:
            fail(f"packet path escapes repository: {packet_path}")
        try:
            data = target.read_bytes()
        except OSError as exc:
            fail(f"cannot read reviewer packet {packet_path}: {exc}")
        actual_sha = hashlib.sha256(data).hexdigest()
        if actual_sha != str(recorded_sha):
            fail(f"reviewer packet digest mismatch: {packet_path}")
        actual_packet_tokens.append((len(data) + 3) // 4)
        packet_sections.extend(parse_packet_sections(data))
    if actual_packet_tokens != packet_tokens:
        fail("reviewer packet token counts do not match packet bytes")
    rows = receipt["rows"]
    if not isinstance(rows, list) or not rows:
        fail("receipt rows must be a non-empty list")
    seen: set[str] = set()
    rows_by_path: dict[str, dict[str, Any]] = {}
    dispositions: list[str] = []
    actual_total_tokens = 0
    for row in rows:
        if not isinstance(row, dict):
            fail("receipt row must be a mapping")
        path = safe_path(str(row.get("path", "")))
        if path in seen:
            fail(f"duplicate receipt row: {path}")
        seen.add(path)
        rows_by_path[path] = row
        tier = str(row.get("tier", ""))
        if forced_t2(path, config) and tier != "T2":
            fail(f"forced-T2 path is under-tiered: {path}")
        if not re.fullmatch(r"[0-9a-f]{64}", str(row.get("sha256", ""))):
            fail(f"invalid row sha256 for {path}")
        try:
            data, basis = source_bytes(repo, path, source, str(row.get("file_kind", "text")))
        except OSError as exc:
            fail(f"cannot read {path}: {exc}")
        actual = hashlib.sha256(data).hexdigest()
        if actual != str(row.get("sha256", "")):
            fail(f"digest mismatch for {path} ({basis})")
        actual_total_tokens += (len(data) + 3) // 4
        coverage = str(row.get("coverage", ""))
        disposition = str(row.get("disposition", ""))
        dispositions.append(disposition)
        if args.gate:
            if coverage != "fully_reviewed":
                fail(f"incomplete full-file coverage for {path}: {coverage}")
            if disposition != "pass":
                fail(f"non-pass disposition for {path}: {disposition}")
            if str(row.get("file_kind")) == "unsupported":
                fail(f"unsupported file kind cannot pass the gate: {path}")
            if str(row.get("reviewer")) == "pending" or str(row.get("review_method")) != "full-file-plus-diff":
                fail(f"review attestation is incomplete for {path}")
            if tier == "T2" and row.get("independent_pass") is not True:
                fail(f"independent T2 pass is missing for {path}")
            if (
                str(row.get("file_kind")) in {"binary", "generated"}
                and "generator:" not in str(row.get("coverage_notes", ""))
            ):
                fail(f"binary/generated row lacks generator evidence: {path}")
            if row.get("prepass_status") == "candidate" and not row.get("finding_refs"):
                fail(f"candidate pre-pass row has no finding references: {path}")
    packet_by_path: dict[str, list[dict[str, Any]]] = {}
    for section in packet_sections:
        path = section["path"]
        if path not in rows_by_path:
            fail(f"reviewer packet contains an unlisted path: {path}")
        row = rows_by_path[path]
        if section["sha256"] != row["sha256"]:
            fail(f"reviewer packet file digest does not match receipt row: {path}")
        if section["content_bytes"] < 0:
            fail(f"reviewer packet content byte count is invalid: {path}")
        if section["content"] is not None:
            payload_bytes = section["content"].encode("utf-8")
            if hashlib.sha256(payload_bytes).hexdigest() != section["content_sha256"]:
                fail(f"reviewer packet content digest mismatch: {path}")
            if len(payload_bytes) != section["content_bytes"]:
                fail(f"reviewer packet content byte count mismatch: {path}")
        elif section["content_sha256"] != row["sha256"]:
            fail(f"omitted reviewer packet content is not bound to the file digest: {path}")
        packet_by_path.setdefault(path, []).append(section)
    if set(packet_by_path) != seen:
        missing = sorted(seen - set(packet_by_path))
        extra = sorted(set(packet_by_path) - seen)
        fail(f"reviewer packets do not cover receipt rows; missing={missing}; extra={extra}")
    for path, row in rows_by_path.items():
        sections = packet_by_path[path]
        expected_count = int(row["chunk_count"])
        if len(sections) != expected_count:
            fail(f"reviewer packet chunk count does not match receipt row: {path}")
        if {int(section["chunk"]) for section in sections} != set(range(1, expected_count + 1)):
            fail(f"reviewer packet chunk numbering is incomplete: {path}")
        if any(int(section["chunk_count"]) != expected_count for section in sections):
            fail(f"reviewer packet declares inconsistent chunk counts: {path}")
        if row["file_kind"] != "binary":
            ordered = sorted(sections, key=lambda section: int(section["chunk"]))
            if any(section["content"] is None for section in ordered):
                fail(f"reviewer packet omits text content: {path}")
            expected_data, _ = source_bytes(repo, path, source, str(row["file_kind"]))
            expected_text = expected_data.decode("utf-8", errors="replace")
            if "".join(section["content"] for section in ordered) != expected_text:
                fail(f"reviewer packet content does not match reviewed bytes: {path}")
    actual_include = include_hash(sorted(seen))
    if actual_include != str(receipt["include_set_sha256"]):
        fail("include-set hash does not match receipt rows")
    if actual_total_tokens != int(receipt["estimated_tokens_total"]):
        fail(f"estimated token total does not match reviewed bytes: {actual_total_tokens}")
    if args.gate and source == "staged":
        staged = staged_records(repo)
        if set(staged) != seen:
            missing = sorted(set(staged) - seen)
            extra = sorted(seen - set(staged))
            fail(f"receipt does not exactly cover staged paths; missing={missing}; extra={extra}")
        for row in rows:
            change = staged[str(row["path"])]
            if row["file_kind"] == "deleted" and change != "D":
                fail(f"row marks a non-deletion as deleted: {row['path']}")
            if row["file_kind"] != "deleted" and change == "D":
                fail(f"staged deletion is not classified as deleted: {row['path']}")
    receipt_digest = hashlib.sha256(canonical_receipt(receipt)).hexdigest()
    recorded_digest = receipt.get("receipt_sha256")
    if recorded_digest and recorded_digest != receipt_digest:
        fail("receipt_sha256 does not match receipt content")
    if args.trailer:
        disposition = "pass" if args.gate else ("needs_work" if "needs_work" in dispositions else "pending")
        check_trailer(args.trailer, disposition, actual_include, receipt_digest)
    print(f"PASS {len(rows)} rows source={source} gate={str(args.gate).lower()}")
    print(f"include_set_sha256={actual_include}")
    print(f"receipt_sha256={receipt_digest}")
    return 0


if __name__ == "__main__":
    main()
