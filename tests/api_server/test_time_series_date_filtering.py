from snapshotapi_fixtures import load_ctx

def test_time_series_date_filtering(tmp_path, api_app_module):
    ctx = load_ctx(tmp_path, api_app_module)
    code, payload = api_app_module.handle_get(ctx, "/api/v1/dashboard/time-series", {"date_from":"2026-01-02", "date_to":"2026-01-03"})
    assert code == 200
    assert [r["date"] for r in payload["records"]] == ["2026-01-02", "2026-01-03"]
