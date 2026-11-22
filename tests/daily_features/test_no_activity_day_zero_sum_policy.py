from helpers07 import setup_root, run_module, output, activity
def test_no_activity_day_has_zero_sums_and_null_means(tmp_path):
    root = setup_root(tmp_path, activities=[activity("a1", "2026-01-01")])
    assert run_module(root) == 0
    row = output(root)["records"][1]
    assert row["activity_count"] == 0
    assert row["activity_total_duration_seconds"] == 0
    assert row["activity_duration_weighted_average_power_w"] is None
