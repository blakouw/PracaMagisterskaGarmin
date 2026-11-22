from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_packaging_policy_is_local_portable_and_private_data_free():
    policy = json.loads((ROOT / "config/windows_packaging_policy_v1.json").read_text(encoding="utf-8"))
    assert policy["policy_version"] == "windows_packaging_policy_v1"
    assert policy["runtime"]["host"] == "127.0.0.1"
    assert policy["runtime"]["port"] == 8765
    assert policy["runtime"]["host_override_allowed"] is False
    assert policy["runtime"]["public_deployment_approved"] is False
    assert policy["runtime"]["vite_dev_server_allowed_in_packaged_runtime"] is False
    assert policy["included_content_policy"]["include_production_ui_build"] is True
    assert policy["included_content_policy"]["include_vite_dev_server"] is False
    assert policy["included_content_policy"]["include_current_snapshot_data"] is False
    assert policy["privacy_policy"]["secrets_packaged"] is False
    assert policy["privacy_policy"]["tokens_packaged"] is False
