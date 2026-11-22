from .helpers12 import component_record, read_json, run_module, setup_root, weight_record


def test_orphan_component_dates_reported(tmp_path):
    components = [component_record("2026-01-01"), component_record("2026-01-02")]
    weights = [weight_record("2026-01-01")]
    root = setup_root(tmp_path, components=components, weights=weights)
    assert run_module(root) == 0
    q = read_json(root / "data/pipeline/12_compute_pws_score/pws_score_quality_report.json")
    assert q["input_contract_validation"]["orphan_component_dates"] == ["2026-01-02"]
