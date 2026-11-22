from snapshotapi_fixtures import load_ctx

def test_snapshot_not_ready(tmp_path, api_app_module):
    ctx = load_ctx(tmp_path, api_app_module, payload_ready=False)
    assert ctx.ready is False
    assert any(e["code"] == "CURRENT_SNAPSHOT_NOT_READY" for e in ctx.errors)
