from .helpers09 import first_record, run_module, setup_root, base_record


def test_insufficient_when_fewer_than_three_components(tmp_path):
    record = base_record(hrv_last_night_avg_ms=None, hrv_weekly_avg_ms=None, hrv_baseline_balanced_low_ms=None, hrv_baseline_balanced_upper_ms=None, resting_hr_bpm=None, resting_hr_baseline_bpm=None, acwr_ewma=None, acwr_rolling=None)
    root = setup_root(tmp_path, records=[record])
    assert run_module(root) == 0
    row = first_record(root)
    assert row["available_components_count"] == 1
    assert row["readiness_score"] is None
    assert row["readiness_status"] == "insufficient_data"


def test_insufficient_when_weight_sum_below_minimum(tmp_path):
    record = base_record(hrv_last_night_avg_ms=None, hrv_weekly_avg_ms=None, hrv_baseline_balanced_low_ms=None, hrv_baseline_balanced_upper_ms=None, avg_stress=None)
    root = setup_root(tmp_path / "weight", records=[record])
    assert run_module(root) == 0
    row = first_record(root)
    assert row["available_components_count"] == 2
    assert row["available_base_weight_sum"] == 0.3636
    assert row["readiness_score"] is None
