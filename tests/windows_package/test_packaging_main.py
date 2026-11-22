from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_policy_registry_and_inputs_validate(packaging_module):
    assert packaging_module.validate_policy(ROOT) == []
    _, registry_errors = packaging_module.validate_registry(ROOT)
    assert registry_errors == []
    assert packaging_module.check_inputs(ROOT) == []


def test_package_privacy_audit_detects_forbidden_files(tmp_path, packaging_module, monkeypatch):
    pkg = tmp_path / "release/windows/PersonalWellnessDashboard_1.0.0_portable"
    current = pkg / "data/published/dashboard_snapshots/current"
    current.mkdir(parents=True)
    (current / "dashboard_payload.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(packaging_module, "package_dir", lambda root: pkg)
    audit = packaging_module.privacy_audit(tmp_path)
    assert audit["status"] == "failed"
    assert audit["private_snapshots_packaged"] is True
    assert audit["findings"][0]["path"].endswith("dashboard_payload.json")


def test_package_manifest_confirms_runtime_boundaries(packaging_module, tmp_path):
    pkg = tmp_path / "release/windows/PersonalWellnessDashboard_1.0.0_portable"
    exe = pkg / "PersonalWellnessDashboard.exe"
    exe.parent.mkdir(parents=True)
    exe.write_bytes(b"synthetic")
    zip_path = tmp_path / "release/windows/PersonalWellnessDashboard_1.0.0_portable.zip"
    manifest = packaging_module.package_manifest(tmp_path, exe, {"package_directory": "release/windows/PersonalWellnessDashboard_1.0.0_portable"}, zip_path)
    assert manifest["runtime"]["host"] == "127.0.0.1"
    assert manifest["runtime"]["uses_vite_dev_server"] is False
    assert manifest["data_policy"]["current_snapshot_packaged"] is False
    assert manifest["forbidden_action_confirmation"]["pipeline_triggered"] is False
    assert manifest["forbidden_action_confirmation"]["llm_called"] is False


def test_generated_artifacts_if_present_are_private_data_free():
    artifact = ROOT / "data/pipeline/19_packaging_windows"
    if not artifact.exists():
        return
    privacy_path = artifact / "windows_package_privacy_audit.json"
    if not privacy_path.exists():
        return
    privacy = json.loads(privacy_path.read_text(encoding="utf-8"))
    assert privacy["private_snapshots_packaged"] is False
    assert privacy["tokens_or_secrets_packaged"] is False
    assert privacy["raw_garmin_files_packaged"] is False
