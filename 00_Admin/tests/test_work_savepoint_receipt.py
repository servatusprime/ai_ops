from __future__ import annotations

import hashlib
import importlib.util
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "00_Admin" / "scripts" / "validate_work_savepoint_receipt.py"
SPEC = importlib.util.spec_from_file_location("validate_work_savepoint_receipt", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class WorkSavepointReceiptTests(unittest.TestCase):
    def _receipt(self, root: Path) -> Path:
        include = ["90_Sandbox/workbook.md"]
        data = {
            "receipt_version": "0.1.0",
            "repo_root": str(root),
            "repo_id": root.name,
            "artifact_id": "wb_test",
            "active_path": "90_Sandbox/workbook.md",
            "head": "a" * 40,
            "branch": "main",
            "include": include,
            "include_set_sha256": hashlib.sha256("\n".join(include).encode()).hexdigest(),
            "future_work": "not_applicable",
            "status": "checkpointed",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        path = root / "receipt.yaml"
        path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
        return path

    def test_valid_receipt_binds_identity_and_include(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            active = root / "90_Sandbox" / "workbook.md"
            active.parent.mkdir()
            active.write_text("active\n", encoding="utf-8")
            receipt = self._receipt(root)
            result = MODULE.validate_receipt(receipt, repo_root=root, expected_head="a" * 40)
            self.assertEqual("wb_test", result["artifact_id"])

    def test_unsorted_or_duplicate_include_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            receipt = self._receipt(root)
            data = yaml.safe_load(receipt.read_text(encoding="utf-8"))
            data["include"] = ["b", "a"]
            receipt.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
            with self.assertRaisesRegex(MODULE.ReceiptError, "sorted"):
                MODULE.validate_receipt(receipt, expected_head="a" * 40)

    def test_head_and_active_path_are_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            receipt = self._receipt(root)
            with self.assertRaisesRegex(MODULE.ReceiptError, "HEAD"):
                MODULE.validate_receipt(receipt, expected_head="b" * 40)
            with self.assertRaisesRegex(MODULE.ReceiptError, "active_path"):
                MODULE.validate_receipt(receipt, repo_root=root, expected_head="a" * 40)

    def test_schema_enums_unknown_fields_and_repo_binding_are_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            active = root / "90_Sandbox" / "workbook.md"
            active.parent.mkdir()
            active.write_text("active\n", encoding="utf-8")
            receipt = self._receipt(root)
            data = yaml.safe_load(receipt.read_text(encoding="utf-8"))
            data["future_work"] = "invented"
            with self.assertRaisesRegex(MODULE.ReceiptError, "future_work"):
                receipt.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
                MODULE.validate_receipt(receipt, repo_root=root, expected_head="a" * 40)
            data = yaml.safe_load(receipt.read_text(encoding="utf-8"))
            data["future_work"] = "not_applicable"
            data["unexpected"] = True
            receipt.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
            with self.assertRaisesRegex(MODULE.ReceiptError, "undeclared"):
                MODULE.validate_receipt(receipt, repo_root=root, expected_head="a" * 40)
            data = yaml.safe_load(receipt.read_text(encoding="utf-8"))
            data.pop("unexpected")
            data["repo_root"] = str(root / "spoofed")
            receipt.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
            with self.assertRaisesRegex(MODULE.ReceiptError, "repo_root"):
                MODULE.validate_receipt(receipt, repo_root=root, expected_head="a" * 40)

    def test_absolute_include_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            receipt = self._receipt(root)
            data = yaml.safe_load(receipt.read_text(encoding="utf-8"))
            data["include"] = ["C:/outside.md"]
            data["include_set_sha256"] = hashlib.sha256("C:/outside.md".encode()).hexdigest()
            receipt.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
            with self.assertRaisesRegex(MODULE.ReceiptError, "include"):
                MODULE.validate_receipt(receipt, expected_head="a" * 40)


if __name__ == "__main__":
    unittest.main()
