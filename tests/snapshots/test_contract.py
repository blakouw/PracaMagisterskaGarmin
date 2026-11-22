import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def test_contract_and_registry_status():
    contract = json.loads((ROOT / "pipeline/16_persist_local_snapshot/contract.json").read_text(encoding="utf-8"))
    assert contract["module_id"] == "16_persist_local_snapshot"
    assert contract["status"] == "implemented"
    assert contract["run_command"] == "pipeline/16_persist_local_snapshot/run.bat"
    assert "15_build_dashboard_payload" in contract["depends_on"]
    assert "implement_api_server" in contract["prohibited_responsibilities"]
    registry = json.loads((ROOT / "config/pipeline_modules.json").read_text(encoding="utf-8"))
    by_id = {m["id"]: m for m in registry["modules"]}
    assert by_id["16_persist_local_snapshot"]["status"] == "implemented"
    assert by_id["17_local_api_server"]["status"] == "implemented"
    assert by_id["18_angular_dashboard_ui"]["status"] == "implemented"


