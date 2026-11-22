import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_contract_and_registry_status():
    contract = json.loads((ROOT / "pipeline/09_compute_readiness/contract.json").read_text(encoding="utf-8"))
    assert contract["module_id"] == "09_compute_readiness"
    assert contract["status"] == "implemented"
    assert contract["run_command"] == "pipeline/09_compute_readiness/run.bat"
    assert "08_compute_load_metrics" in contract["depends_on"]
    assert "calculate_pws_components" in contract["prohibited_responsibilities"]
    registry = json.loads((ROOT / "config/pipeline_modules.json").read_text(encoding="utf-8"))
    modules = registry["modules"]
    by_id = {module["id"]: module for module in modules}
    assert by_id["09_compute_readiness"]["status"] == "implemented"
    assert by_id["10_compute_pws_components"]["status"] == "implemented"
    assert by_id["11_compute_pws_weights"]["status"] == "implemented"
    assert by_id["12_compute_pws_score"]["status"] == "implemented"
    for module in modules[14:]:
        expected = "implemented" if module["id"] in {"15_build_dashboard_payload", "16_persist_local_snapshot", "17_local_api_server", "18_angular_dashboard_ui", "19_packaging_windows"} else "planned"
        assert module["status"] == expected, module["id"]


