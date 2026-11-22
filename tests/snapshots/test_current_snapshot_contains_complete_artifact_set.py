from snapshot16_fixtures import write_dashboard_fixture, run_module, publication, current, history_dir, read_json_file

def test_current_snapshot_complete(tmp_path, snapshot_module):
    write_dashboard_fixture(tmp_path)
    run_module(tmp_path, snapshot_module)
    for name in snapshot_module.REQUIRED_SOURCE_FILES + snapshot_module.GENERATED_SNAPSHOT_FILES:
        assert (current(tmp_path) / name).is_file(), name
