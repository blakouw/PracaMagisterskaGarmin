from .helpers12 import component_record, read_json, run_module, setup_root, weight_record


def test_component_score_mismatch_is_reported(tmp_path):
    components = [component_record("2026-01-01", lq=99)]
    weights = [weight_record("2026-01-01", lq=100)]
    root = setup_root(tmp_path, components=components, weights=weights)
    assert run_module(root) == 0
    q = read_json(root / "data/pipeline/12_compute_pws_score/pws_score_quality_report.json")
    assert q["input_contract_validation"]["component_score_mismatches_between_modules"]
