import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def test_snapshot_read_only_endpoint_contract_with_ephemeral_chat():
    p = json.loads((ROOT / "config/dashboard_snapshot_api_policy_v1.json").read_text(encoding="utf-8"))
    endpoint_methods = {e["path"]: e["method"] for e in p["endpoints"]}
    assert endpoint_methods["/api/v1/dashboard/chat"] == "POST"
    assert all(method == "GET" for path, method in endpoint_methods.items() if path != "/api/v1/dashboard/chat")
    assert p["http_policy"]["read_only"] is True
    assert p["http_policy"]["chat_endpoint_modifies_snapshot"] is False
    assert p["http_policy"]["chat_endpoint_triggers_pipeline"] is False
