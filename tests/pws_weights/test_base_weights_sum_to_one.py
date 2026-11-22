import json
from pathlib import Path


def test_base_weights_sum_to_one():
    policy = json.loads((Path(__file__).resolve().parents[2] / "config/pws_weights_policy_v1.json").read_text(encoding="utf-8"))
    assert policy["base_weights"] == {"LQ": 0.20, "REC": 0.35, "CAP": 0.15, "VS": 0.30}
    assert abs(sum(policy["base_weights"].values()) - 1.0) < 1e-12
