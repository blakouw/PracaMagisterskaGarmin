import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def read_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))

def test_module_04_contract_is_implemented_and_optional() -> None:
    contract = read_json("pipeline/04_garmin_activity_ingest/contract.json")
    assert contract["module_id"] == "04_garmin_activity_ingest"
    assert contract["status"] == "implemented"
    assert contract["optional"] is True
    assert contract["run_command"] == "pipeline/04_garmin_activity_ingest/run.bat"
    assert "store_token_values_in_artifacts" in contract["prohibited_responsibilities"]
    assert "normalize_activities" in contract["prohibited_responsibilities"]
    assert "call_llm" in contract["prohibited_responsibilities"]


def test_registry_statuses_after_module_04() -> None:
    modules = read_json("config/pipeline_modules.json")["modules"]
    for module in modules[:14]:
        assert module["status"] == "implemented", module["id"]
    assert modules[4]["optional"] is True
    for module in modules[14:]:
        expected = "implemented" if module["id"] in {"15_build_dashboard_payload", "16_persist_local_snapshot", "17_local_api_server", "18_angular_dashboard_ui", "19_packaging_windows"} else "planned"
        assert module["status"] == expected, module["id"]


