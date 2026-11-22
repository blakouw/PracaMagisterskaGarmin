from .helpers09 import output, read_json, run_module, setup_root, base_record


def test_quality_report_counts_methods(tmp_path):
    root = setup_root(tmp_path, records=[base_record(), base_record(date="2026-01-02", hrv_baseline_balanced_low_ms=None, hrv_baseline_balanced_upper_ms=None, acwr_ewma=None)])
    assert run_module(root) == 0
    report = read_json(output(root, "readiness_quality_report.json"))
    assert report["score_availability"]["computed_score_count"] == 2
    assert report["component_availability"]["hrv"]["methods_used"]["relative_to_weekly_average"] == 1
    assert report["component_availability"]["load_balance"]["methods_used"]["acwr_rolling"] == 1
