from snapshotapi_fixtures import load_ctx

def test_api_does_not_recompute_values(tmp_path, api_app_module):
    ctx = load_ctx(tmp_path, api_app_module)
    code, payload = api_app_module.handle_get(ctx, "/api/v1/dashboard")
    assert code == 200
    assert payload["time_series"][1]["pws_deterministic"] == 75.34
