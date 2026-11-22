from helpers07 import setup_root, run_module, output, activity
def test_only_daily_dates_create_rows(tmp_path):
    root = setup_root(tmp_path, activities=[activity("a1", "2026-01-01"), activity("orphan", "2026-01-03")])
    assert run_module(root) == 0
    records = output(root)["records"]
    assert [r["date"] for r in records] == ["2026-01-01", "2026-01-02"]
    assert output(root, "daily_features_quality_report.json")["orphan_activity_dates"] == [{"date": "2026-01-03", "activities_count": 1}]
