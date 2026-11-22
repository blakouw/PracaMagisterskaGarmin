from snapshotapi_fixtures import load_ctx

def test_time_series_invalid_query_parameters(tmp_path, api_app_module):
    ctx = load_ctx(tmp_path, api_app_module)
    assert api_app_module.handle_get(ctx, "/api/v1/dashboard/time-series", {"date_from":"bad"})[0] == 400
    assert api_app_module.handle_get(ctx, "/api/v1/dashboard/time-series", {"limit":"10001"})[0] == 400
