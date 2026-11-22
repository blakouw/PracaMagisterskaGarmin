import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


IMPLEMENTED_AFTER_LOAD_METRICS = {
    "09_compute_readiness",
    "10_compute_pws_components",
    "11_compute_pws_weights",
    "12_compute_pws_score",
    "13_validate_llm_weight_influence",
    "15_build_dashboard_payload",
    "16_persist_local_snapshot",
    "17_local_api_server",
    "18_angular_dashboard_ui",
    "19_packaging_windows",
}


def test_contract_and_pipeline_status():
    contract = json.loads((ROOT / "pipeline/08_compute_load_metrics/contract.json").read_text(encoding="utf-8"))
    assert contract["module_id"] == "08_compute_load_metrics"
    assert contract["status"] == "implemented"
    assert "07_build_daily_features" in contract["depends_on"]
    assert "calculate_readiness" in contract["prohibited_responsibilities"]
    registry = json.loads((ROOT / "config/pipeline_modules.json").read_text(encoding="utf-8"))
    modules = registry["modules"]
    by_id = {module.get("module_id", module.get("id")): module for module in modules}
    assert by_id["08_compute_load_metrics"]["status"] == "implemented"
    for module_id in IMPLEMENTED_AFTER_LOAD_METRICS:
        assert by_id[module_id]["status"] == "implemented"
    assert by_id["14_build_coach_context"]["status"] == "planned"
    for module in modules:
        module_id = module.get("module_id", module.get("id"))
        if module_id.startswith("20_"):
            assert module["status"] == "planned"


