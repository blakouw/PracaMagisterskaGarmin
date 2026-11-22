from .helpers12 import full_fixture_records, read_json, run_module, setup_root


def test_schema(tmp_path):
    components, weights = full_fixture_records()
    root = setup_root(tmp_path, components=components, weights=weights)
    assert run_module(root) == 0
    schema = read_json(root / "data/pipeline/12_compute_pws_score/pws_score_schema.json")
    assert schema["schema_version"] == "pws_score_schema_v1"
    assert schema["weight_source"] == "11_compute_pws_weights.deterministic_effective_weights"
