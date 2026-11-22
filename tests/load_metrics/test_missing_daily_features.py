from .helpers08 import output, read_json, run_module, setup_root


def test_missing_daily_features_blocks(tmp_path):
    root = setup_root(tmp_path, write_features=False)
    assert run_module(root) == 1
    manifest = read_json(output(root, "run_manifest.json"))
    errors = read_json(output(root, "errors.json"))
    assert manifest["domain_status"] == "blocked_missing_daily_features"
    assert any(error["code"] == "DAILY_FEATURES_NOT_FOUND" for error in errors["errors"])
