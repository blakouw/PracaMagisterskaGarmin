from .helpers12 import partial_fixture_records, read_json, run_module, setup_root


def test_quality_report(tmp_path):
    components, weights = partial_fixture_records()
    root = setup_root(tmp_path, components=components, weights=weights)
    assert run_module(root) == 0
    q = read_json(root / "data/pipeline/12_compute_pws_score/pws_score_quality_report.json")
    assert q["coverage_tiers"]["partial_eligible"] == 1
    assert q["llm_path"]["llm_called"] is False
