from snapshotapi_fixtures import load_ctx

def test_health_valid(tmp_path, api_app_module):
    ctx = load_ctx(tmp_path, api_app_module)
    code, payload = api_app_module.handle_get(ctx, "/api/v1/health")
    assert code == 200
    assert payload["status"] == "ok"
    assert payload["primary_score_type"] == "deterministic"
