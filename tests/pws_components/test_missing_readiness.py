from .helpers10 import output, read_json, run_module, setup_root


def test_missing_readiness_blocks(tmp_path):
    root = setup_root(tmp_path, write_readiness=False)
    assert run_module(root) == 1
    assert read_json(output(root, "run_manifest.json"))["domain_status"] == "blocked_missing_readiness"


def test_readiness_not_ready_blocks(tmp_path):
    root = setup_root(tmp_path, readiness_ready=False)
    assert run_module(root) == 1
    assert read_json(output(root, "run_manifest.json"))["domain_status"] == "blocked_readiness_not_ready"
