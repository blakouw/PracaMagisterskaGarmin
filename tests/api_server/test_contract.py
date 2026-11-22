import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def test_contract_and_registry():
    c = json.loads((ROOT / "pipeline/17_local_api_server/contract.json").read_text(encoding="utf-8"))
    assert c["module_id"] == "17_local_api_server"
    assert c["status"] == "implemented"
    assert c["runtime"]["host"] == "127.0.0.1"
    assert "16_persist_local_snapshot" in c["depends_on"]
    assert "implement_authentication" in c["prohibited_responsibilities"]
    registry = json.loads((ROOT / "config/pipeline_modules.json").read_text(encoding="utf-8"))
    by = {m["id"]: m for m in registry["modules"]}
    assert by["17_local_api_server"]["status"] == "implemented"
    assert by["18_angular_dashboard_ui"]["status"] == "implemented"
    assert by["19_packaging_windows"]["status"] == "implemented"

