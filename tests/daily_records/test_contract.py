import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
def read_json(p: str) -> dict:
    return json.loads((ROOT / p).read_text(encoding="utf-8"))
def test_contract_implemented() -> None:
    c = read_json("pipeline/05_normalize_daily_records/contract.json")
    assert c["module_id"] == "05_normalize_daily_records"
    assert c["status"] == "implemented"
    assert c["optional"] is False
    assert "03_trim_workbook" in c["depends_on"]
    assert "04_garmin_activity_ingest" not in c["depends_on"]
    assert "normalize_activities" in c["prohibited_responsibilities"]
    assert "calculate_pws" in c["prohibited_responsibilities"]
def test_registry_statuses_after_module_05() -> None:
    modules = read_json("config/pipeline_modules.json")["modules"]
    for m in modules[:14]:
        assert m["status"] == "implemented", m["id"]
    for m in modules[14:]:
        expected = "implemented" if m["id"] in {"15_build_dashboard_payload", "16_persist_local_snapshot", "17_local_api_server", "18_angular_dashboard_ui", "19_packaging_windows"} else "planned"
        assert m["status"] == expected, m["id"]


