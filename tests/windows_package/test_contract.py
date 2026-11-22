from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_ID = "19_packaging_windows"


def test_contract_and_registry_are_implemented():
    contract = json.loads((ROOT / "pipeline" / MODULE_ID / "contract.json").read_text(encoding="utf-8"))
    registry = json.loads((ROOT / "config/pipeline_modules.json").read_text(encoding="utf-8"))
    by_id = {item["id"]: item for item in registry["modules"]}
    assert contract["module_id"] == MODULE_ID
    assert contract["status"] == "implemented"
    assert by_id[MODULE_ID]["status"] == "implemented"
    assert by_id[MODULE_ID]["runtime"]["host"] == "127.0.0.1"
    assert by_id[MODULE_ID]["runtime"]["uses_vite_dev_server"] is False
    assert "auth_and_profile_api" not in by_id
    assert "garmin_token_pipeline" not in by_id


def test_expected_outputs_are_declared():
    registry = json.loads((ROOT / "config/pipeline_modules.json").read_text(encoding="utf-8"))
    module = next(item for item in registry["modules"] if item["id"] == MODULE_ID)
    expected = set(module["expected_outputs"])
    assert f"data/pipeline/{MODULE_ID}/windows_package_manifest.json" in expected
    assert f"data/pipeline/{MODULE_ID}/windows_package_integrity.json" in expected
    assert f"data/pipeline/{MODULE_ID}/windows_package_privacy_audit.json" in expected
    assert "release/windows/PersonalWellnessDashboard_1.0.0_portable/" in expected
    assert "release/windows/PersonalWellnessDashboard_1.0.0_portable.zip" in expected
