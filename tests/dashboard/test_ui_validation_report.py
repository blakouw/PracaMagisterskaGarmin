import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_ui_validation_report(validate_module):
    code = validate_module.main(["--build-exit-code", "0", "--frontend-test-exit-code", "0"])
    assert code == 0
    report = json.loads((ROOT / "data/pipeline/18_angular_dashboard_ui/ui_validation_report.json").read_text(encoding="utf-8"))
    assert report["validation_status"] == "valid"
    assert report["checks"]["api_client_uses_relative_api_paths"] is True
    assert report["checks"]["direct_pipeline_file_reads_absent"] is True
    assert report["checks"]["auth_profile_features_absent"] is True
