from __future__ import annotations

import json
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_ID = "19_packaging_windows"
ARTIFACT = ROOT / "data/pipeline" / MODULE_ID
PACKAGE = ROOT / "release/windows/PersonalWellnessDashboard_1.0.0_portable"
ZIP = ROOT / "release/windows/PersonalWellnessDashboard_1.0.0_portable.zip"


def test_release_artifacts_exist_after_module_execution():
    required = [
        ARTIFACT / "windows_package_manifest.json",
        ARTIFACT / "windows_package_integrity.json",
        ARTIFACT / "windows_package_privacy_audit.json",
        ARTIFACT / "windows_package_quality_report.json",
        ARTIFACT / "windows_package_lineage.json",
        ARTIFACT / "run_manifest.json",
        ARTIFACT / "run_log.txt",
        ARTIFACT / "errors.json",
    ]
    missing = [path for path in required if not path.exists()]
    assert not missing


def test_release_tree_excludes_private_snapshot_and_includes_placeholder():
    assert (PACKAGE / "PersonalWellnessDashboard.exe").is_file()
    assert (PACKAGE / "runtime/ui/index.html").is_file()
    assert (PACKAGE / "data/published/dashboard_snapshots/current/PLACE_CURRENT_SNAPSHOT_HERE.txt").is_file()
    assert not (PACKAGE / "data/published/dashboard_snapshots/current/dashboard_payload.json").exists()


def test_zip_exists_and_does_not_contain_private_snapshot():
    assert ZIP.is_file()
    with zipfile.ZipFile(ZIP) as archive:
        names = archive.namelist()
    assert any(name.endswith("PersonalWellnessDashboard.exe") for name in names)
    assert any(name.endswith("runtime/ui/index.html") for name in names)
    assert not any(name.endswith("dashboard_payload.json") and "data/published/dashboard_snapshots/current" in name for name in names)


def test_quality_and_lineage_confirm_no_forbidden_actions():
    quality = json.loads((ARTIFACT / "windows_package_quality_report.json").read_text(encoding="utf-8"))
    lineage = json.loads((ARTIFACT / "windows_package_lineage.json").read_text(encoding="utf-8"))
    assert quality["runtime"]["local_only"] is True
    assert quality["runtime"]["uses_vite_dev_server"] is False
    assert quality["privacy"]["private_snapshots_packaged"] is False
    forbidden = lineage["forbidden_action_confirmation"]
    assert forbidden["analytical_pipeline_triggered"] is False
    assert forbidden["garmin_data_downloaded"] is False
    assert forbidden["llm_called"] is False
    assert forbidden["public_deployment_implemented"] is False
