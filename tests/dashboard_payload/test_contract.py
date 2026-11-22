import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_contract():
    c=json.loads((ROOT/"pipeline/15_build_dashboard_payload/contract.json").read_text(encoding="utf-8"))
    assert c["module_id"]=="15_build_dashboard_payload"
    assert c["status"]=="implemented"
    assert "implement_api_server" in c["prohibited_responsibilities"]
    registry=json.loads((ROOT/"config/pipeline_modules.json").read_text(encoding="utf-8"))
    by={m["id"]:m for m in registry["modules"]}
    assert by["15_build_dashboard_payload"]["status"]=="implemented"
    assert by["14_build_coach_context"]["status"]=="planned"
    assert by["16_persist_local_snapshot"]["status"]=="implemented"

