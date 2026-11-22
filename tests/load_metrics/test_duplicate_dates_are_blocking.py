from .helpers08 import make_records, output, read_json, run_module, setup_root


def test_duplicate_dates_block(tmp_path):
    records = make_records([100, 200], dates=["2026-01-01", "2026-01-01"])
    root = setup_root(tmp_path, records=records)
    assert run_module(root) == 1
    manifest = read_json(output(root, "run_manifest.json"))
    assert manifest["domain_status"] == "blocked_duplicate_dates"
