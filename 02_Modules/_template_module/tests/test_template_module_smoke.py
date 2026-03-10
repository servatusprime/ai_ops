from __future__ import annotations

from pathlib import Path


def test_metadata_exists_and_has_id():
    module_root = Path(__file__).resolve().parents[1]
    meta_path = module_root / "metadata" / "module.yaml"
    assert meta_path.exists(), "metadata/module.yaml missing"
    text = meta_path.read_text(encoding="utf-8")
    assert f"id: {module_root.name}" in text, "metadata/module.yaml id does not match folder name"
    assert "status:" in text, "metadata/module.yaml missing status"
    assert "owner:" in text, "metadata/module.yaml missing owner"


def test_src_folder_present():
    module_root = Path(__file__).resolve().parents[1]
    assert (module_root / "src").exists(), "src folder missing"
