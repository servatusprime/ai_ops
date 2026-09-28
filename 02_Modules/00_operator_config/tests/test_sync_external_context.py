from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "operations" / "op_sync_external_context.py"
SPEC = importlib.util.spec_from_file_location("op_sync_external_context", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
sync_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync_module)


class ExternalContextRefreshTests(unittest.TestCase):
    def setUp(self) -> None:
        sandbox = Path(__file__).resolve().parents[3] / "90_Sandbox"
        self.temp = tempfile.TemporaryDirectory(dir=sandbox)
        self.repo = Path(self.temp.name)
        self.source = self.repo / "source" / "context.md"
        self.source.parent.mkdir()
        self.source.write_text("original\n", encoding="utf-8")
        self.bundle = self.repo / "output" / "bundle"
        self.bundle.mkdir(parents=True)
        self.config_file = self.repo / "00_Admin" / "configs" / "setup_contract.yaml"
        self.config_file.parent.mkdir(parents=True)
        self.config_file.write_text(
            "customizations:\n"
            "  external_context:\n"
            "    manifest_path: manifest.yaml\n"
            "    bundle_root: output/bundle\n",
            encoding="utf-8",
        )
        self.config = self.config_file
        self.manifest = self.repo / "manifest.yaml"
        self.manifest.write_text(
            "files:\n"
            "  - source_path: source/context.md\n"
            "    bundle_path: context.md\n",
            encoding="utf-8",
        )
    def tearDown(self) -> None:
        self.temp.cleanup()

    @property
    def output(self) -> Path:
        return self.bundle / "context.md"

    @property
    def receipt(self) -> Path:
        return self.bundle / ".context.md.external-context.json"

    def test_default_apply_is_no_clobber_and_repeat_requires_refresh(self) -> None:
        sync_module.sync_external_context(self.config, dry_run=False)
        self.assertEqual(self.output.read_text(encoding="utf-8"), "original\n")
        with self.assertRaises(FileExistsError):
            sync_module.sync_external_context(self.config, dry_run=False)
        self.assertEqual(self.output.read_text(encoding="utf-8"), "original\n")

    def test_refresh_replaces_only_receipted_output_and_updates_digest(self) -> None:
        sync_module.sync_external_context(self.config, dry_run=False)
        before = json.loads(self.receipt.read_text(encoding="utf-8"))
        self.source.write_text("refreshed\n", encoding="utf-8")

        sync_module.sync_external_context(self.config, dry_run=False, refresh=True)

        after = json.loads(self.receipt.read_text(encoding="utf-8"))
        self.assertEqual(self.output.read_text(encoding="utf-8"), "refreshed\n")
        self.assertEqual(before["source"], after["source"])
        self.assertEqual(before["destination"], after["destination"])
        self.assertNotEqual(before["destination_sha256"], after["destination_sha256"])

    def test_refresh_rejects_destination_edits_and_manifest_identity_changes(self) -> None:
        sync_module.sync_external_context(self.config, dry_run=False)
        self.output.write_text("operator edit\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "changed since"):
            sync_module.sync_external_context(self.config, dry_run=False, refresh=True)
        self.assertEqual(self.output.read_text(encoding="utf-8"), "operator edit\n")

        self.output.write_text("original\n", encoding="utf-8")
        alternate = self.repo / "source" / "alternate.md"
        alternate.write_text("original\n", encoding="utf-8")
        self.manifest.write_text(
            "files:\n"
            "  - source_path: source/alternate.md\n"
            "    bundle_path: context.md\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "identity does not match"):
            sync_module.sync_external_context(self.config, dry_run=False, refresh=True)

    def test_refresh_rolls_back_destination_if_atomic_promotion_fails(self) -> None:
        sync_module.sync_external_context(self.config, dry_run=False)
        self.source.write_text("new content\n", encoding="utf-8")
        original_replace = os.replace
        failed = False

        def fail_once(src: os.PathLike[str] | str, dst: os.PathLike[str] | str) -> None:
            nonlocal failed
            if Path(dst) == self.output and Path(src) != self.output and not failed:
                failed = True
                raise OSError("injected promotion failure")
            original_replace(src, dst)

        with mock.patch.object(sync_module.os, "replace", side_effect=fail_once):
            with self.assertRaisesRegex(OSError, "injected promotion failure"):
                sync_module.sync_external_context(self.config, dry_run=False, refresh=True)

        self.assertEqual(self.output.read_text(encoding="utf-8"), "original\n")
        receipt = json.loads(self.receipt.read_text(encoding="utf-8"))
        self.assertEqual(receipt["destination_sha256"], sync_module._sha256(self.output))

    def test_source_and_destination_containment_remain_enforced(self) -> None:
        for source_path, bundle_path in (
            ("../outside.md", "context.md"),
            ("source/context.md", "../outside.md"),
        ):
            with self.subTest(source=source_path, destination=bundle_path):
                self.manifest.write_text(
                    "files:\n"
                    f"  - source_path: {source_path}\n"
                    f"    bundle_path: {bundle_path}\n",
                    encoding="utf-8",
                )
                with self.assertRaises(ValueError):
                    sync_module.sync_external_context(
                        self.config, dry_run=False, refresh=True
                    )
        self.assertFalse((self.repo / "outside.md").exists())

    def test_refresh_rejects_changed_mapping_and_default_mode_stays_non_destructive(self) -> None:
        sync_module.sync_external_context(self.config, dry_run=False)
        with self.assertRaises(FileExistsError):
            sync_module.sync_external_context(self.config, dry_run=False)
        self.assertTrue(self.output.exists())
        self.assertTrue(self.receipt.exists())


if __name__ == "__main__":
    unittest.main()
