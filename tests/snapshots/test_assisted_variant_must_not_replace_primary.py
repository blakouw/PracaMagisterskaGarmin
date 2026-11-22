from snapshot16_fixtures import write_dashboard_fixture, run_module, publication, current, history_dir, read_json_file

def test_assisted_variant_must_not_replace_primary(tmp_path, snapshot_module):
    write_dashboard_fixture(tmp_path, assisted_available=True, assisted_replaces=True)
    assert run_module(tmp_path, snapshot_module) == "blocked_assisted_score_contract_violation"
