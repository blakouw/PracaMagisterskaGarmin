from .helpers10 import output, read_json, run_module, setup_root


def test_missing_load_metrics_blocks(tmp_path):
    root = setup_root(tmp_path, write_load=False)
    assert run_module(root) == 1
    assert read_json(output(root, "run_manifest.json"))["domain_status"] == "blocked_missing_load_metrics"


def test_load_metrics_not_ready_blocks(tmp_path):
    root = setup_root(tmp_path, load_ready=False)
    assert run_module(root) == 1
    assert read_json(output(root, "run_manifest.json"))["domain_status"] == "blocked_load_metrics_not_ready"
