import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_policy():
    p=json.loads((ROOT/"config/dashboard_payload_policy_v1.json").read_text(encoding="utf-8"))
    assert p["policy_version"]=="dashboard_payload_policy_v1"
    assert p["primary_score_policy"]["primary_score_source"]=="pws_deterministic"
    assert p["primary_score_policy"]["assisted_score_must_never_replace_primary"] is True
    assert p["privacy_policy"]["payload_is_private"] is True

