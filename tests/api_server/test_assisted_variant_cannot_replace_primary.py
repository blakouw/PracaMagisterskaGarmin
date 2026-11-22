from snapshotapi_fixtures import load_ctx

def test_assisted_variant_cannot_replace_primary(tmp_path, api_app_module):
    ctx = load_ctx(tmp_path, api_app_module, assisted=True, assisted_bad=True)
    assert any(e["code"] == "ASSISTED_VARIANT_CONTRACT_VIOLATION" for e in ctx.errors)
