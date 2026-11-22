from .helpers12 import full_fixture_records, output, read_json, run_module, setup_root


def test_json_output(tmp_path):
    components, weights = full_fixture_records()
    root = setup_root(tmp_path, components=components, weights=weights)
    assert run_module(root) == 0
    payload = read_json(output(root))
    assert payload["module_id"] == "12_compute_pws_score"
    assert payload["score_name"] == "pws_deterministic"
    assert payload["ready_for_next_module"] is True
