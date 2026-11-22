from .helpers09 import first_record, run_module, setup_root, base_record


def test_final_score_partial_coverage_renormalizes_weights(tmp_path):
    record = base_record(resting_hr_bpm=None, resting_hr_baseline_bpm=None)
    root = setup_root(tmp_path, records=[record])
    assert run_module(root) == 0
    row = first_record(root)
    assert row["available_readiness_components"] == ["hrv", "stress", "load_balance"]
    assert row["available_base_weight_sum"] == 0.8182
    assert row["effective_component_weights"]["hrv"] == round(4 / 9, 4)
    assert row["readiness_score"] == 90.0
