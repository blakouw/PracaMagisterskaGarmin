from helpers07 import setup_root, run_module, output, activity
def test_duration_weighted_averages(tmp_path):
    acts = [activity("a1", duration=100, hr=100, power=200, speed=10), activity("a2", duration=300, hr=200, power=300, speed=20)]
    root = setup_root(tmp_path, activities=acts)
    assert run_module(root) == 0
    row = output(root)["records"][0]
    assert row["activity_duration_weighted_average_hr_bpm"] == 175
    assert row["activity_duration_weighted_average_power_w"] == 275
    assert row["activity_duration_weighted_average_speed_kmh"] == 17.5
