import json
from pathlib import Path


def test_cap_has_lowest_weight_with_rationale():
    policy = json.loads((Path(__file__).resolve().parents[2] / "config/pws_weights_policy_v1.json").read_text(encoding="utf-8"))
    assert policy["base_weights"]["CAP"] == min(policy["base_weights"].values())
    assert any("Capacity receives the lowest base weight" in item for item in policy["design_rationale"])
