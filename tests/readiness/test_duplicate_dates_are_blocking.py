from .helpers09 import base_record, output, read_json, run_module, setup_root


def test_duplicate_dates_block(tmp_path):
    root = setup_root(tmp_path, records=[base_record(), base_record()])
    assert run_module(root) == 1
    manifest = read_json(output(root, "run_manifest.json"))
    assert manifest["domain_status"] == "blocked_duplicate_dates"
