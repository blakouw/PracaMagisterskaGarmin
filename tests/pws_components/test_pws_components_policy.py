import json
from pathlib import Path


def test_policy_defines_components_and_no_final_pws():
    root = Path(__file__).resolve().parents[2]
    policy = json.loads((root / "config/pws_components_policy_v1.json").read_text(encoding="utf-8"))
    assert policy["policy_version"] == "pws_components_policy_v1"
    assert set(policy["components"]) == {"LQ", "REC", "CAP", "VS"}
    assert policy["missing_values_policy"]["do_not_compute_final_pws"] is True
    assert "pws_score" in policy["prohibited_outputs"]
