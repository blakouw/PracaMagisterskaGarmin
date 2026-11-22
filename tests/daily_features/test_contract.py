import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
def r(p): return json.loads((ROOT / p).read_text(encoding="utf-8"))
def test_contract_implemented():
    c = r("pipeline/07_build_daily_features/contract.json")
    assert c["status"] == "implemented"
    assert c["optional"] is False
    assert "05_normalize_daily_records" in c["depends_on"]
    assert "06_normalize_activities" in c["optional_inputs_from"]
    assert "calculate_acwr" in c["prohibited_responsibilities"]
    assert c["run_command"] == "pipeline/07_build_daily_features/run.bat"
def test_registry_statuses_after_module_07():
    mods = r("config/pipeline_modules.json")["modules"]
    for m in mods[:14]: assert m["status"] == "implemented", m["id"]
    for m in mods[14:]:
        expected = "implemented" if m["id"] in {"15_build_dashboard_payload", "16_persist_local_snapshot", "17_local_api_server", "18_angular_dashboard_ui", "19_packaging_windows"} else "planned"
        assert m["status"] == expected, m["id"]


