from snapshot16_fixtures import write_dashboard_fixture, run_module, publication, current, history_dir, read_json_file

def test_snapshot_source_hashes_output(tmp_path, snapshot_module):
    write_dashboard_fixture(tmp_path)
    run_module(tmp_path, snapshot_module)
    hashes = read_json_file(current(tmp_path) / "snapshot_source_hashes.json")
    assert hashes["hash_algorithm"] == "sha256"
    assert len(hashes["files"]) == 6
