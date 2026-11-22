from __future__ import annotations

import json

from registry_helpers import ROOT, module_ids


def test_required_project_roots_exist() -> None:
    for relative_path in ["pipeline", "tests", "visualization", "config"]:
        assert (ROOT / relative_path).is_dir(), relative_path


def test_key_contract_files_exist_and_parse() -> None:
    required = [
        "config/pipeline_modules.json",
        "pipeline/00_project_contract/README.md",
        "pipeline/00_project_contract/contract.json",
        ".gitignore",
    ]
    for relative_path in required:
        assert (ROOT / relative_path).is_file(), relative_path
    json.loads((ROOT / "config/pipeline_modules.json").read_text(encoding="utf-8"))
    contract = json.loads((ROOT / "pipeline/00_project_contract/contract.json").read_text(encoding="utf-8"))
    assert contract["module_id"] == "00_project_contract"


def test_module_00_test_layer_is_separate_from_production_and_visualization() -> None:
    assert (ROOT / "pipeline/00_project_contract").is_dir()
    assert (ROOT / "tests/00_project_contract").is_dir()
    assert (ROOT / "visualization/00_project_contract").is_dir()
    assert not (ROOT / "pipeline/00_project_contract/tests").exists()
    assert not (ROOT / "tests/00_project_contract/pipeline").exists()


def test_registry_modules_have_pipeline_folders() -> None:
    for module_id in module_ids():
        assert (ROOT / "pipeline" / module_id).is_dir(), module_id


def test_tests_folder_does_not_contain_production_module_contracts() -> None:
    for contract_path in (ROOT / "tests").rglob("contract.json"):
        payload = json.loads(contract_path.read_text(encoding="utf-8"))
        assert "module_id" not in payload, contract_path


def test_visualization_is_not_nested_inside_pipeline_or_tests() -> None:
    visualization_root = (ROOT / "visualization").resolve()
    assert visualization_root.is_dir()
    assert (ROOT / "pipeline" / "visualization").exists() is False
    assert (ROOT / "tests" / "visualization").exists() is False
