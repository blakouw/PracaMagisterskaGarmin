from helpers07 import setup_root, run_module, output, activity
def test_sums_for_multiple_activities(tmp_path):
    acts = [activity("a1", distance=5, duration=100, calories=50, z1=1), activity("a2", distance=7, duration=200, calories=70, z1=2)]
    root = setup_root(tmp_path, activities=acts)
    assert run_module(root) == 0
    row = output(root)["records"][0]
    assert row["activity_count"] == 2
    assert row["activity_total_distance_km"] == 12
    assert row["activity_total_duration_seconds"] == 300
    assert row["activity_total_calories"] == 120
    assert row["activity_total_hr_zone_1_seconds"] == 3
