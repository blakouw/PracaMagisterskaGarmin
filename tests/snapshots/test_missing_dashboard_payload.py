from snapshot16_fixtures import write_dashboard_fixture, run_module, publication


def test_missing_dashboard_payload_blocks(tmp_path, snapshot_module):
    source = write_dashboard_fixture(tmp_path)
    (source / "dashboard_payload.json").unlink()
    assert run_module(tmp_path, snapshot_module) == "blocked_missing_dashboard_payload"
    assert publication(tmp_path)["ready_for_next_module"] is False
