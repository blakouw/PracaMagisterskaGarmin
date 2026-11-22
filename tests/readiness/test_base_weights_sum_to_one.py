import json
from pathlib import Path


def test_base_weights_sum_to_one():
    policy = json.loads((Path(__file__).resolve().parents[2] / "config/readiness_policy_v1.json").read_text(encoding="utf-8"))
    assert policy["base_weights"] == {
        "hrv": 0.36363636363636365,
        "stress": 0.2727272727272727,
        "rhr": 0.18181818181818182,
        "load_balance": 0.18181818181818182,
    }
    assert sum(policy["base_weights"].values()) == 1.0
