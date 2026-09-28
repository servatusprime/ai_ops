"""Sync declared external context into the repo work area (dry-run by default).

Ordinary --apply creates new outputs and refuses every existing destination.
Use --refresh --apply only for outputs whose sidecar receipt still proves the
same manifest source/destination mapping and unchanged last-synced bytes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Iterable, List

REPARSE_POINT = 0x400


def _is_reparse(path: Path) -> bool:
    try:
        info = path.lstat()
    except OSError:
        return False
    return path.is_symlink() or bool(getattr(info, "st_file_attributes", 0) & REPARSE_POINT)


def _assert_no_reparse_components(path: Path, root: Path, label: str) -> None:
    """Inspect lexical components so resolving a link cannot hide its parent."""
    trusted = Path(os.path.abspath(os.fspath(root)))
    lexical = Path(os.path.abspath(os.fspath(path)))
    try:
        relative = lexical.relative_to(trusted)
    except ValueError as exc:
        raise ValueError(f"{label} escapes trusted root: {path}") from exc
    current = trusted
    for part in relative.parts:
        current = current / part
        if current.exists() and _is_reparse(current):
            raise ValueError(f"{label} crosses a symlink/reparse point: {path}")


def _resolve_inside(path: Path, root: Path, *, label: str, must_exist: bool = True) -> Path:
    trusted = root.resolve(strict=True)
    lexical = path if path.is_absolute() else trusted / path
    resolved = lexical.resolve(strict=False)
    try:
        resolved.relative_to(trusted)
    except ValueError as exc:
        raise ValueError(f"{label} escapes trusted root: {path}") from exc
    if must_exist and not resolved.exists():
        raise FileNotFoundError(f"{label} does not exist: {resolved}")
    _assert_no_reparse_components(lexical, trusted, label)
    return resolved


def _load_yaml(path: Path) -> dict:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise RuntimeError("PyYAML is required to load the config file") from exc

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}, got {type(data).__name__}")
    return data


def _match_filters(path: Path, include_patterns: Iterable[str], exclude_patterns: Iterable[str]) -> bool:
    includes = list(include_patterns)
    excludes = list(exclude_patterns)
    rel = path.as_posix()

    if includes and not any(Path(rel).match(pattern) for pattern in includes):
        return False
    if excludes and any(Path(rel).match(pattern) for pattern in excludes):
        return False
    return True


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _identity_path(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _receipt_path(destination: Path) -> Path:
    return destination.with_name(f".{destination.name}.external-context.json")


def _load_refresh_receipt(
    receipt_path: Path, source_id: str, destination_id: str, destination: Path
) -> dict:
    if _is_reparse(receipt_path):
        raise ValueError(f"refresh receipt is a symlink/reparse point: {receipt_path}")
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileExistsError(
            f"Refusing refresh without a prior external-context receipt: {receipt_path}"
        ) from exc
    if not isinstance(receipt, dict) or receipt.get("schema_version") != 1:
        raise ValueError(f"invalid external-context refresh receipt: {receipt_path}")
    if receipt.get("source") != source_id or receipt.get("destination") != destination_id:
        raise ValueError("refresh source/destination identity does not match prior receipt")
    if not destination.is_file() or _is_reparse(destination):
        raise ValueError(f"refresh destination is missing or unsafe: {destination}")
    if _sha256(destination) != receipt.get("destination_sha256"):
        raise ValueError("refresh destination changed since the last governed sync")
    return receipt


def _write_json_atomic(path: Path, data: dict) -> None:
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", prefix=f".{path.name}.",
            suffix=".tmp", dir=path.parent, delete=False
        ) as handle:
            temp_name = handle.name
            json.dump(data, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        Path(temp_name).replace(path)
    except Exception:
        if temp_name:
            Path(temp_name).unlink(missing_ok=True)
        raise


def _write_json_exclusive(path: Path, data: dict) -> None:
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", prefix=f".{path.name}.",
            suffix=".tmp", dir=path.parent, delete=False
        ) as handle:
            temp_name = handle.name
            json.dump(data, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temp_name, path)
    finally:
        if temp_name:
            Path(temp_name).unlink(missing_ok=True)


def _copy_to_temp(source: Path, destination: Path) -> tuple[Path, str]:
    temp_name: str | None = None
    try:
        with source.open("rb") as source_handle:
            before = os.fstat(source_handle.fileno())
            with tempfile.NamedTemporaryFile(
                mode="wb", prefix=f".{destination.name}.", suffix=".tmp",
                dir=destination.parent, delete=False
            ) as target_handle:
                temp_name = target_handle.name
                shutil.copyfileobj(source_handle, target_handle)
                target_handle.flush()
                os.fsync(target_handle.fileno())
            after = os.fstat(source_handle.fileno())
        identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
        identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
        if identity_before != identity_after:
            raise RuntimeError(f"external-context source changed during refresh: {source}")
        temp_path = Path(temp_name)
        return temp_path, _sha256(temp_path)
    except Exception:
        if temp_name:
            Path(temp_name).unlink(missing_ok=True)
        raise


def _apply_new_copy(source: Path, destination: Path, receipt_path: Path,
                    source_id: str, destination_id: str) -> None:
    temp_path, digest = _copy_to_temp(source, destination)
    promoted = False
    try:
        # A same-directory hard link provides atomic, no-clobber promotion.
        os.link(temp_path, destination)
        promoted = True
        shutil.copystat(source, destination, follow_symlinks=False)
        _write_json_exclusive(receipt_path, {
            "schema_version": 1,
            "source": source_id,
            "destination": destination_id,
            "destination_sha256": digest,
        })
    except Exception:
        if promoted:
            destination.unlink(missing_ok=True)
        raise
    finally:
        temp_path.unlink(missing_ok=True)


def _apply_refresh(source: Path, destination: Path, receipt_path: Path,
                   source_id: str, destination_id: str) -> None:
    _load_refresh_receipt(receipt_path, source_id, destination_id, destination)
    temp_path, digest = _copy_to_temp(source, destination)
    backup_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=f".{destination.name}.", suffix=".rollback",
            dir=destination.parent, delete=False
        ) as backup:
            backup_path = Path(backup.name)
        backup_path.unlink()
        _load_refresh_receipt(receipt_path, source_id, destination_id, destination)
        os.replace(destination, backup_path)
        try:
            os.replace(temp_path, destination)
            shutil.copystat(source, destination, follow_symlinks=False)
            _write_json_atomic(receipt_path, {
                "schema_version": 1,
                "source": source_id,
                "destination": destination_id,
                "destination_sha256": digest,
            })
        except Exception:
            destination.unlink(missing_ok=True)
            os.replace(backup_path, destination)
            backup_path = None
            raise
    finally:
        temp_path.unlink(missing_ok=True)
        if backup_path is not None:
            backup_path.unlink(missing_ok=True)


def sync_external_context(
    config_path: Path, dry_run: bool = True, refresh: bool = False
) -> List[Path]:
    config_candidate = config_path if config_path.is_absolute() else Path.cwd() / config_path
    # setup_contract.yaml lives under 00_Admin/configs; derive the governed
    # repo root instead of treating the config directory as the root.
    if config_candidate.parent.name == "configs" and config_candidate.parent.parent.name == "00_Admin":
        repo_root = config_candidate.parents[2]
    else:
        repo_root = Path.cwd().resolve()
    config_path = _resolve_inside(config_candidate, repo_root, label="config")
    data = _load_yaml(config_path)
    customizations = data.get("customizations", {})
    external = customizations.get("external_context", {})
    include_patterns = external.get("include_patterns", [])
    exclude_patterns = external.get("exclude_patterns", [])

    manifest_path_raw = Path(external.get("manifest_path", "90_Sandbox/ai_external_context/manifest.yaml"))
    bundle_root_raw = Path(external.get("bundle_root", "90_Sandbox/ai_external_context"))
    if manifest_path_raw.is_absolute() or bundle_root_raw.is_absolute():
        raise ValueError("external-context manifest_path and bundle_root must be repo-relative")
    manifest_path = _resolve_inside(repo_root / manifest_path_raw, repo_root, label="manifest")
    bundle_root = _resolve_inside(repo_root / bundle_root_raw, repo_root, label="bundle root", must_exist=False)

    copied: List[Path] = []
    if not manifest_path.exists():
        raise FileNotFoundError(f"External context manifest not found: {manifest_path}")

    manifest = _load_yaml(manifest_path)
    files = manifest.get("files", [])
    if not isinstance(files, list):
        raise ValueError("ai_external_context manifest 'files' must be a list")

    for entry in files:
        if not isinstance(entry, dict):
            continue
        source = entry.get("source_path")
        bundle = entry.get("bundle_path")
        if not source or not bundle:
            continue
        if not _match_filters(Path(bundle), include_patterns, exclude_patterns):
            continue
        source_raw = Path(str(source))
        bundle_raw = Path(str(bundle))
        if source_raw.is_absolute() or bundle_raw.is_absolute():
            raise ValueError("source_path and bundle_path must be relative")
        src = _resolve_inside(repo_root / source_raw, repo_root, label="source")
        dest = _resolve_inside(bundle_root / bundle_raw, bundle_root, label="bundle destination", must_exist=False)
        if src == dest:
            raise ValueError("external-context source and destination resolve to the same file")
        receipt_path = _receipt_path(dest)
        _assert_no_reparse_components(receipt_path, bundle_root, "bundle refresh receipt")
        source_id = _identity_path(src, repo_root)
        destination_id = _identity_path(dest, bundle_root)
        if refresh:
            if not (dest.exists() or dest.is_symlink()):
                raise FileNotFoundError(f"cannot refresh a missing external-context output: {dest}")
            _load_refresh_receipt(receipt_path, source_id, destination_id, dest)
        elif dest.exists() or dest.is_symlink() or receipt_path.exists() or receipt_path.is_symlink():
            raise FileExistsError(f"Refusing to clobber existing external-context output: {dest}")
        copied.append(dest)
        if dry_run:
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        if _is_reparse(dest.parent):
            raise ValueError(f"bundle destination parent is a symlink/reparse point: {dest.parent}")
        if refresh:
            _apply_refresh(src, dest, receipt_path, source_id, destination_id)
        else:
            _apply_new_copy(src, dest, receipt_path, source_id, destination_id)
    return copied


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync external context into the repo work area.")
    parser.add_argument("--config", default="00_Admin/configs/setup_contract.yaml",
                        help="Path to config file (customizations section)")
    parser.add_argument("--apply", action="store_true", help="Apply changes (default: dry run)")
    parser.add_argument(
        "--refresh", action="store_true",
        help="Refresh only outputs with matching prior sync receipts; requires --apply",
    )
    args = parser.parse_args()

    if args.refresh and not args.apply:
        parser.error("--refresh requires --apply")

    try:
        copied = sync_external_context(
            Path(args.config), dry_run=not args.apply, refresh=args.refresh
        )
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}")
        return 1
    print(f"Planned copies: {len(copied)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
