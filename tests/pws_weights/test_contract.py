import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_contract_is_implemented():
    contract = json.loads((ROOT / "pipeline/11_compute_pws_weights/contract.json").read_text(encoding="utf-8"))
    assert contract["module_id"] == "11_compute_pws_weights"
    assert contract["status"] == "implemented"
    assert "calculate_final_pws" in contract["prohibited_responsibilities"]
    assert "call_llm" in contract["prohibited_responsibilities"]


def test_pipeline_registry_marks_module11_implemented_and_future_planned():
    registry = json.loads((ROOT / "config/pipeline_modules.json").read_text(encoding="utf-8"))
    modules = registry["modules"]
    by_id = {module["id"]: module for module in modules}
    assert by_id["11_compute_pws_weights"]["status"] == "implemented"
    assert by_id["12_compute_pws_score"]["status"] == "implemented"
    for module in modules:
        if module["id"] in {"15_build_dashboard_payload", "16_persist_local_snapshot", "17_local_api_server", "18_angular_dashboard_ui", "19_packaging_windows"}:
            assert module["status"] == "implemented"
        elif module["order"] > 13:
            assert module["status"] == "planned"



