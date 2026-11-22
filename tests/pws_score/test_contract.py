import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_contract_and_registry_status():
    contract = json.loads((ROOT / "pipeline/12_compute_pws_score/contract.json").read_text(encoding="utf-8"))
    assert contract["module_id"] == "12_compute_pws_score"
    assert contract["status"] == "implemented"
    assert "call_llm" in contract["prohibited_responsibilities"]
    registry = json.loads((ROOT / "config/pipeline_modules.json").read_text(encoding="utf-8"))
    by_id = {module["id"]: module for module in registry["modules"]}
    assert by_id["12_compute_pws_score"]["status"] == "implemented"
    for module in registry["modules"]:
        if module["id"] in {"15_build_dashboard_payload", "16_persist_local_snapshot", "17_local_api_server", "18_angular_dashboard_ui", "19_packaging_windows"}:
            assert module["status"] == "implemented"
        elif module["order"] > 13:
            assert module["status"] == "planned"



