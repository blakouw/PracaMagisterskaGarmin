import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_local_dashboard_ui_policy():
    policy = json.loads((ROOT / "config/local_dashboard_ui_policy_v1.json").read_text(encoding="utf-8"))
    assert policy["policy_version"] == "local_dashboard_ui_policy_v1"
    assert policy["source_api"]["module"] == "17_local_api_server"
    assert policy["source_api"]["base_path"] == "/api/v1"
    assert policy["source_api"]["development_proxy_target"] == "http://127.0.0.1:8765"
    assert policy["runtime"]["local_only"] is True
    assert policy["runtime"]["read_only"] is True
    assert policy["runtime"]["public_deployment_approved"] is False
    assert policy["presentation_policy"]["primary_score"]["required_score_type"] == "deterministic"
    assert policy["presentation_policy"]["optional_assisted_score"]["must_not_replace_primary_score"] is True
