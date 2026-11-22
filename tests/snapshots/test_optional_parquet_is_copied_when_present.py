from snapshot16_fixtures import write_dashboard_fixture, run_module, publication, current, history_dir, read_json_file

def test_optional_parquet_copied(tmp_path, snapshot_module):
    write_dashboard_fixture(tmp_path, parquet=True)
    assert run_module(tmp_path, snapshot_module) == "published"
    pub = publication(tmp_path)
    assert (history_dir(tmp_path, pub["snapshot_id"]) / "dashboard_time_series.parquet").is_file()
    assert (current(tmp_path) / "dashboard_time_series.parquet").is_file()
