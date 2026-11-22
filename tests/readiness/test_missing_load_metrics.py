from .helpers09 import output, read_json, run_module, setup_root


def test_missing_load_metrics_blocks(tmp_path):
    root = setup_root(tmp_path, write_load=False)
    assert run_module(root) == 1
    manifest = read_json(output(root, "run_manifest.json"))
    assert manifest["domain_status"] == "blocked_missing_load_metrics"
    errors = read_json(output(root, "errors.json"))["errors"]
    assert any(error["code"] == "LOAD_METRICS_NOT_FOUND" for error in errors)


def test_not_ready_load_metrics_blocks(tmp_path):
    root = setup_root(tmp_path, ready=False)
    assert run_module(root) == 1
    manifest = read_json(output(root, "run_manifest.json"))
    assert manifest["domain_status"] == "blocked_load_metrics_not_ready"
