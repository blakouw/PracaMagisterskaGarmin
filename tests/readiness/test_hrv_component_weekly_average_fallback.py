from .helpers09 import first_record, run_module, setup_root, base_record


def test_hrv_weekly_fallback(tmp_path):
    root = setup_root(tmp_path, records=[base_record(hrv_baseline_balanced_low_ms=None, hrv_baseline_balanced_upper_ms=None, hrv_last_night_avg_ms=50, hrv_weekly_avg_ms=100)])
    assert run_module(root) == 0
    row = first_record(root)
    assert row["hrv_readiness_score"] == 50
    assert row["hrv_readiness_method"] == "relative_to_weekly_average"


def test_hrv_unavailable_without_inputs(tmp_path):
    root = setup_root(tmp_path, records=[base_record(hrv_last_night_avg_ms=None, hrv_weekly_avg_ms=None, hrv_baseline_balanced_low_ms=None, hrv_baseline_balanced_upper_ms=None)])
    assert run_module(root) == 0
    assert first_record(root)["hrv_readiness_score"] is None
