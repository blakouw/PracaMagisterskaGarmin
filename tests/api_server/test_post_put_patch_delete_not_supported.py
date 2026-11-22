import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def test_only_approved_chat_post_is_supported():
    p = json.loads((ROOT / "config/dashboard_snapshot_api_policy_v1.json").read_text(encoding="utf-8"))
    assert p["http_policy"]["allowed_methods"] == ["GET", "POST"]
    assert p["http_policy"]["allowed_post_endpoints"] == ["/api/v1/dashboard/chat"]
    assert set(p["http_policy"]["disallowed_methods"]) >= {"PUT", "PATCH", "DELETE"}
    assert p["http_policy"]["chat_endpoint_modifies_snapshot"] is False
    assert p["http_policy"]["chat_endpoint_triggers_pipeline"] is False
