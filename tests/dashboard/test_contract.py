import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_ID = "18_angular_dashboard_ui"


def test_contract_and_registry_status():
    contract = json.loads((ROOT / "pipeline" / MODULE_ID / "contract.json").read_text(encoding="utf-8"))
    assert contract["module_id"] == MODULE_ID
    assert contract["status"] == "implemented"
    assert contract["runtime"]["api_proxy_target"] == "http://127.0.0.1:8765"
    assert "17_local_api_server" in contract["depends_on"]
    assert "implement_authentication" in contract["prohibited_responsibilities"]
    registry = json.loads((ROOT / "config/pipeline_modules.json").read_text(encoding="utf-8"))
    by_id = {module["id"]: module for module in registry["modules"]}
    assert by_id[MODULE_ID]["status"] == "implemented"
    assert by_id["19_packaging_windows"]["status"] == "implemented"
    assert "auth_and_profile_api" not in by_id
    assert "garmin_token_pipeline" not in by_id
