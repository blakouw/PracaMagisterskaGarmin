from helpers07 import setup_root, run_module, output, activity
def test_quality_report_counts(tmp_path):
    root = setup_root(tmp_path, activities=[activity("a1")])
    assert run_module(root) == 0
    q = output(root, "daily_features_quality_report.json")
    assert q["records_count"] == 2
    assert q["dates_with_activities_count"] == 1
    assert "feature_coverage" in q
    assert q["ready_for_next_module"] is True
