from snapshot16_fixtures import write_dashboard_fixture, run_module, publication, current, history_dir, read_json_file

def test_primary_score_must_be_deterministic(tmp_path, snapshot_module):
    write_dashboard_fixture(tmp_path, primary_type="llm_assisted")
    assert run_module(tmp_path, snapshot_module) == "blocked_invalid_primary_score_contract"
