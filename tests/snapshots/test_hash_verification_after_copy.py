from snapshot16_fixtures import write_dashboard_fixture, run_module, publication, current, history_dir, read_json_file

def test_hash_verification_after_copy(tmp_path, snapshot_module):
    write_dashboard_fixture(tmp_path, parquet=True)
    run_module(tmp_path, snapshot_module)
    hashes = read_json_file(current(tmp_path) / "snapshot_source_hashes.json")
    assert hashes["all_required_hashes_verified"] is True
    assert hashes["all_present_optional_hashes_verified"] is True
