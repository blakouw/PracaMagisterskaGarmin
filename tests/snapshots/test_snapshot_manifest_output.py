from snapshot16_fixtures import write_dashboard_fixture, run_module, publication, current, history_dir, read_json_file

def test_snapshot_manifest_output(tmp_path, snapshot_module):
    write_dashboard_fixture(tmp_path, assisted_available=True)
    run_module(tmp_path, snapshot_module)
    manifest = read_json_file(current(tmp_path) / "snapshot_manifest.json")
    assert manifest["publisher_module_id"] == "16_persist_local_snapshot"
    assert manifest["primary_score_policy"]["score_type"] == "deterministic"
    assert manifest["optional_assisted_variant"]["must_not_replace_primary_score"] is True
