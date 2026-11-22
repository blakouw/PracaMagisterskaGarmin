from snapshotapi_fixtures import load_ctx

def test_invalid_snapshot_json(tmp_path, api_app_module):
    ctx = load_ctx(tmp_path, api_app_module, invalid_json="snapshot_status.json")
    assert any(e["code"] == "CURRENT_SNAPSHOT_JSON_INVALID" for e in ctx.errors)
