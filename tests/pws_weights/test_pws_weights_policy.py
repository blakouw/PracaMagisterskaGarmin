from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[2]


def test_policy_shape_and_guardrails():
    policy = json.loads((ROOT / "config/pws_weights_policy_v1.json").read_text(encoding="utf-8"))
    assert policy["policy_version"] == "pws_weights_policy_v1"
    assert set(policy["components"]) == {"LQ", "REC", "CAP", "VS"}
    limits = policy["future_llm_adjustment_guardrails"]["adjustment_limits"]
    assert limits["maximum_absolute_delta_per_component"] == 0.20
    assert limits["maximum_total_positive_weight_shift"] == 0.20
    assert limits["maximum_total_absolute_delta"] == 0.40
    assert limits["unavailable_component_weight_must_remain_zero"] is True
    assert policy["future_llm_adjustment_guardrails"]["this_module_must_not_call_llm"] is True
