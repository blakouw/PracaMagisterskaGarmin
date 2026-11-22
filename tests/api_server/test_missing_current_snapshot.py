def test_missing_current_snapshot(tmp_path, api_app_module):
    ctx = api_app_module.load_snapshot(tmp_path)
    code, payload = api_app_module.handle_get(ctx, "/api/v1/health")
    assert code == 200
    assert payload["snapshot_available"] is False
