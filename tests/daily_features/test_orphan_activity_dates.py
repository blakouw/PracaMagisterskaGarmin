from helpers07 import setup_root, run_module, output, activity
def test_orphan_dates_are_reported_not_joined(tmp_path):
    root = setup_root(tmp_path, activities=[activity("a3", "2026-01-03")])
    assert run_module(root) == 0
    q = output(root, "daily_features_quality_report.json")
    assert q["orphan_activity_dates"][0]["date"] == "2026-01-03"
    assert all(r["date"] != "2026-01-03" for r in output(root)["records"])
