from snapshotapi_fixtures import load_ctx

def test_snapshot_manifest_endpoint(tmp_path, api_app_module):
    ctx = load_ctx(tmp_path, api_app_module)
    code, payload = api_app_module.handle_get(ctx, "/api/v1/snapshot/manifest")
    assert code == 200
    assert payload["primary_score_policy"]["score_type"] == "deterministic"
