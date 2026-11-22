from snapshot16_fixtures import write_dashboard_fixture, run_module, publication, current, history_dir, read_json_file

def test_snapshot_status_output(tmp_path, snapshot_module):
    write_dashboard_fixture(tmp_path, primary_score=None)
    run_module(tmp_path, snapshot_module)
    status = read_json_file(current(tmp_path) / "snapshot_status.json")
    assert status["primary_pws"]["score_type"] == "deterministic"
    assert status["primary_pws"]["score"] is None
