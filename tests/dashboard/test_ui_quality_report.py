import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_ui_quality_report(validate_module):
    assert validate_module.main(["--build-exit-code", "0", "--frontend-test-exit-code", "0"]) == 0
    report = json.loads((ROOT / "data/pipeline/18_angular_dashboard_ui/ui_quality_report.json").read_text(encoding="utf-8"))
    assert report["status"] == "implemented_and_validated"
    assert report["data_contract"]["uses_local_api_only"] is True
    assert report["forbidden_action_confirmation"]["llm_calls"] is False
    assert report["runtime_boundary"]["public_deployment_approved"] is False
