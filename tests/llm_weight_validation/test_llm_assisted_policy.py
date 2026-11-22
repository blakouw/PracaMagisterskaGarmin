import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
def test_policy():
    p=json.loads((ROOT/"config/llm_assisted_pws_policy_v1.json").read_text(encoding="utf-8"))
    assert p["module_optional"] is True
    assert p["execution_policy"]["maximum_llm_calls_per_eligible_date"] == 1
    assert p["execution_policy"]["maximum_llm_calls_per_run"] == "number_of_eligible_dates"
    assert p["execution_policy"]["default_target_selection"] == "all_eligible_dates_in_ascending_order"
    assert p["validation_policy"]["maximum_absolute_delta_per_component"] == 0.20
    assert p["validation_policy"]["maximum_total_positive_weight_shift"] == 0.20
    assert p["validation_policy"]["maximum_total_absolute_delta"] == 0.40
    assert p["execution_policy"]["historical_batch_processing_allowed"] is True
