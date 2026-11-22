import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_no_wildcard_cors():
    p=json.loads((ROOT/"config/dashboard_snapshot_api_policy_v1.json").read_text(encoding="utf-8"))
    assert p["cors_policy"]["enabled_by_default"] is False
    assert p["cors_policy"]["allow_wildcard_origins"] is False
