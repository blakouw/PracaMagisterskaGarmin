import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def test_api_policy():
    p = json.loads((ROOT / "config/dashboard_snapshot_api_policy_v1.json").read_text(encoding="utf-8"))
    assert p["policy_version"] == "dashboard_snapshot_api_policy_v1"
    assert p["runtime"]["default_host"] == "127.0.0.1"
    assert p["runtime"]["approved_for_public_exposure"] is False
    assert p["http_policy"]["allowed_methods"] == ["GET", "POST"]
    assert p["http_policy"]["allowed_post_endpoints"] == ["/api/v1/dashboard/chat"]
    assert p["privacy_policy"]["chat_must_use_local_llm_endpoint_only"] is True
