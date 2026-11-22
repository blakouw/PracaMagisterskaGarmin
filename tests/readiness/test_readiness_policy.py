import json
from pathlib import Path


def test_readiness_policy_core_rules():
    root = Path(__file__).resolve().parents[2]
    policy = json.loads((root / "config/readiness_policy_v1.json").read_text(encoding="utf-8"))
    assert policy["policy_version"] == "readiness_policy_v1"
    assert policy["score_name"] == "readiness_score"
    assert policy["missing_component_policy"]["do_not_substitute_zero"] is True
    assert policy["missing_component_policy"]["minimum_available_base_weight_sum_for_final_score"] == 0.50
    assert policy["missing_component_policy"]["minimum_available_components_for_final_score"] == 3
    assert abs(sum(policy["base_weights"].values()) - 1.0) < 1e-9
