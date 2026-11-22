from snapshotapi_fixtures import load_ctx

def test_api_loads_snapshot_once_at_startup(tmp_path, api_app_module):
    ctx = load_ctx(tmp_path, api_app_module)
    current = tmp_path / "data/published/dashboard_snapshots/current/dashboard_payload.json"
    current.write_text("{bad-json", encoding="utf-8")
    code, payload = api_app_module.handle_get(ctx, "/api/v1/dashboard")
    assert code == 200
    assert payload["metadata"]["latest_date"] == "2026-01-03"
