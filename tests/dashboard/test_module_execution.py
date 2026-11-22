import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_module_execution(validate_module):
    assert validate_module.main(["--build-exit-code", "0", "--frontend-test-exit-code", "0"]) == 0
    manifest = json.loads((ROOT / "data/pipeline/18_angular_dashboard_ui/run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["execution_status"] == "success"
    assert manifest["runtime"]["api_proxy_target"] == "http://127.0.0.1:8765"
    assert manifest["forbidden_action_confirmation"]["pipeline_triggered"] is False
