from snapshot16_fixtures import write_dashboard_fixture, run_module, publication, current, history_dir, read_json_file

def test_history_snapshot_written(tmp_path, snapshot_module):
    write_dashboard_fixture(tmp_path)
    run_module(tmp_path, snapshot_module)
    pub = publication(tmp_path)
    assert history_dir(tmp_path, pub["snapshot_id"]).is_dir()
