from snapshot16_fixtures import write_dashboard_fixture, run_module, publication, current, history_dir, read_json_file

def test_snapshot_publication_json_output(tmp_path, snapshot_module):
    write_dashboard_fixture(tmp_path)
    run_module(tmp_path, snapshot_module)
    pub = publication(tmp_path)
    assert pub["status"] == "published_without_optional_parquet"
    assert pub["payload_preservation_confirmation"]["analytical_values_recomputed"] is False
