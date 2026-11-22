from snapshotapi_fixtures import load_ctx

def test_disclosures_endpoint(tmp_path, api_app_module):
    ctx = load_ctx(tmp_path, api_app_module)
    code, payload = api_app_module.handle_get(ctx, "/api/v1/dashboard/disclosures")
    assert code == 200
    assert "primary_score" in payload
