from .helpers12 import full_fixture_records, read_json, run_module, setup_root


def test_lineage_report(tmp_path):
    components, weights = full_fixture_records()
    root = setup_root(tmp_path, components=components, weights=weights)
    assert run_module(root) == 0
    lineage = read_json(root / "data/pipeline/12_compute_pws_score/pws_score_lineage.json")
    assert lineage["score_transformation"]["weights_recomputed"] is False
    assert lineage["future_llm_boundary"]["llm_called_in_this_module"] is False
