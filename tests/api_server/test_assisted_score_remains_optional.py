from snapshotapi_fixtures import load_ctx

def test_assisted_score_remains_optional(tmp_path, api_app_module):
    ctx = load_ctx(tmp_path, api_app_module, assisted=True)
    code, payload = api_app_module.handle_get(ctx, "/api/v1/dashboard/current-state")
    assert code == 200
    assert payload["primary_pws"]["score_type"] == "deterministic"
    assert payload["optional_assisted_pws"]["score_type"] == "llm_assisted"
    assert payload["optional_assisted_pws"]["must_not_replace_primary_score"] is True
