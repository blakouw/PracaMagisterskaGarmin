import json
from pathlib import Path


def test_policy_shape():
    policy = json.loads((Path(__file__).resolve().parents[2] / "config/pws_score_policy_v1.json").read_text(encoding="utf-8"))
    assert policy["policy_version"] == "pws_score_policy_v1"
    assert policy["score_name"] == "pws_deterministic"
    assert policy["input_weight_policy"]["allowed_weight_source_only"] == "11_compute_pws_weights.deterministic_effective_weights"
    assert policy["future_llm_assisted_path"]["implemented_in_this_module"] is False
