from helpers07 import setup_root, run_module, output, activity
def test_activity_with_missing_distance_aggregates_to_null(tmp_path):
    act = activity("a1", distance=None, duration=100)
    root = setup_root(tmp_path, activities=[act])
    assert run_module(root) == 0
    row = output(root)["records"][0]
    assert row["activity_count"] == 1
    assert row["activity_total_distance_km"] is None
