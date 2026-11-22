from snapshotapi_fixtures import load_ctx

def test_time_series_endpoint(tmp_path, api_app_module):
    ctx = load_ctx(tmp_path, api_app_module)
    code, payload = api_app_module.handle_get(ctx, "/api/v1/dashboard/time-series")
    assert code == 200
    assert payload["records_count"] == 3
