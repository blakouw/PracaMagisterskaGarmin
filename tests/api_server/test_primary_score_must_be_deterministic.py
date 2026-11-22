from snapshotapi_fixtures import load_ctx

def test_primary_score_must_be_deterministic(tmp_path, api_app_module):
    ctx = load_ctx(tmp_path, api_app_module, primary_type="llm_assisted")
    assert any(e["code"] == "PRIMARY_SCORE_NOT_DETERMINISTIC" for e in ctx.errors)
