import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def test_policy_contract():
    policy = json.loads((ROOT / "config/dashboard_snapshot_policy_v1.json").read_text(encoding="utf-8"))
    assert policy["policy_version"] == "dashboard_snapshot_policy_v1"
    assert policy["source_module"] == "15_build_dashboard_payload"
    assert policy["hash_policy"]["algorithm"] == "sha256"
    assert policy["retention_policy"]["automatic_history_deletion_enabled"] is False
    assert "implement_api_server" in policy["prohibited_responsibilities"]
