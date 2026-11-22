from snapshot16_fixtures import write_dashboard_fixture, run_module, publication, current, history_dir, read_json_file

def test_payload_not_ready_blocks(tmp_path, snapshot_module):
    write_dashboard_fixture(tmp_path, ready=False)
    assert run_module(tmp_path, snapshot_module) == "blocked_dashboard_payload_not_ready"
