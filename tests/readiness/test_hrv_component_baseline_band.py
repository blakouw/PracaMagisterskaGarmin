from .helpers09 import first_record, run_module, setup_root, base_record


def test_hrv_baseline_band_balanced_and_low(tmp_path):
    root = setup_root(tmp_path, records=[base_record(hrv_last_night_avg_ms=60, hrv_baseline_balanced_low_ms=50, hrv_baseline_balanced_upper_ms=70)])
    assert run_module(root) == 0
    assert first_record(root)["hrv_readiness_score"] == 100
    assert first_record(root)["hrv_readiness_method"] == "baseline_band"

    root2 = setup_root(tmp_path / "low", records=[base_record(hrv_last_night_avg_ms=40, hrv_baseline_balanced_low_ms=50, hrv_baseline_balanced_upper_ms=70)])
    assert run_module(root2) == 0
    assert first_record(root2)["hrv_readiness_score"] == 80
