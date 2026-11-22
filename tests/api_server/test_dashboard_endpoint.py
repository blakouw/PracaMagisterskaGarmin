from snapshotapi_fixtures import load_ctx

def test_dashboard_endpoint(tmp_path, api_app_module):
    ctx = load_ctx(tmp_path, api_app_module)
    code, payload = api_app_module.handle_get(ctx, "/api/v1/dashboard")
    assert code == 200
    assert payload["current_state"]["primary_pws"]["score_type"] == "deterministic"
