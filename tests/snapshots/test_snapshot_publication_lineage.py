from snapshot16_fixtures import write_dashboard_fixture, run_module, publication, current, history_dir, read_json_file

def test_snapshot_publication_lineage(tmp_path, snapshot_module):
    write_dashboard_fixture(tmp_path)
    run_module(tmp_path, snapshot_module)
    lineage = read_json_file(tmp_path / "data/pipeline/16_persist_local_snapshot/snapshot_publication_lineage.json")
    assert lineage["publication_transformation"]["content_modified"] is False
    assert lineage["forbidden_action_confirmation"]["api_server_implemented"] is False
