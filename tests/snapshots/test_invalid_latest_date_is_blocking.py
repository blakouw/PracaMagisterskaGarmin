from snapshot16_fixtures import write_dashboard_fixture, run_module, publication, current, history_dir, read_json_file

def test_invalid_latest_date_blocks(tmp_path, snapshot_module):
    write_dashboard_fixture(tmp_path, latest_date="not-a-date")
    assert run_module(tmp_path, snapshot_module) == "blocked_invalid_dashboard_latest_date"
