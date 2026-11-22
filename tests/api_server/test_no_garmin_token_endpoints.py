import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_no_token_endpoints():
    p=json.loads((ROOT/"config/dashboard_snapshot_api_policy_v1.json").read_text(encoding="utf-8"))
    paths={e["path"] for e in p["endpoints"]}
    assert all("token" not in path and "garmin" not in path for path in paths)
