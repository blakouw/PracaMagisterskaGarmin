from snapshotapi_fixtures import load_ctx

def test_missing_required_snapshot_file(tmp_path, api_app_module):
    ctx = load_ctx(tmp_path, api_app_module, missing="snapshot_status.json")
    assert ctx.ready is False
    assert any(e["code"] == "CURRENT_SNAPSHOT_REQUIRED_FILE_NOT_FOUND" for e in ctx.errors)
