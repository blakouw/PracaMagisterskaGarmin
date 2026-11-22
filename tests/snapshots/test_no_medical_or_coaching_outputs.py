from snapshot16_fixtures import write_dashboard_fixture, run_module, read_json_file

def test_no_medical_or_coaching_outputs(tmp_path, snapshot_module):
    write_dashboard_fixture(tmp_path)
    run_module(tmp_path, snapshot_module)
    lineage = read_json_file(tmp_path / "data/pipeline/16_persist_local_snapshot/snapshot_publication_lineage.json")
    forbidden = lineage["forbidden_action_confirmation"]
    assert forbidden["medical_diagnosis_generated"] is False
    assert forbidden["training_prescription_generated"] is False
    assert forbidden["api_server_implemented"] is False
    assert forbidden["ui_implemented"] is False
