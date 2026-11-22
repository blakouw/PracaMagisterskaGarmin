from snapshot16_fixtures import write_dashboard_fixture, run_module, publication, current, history_dir, read_json_file

def test_history_preserved_on_current_failure(tmp_path, snapshot_module, monkeypatch):
    write_dashboard_fixture(tmp_path)
    monkeypatch.setenv("SNAPSHOT_SIMULATE_CURRENT_PUBLISH_FAILURE", "1")
    run_module(tmp_path, snapshot_module)
    pub = publication(tmp_path)
    assert pub["publication_result"]["history_snapshot_written"] is True
    assert history_dir(tmp_path, pub["snapshot_id"]).is_dir()
    assert pub["ready_for_next_module"] is False
