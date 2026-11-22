from helpers07 import setup_root, run_module, output
def test_daily_only_build(tmp_path):
    root = setup_root(tmp_path, write_activity=False)
    assert run_module(root) == 0
    data = output(root)
    assert data["status"] == "built_without_activity_source"
    assert data["records"][0]["activity_count"] == 0
    assert data["records"][0]["activity_total_distance_km"] == 0
    assert data["records"][0]["activity_duration_weighted_average_hr_bpm"] is None
