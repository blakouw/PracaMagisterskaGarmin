from snapshot16_fixtures import write_dashboard_fixture, run_module, publication, current, history_dir, read_json_file

def test_optional_parquet_absence_non_blocking(tmp_path, snapshot_module):
    write_dashboard_fixture(tmp_path)
    assert run_module(tmp_path, snapshot_module) == "published_without_optional_parquet"
    assert publication(tmp_path)["ready_for_next_module"] is True
