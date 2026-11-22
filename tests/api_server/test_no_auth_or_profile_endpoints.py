import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_no_auth_profile_endpoints():
    p=json.loads((ROOT/"config/dashboard_snapshot_api_policy_v1.json").read_text(encoding="utf-8"))
    paths={e["path"] for e in p["endpoints"]}
    assert all("login" not in path and "profile" not in path for path in paths)
