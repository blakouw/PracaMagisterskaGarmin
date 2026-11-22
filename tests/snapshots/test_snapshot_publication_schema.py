from snapshot16_fixtures import write_dashboard_fixture, run_module, publication, current, history_dir, read_json_file

def test_snapshot_publication_schema(tmp_path, snapshot_module):
    write_dashboard_fixture(tmp_path)
    run_module(tmp_path, snapshot_module)
    schema = read_json_file(tmp_path / "data/pipeline/16_persist_local_snapshot/snapshot_publication_schema.json")
    assert schema["primary_score_policy"]["score_type"] == "deterministic"
    assert schema["recomputation_policy"]["llm_called"] is False
