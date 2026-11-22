from helpers07 import setup_root, run_module, output
def test_missing_daily_records_blocks(tmp_path):
    root = setup_root(tmp_path, write_daily=False, write_activity=False)
    assert run_module(root) == 1
    assert output(root, "run_manifest.json")["domain_status"] == "blocked_missing_daily_records"
