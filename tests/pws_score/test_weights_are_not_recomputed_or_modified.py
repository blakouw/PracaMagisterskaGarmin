from .helpers12 import full_fixture_records, first_record, read_json, run_module, setup_root


def test_weights_are_not_recomputed_or_modified(tmp_path):
    components, weights = full_fixture_records()
    root = setup_root(tmp_path, components=components, weights=weights)
    assert run_module(root) == 0
    record = first_record(root)
    assert record["pws_deterministic_weights"] == weights[0]["deterministic_effective_weights"]
    lineage = read_json(root / "data/pipeline/12_compute_pws_score/pws_score_lineage.json")
    assert lineage["score_transformation"]["weights_recomputed"] is False
    assert lineage["score_transformation"]["weights_modified"] is False
