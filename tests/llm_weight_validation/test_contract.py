import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
def test_contract():
    c = json.loads((ROOT/"pipeline/13_validate_llm_weight_influence/contract.json").read_text(encoding="utf-8"))
    assert c["status"] == "implemented"
    assert c["optional"] is True
    assert "send_full_private_history_in_one_llm_request" in c["prohibited_responsibilities"]
    assert "batch_process_historical_dates_with_llm" not in c["prohibited_responsibilities"]
    assert "data/pipeline/13_validate_llm_weight_influence/llm_conversation_index.json" in c["outputs"]
    assert "data/pipeline/13_validate_llm_weight_influence/llm_conversations/<date>.json" in c["outputs"]
    registry = json.loads((ROOT/"config/pipeline_modules.json").read_text(encoding="utf-8"))
    by_id = {m["id"]: m for m in registry["modules"]}
    assert by_id["13_validate_llm_weight_influence"]["status"] == "implemented"
    assert by_id["14_build_coach_context"]["status"] == "planned"
