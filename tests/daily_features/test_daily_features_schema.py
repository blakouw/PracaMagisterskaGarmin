from helpers07 import setup_root, run_module, output
def test_schema_contains_daily_and_activity_fields(tmp_path):
    root = setup_root(tmp_path)
    assert run_module(root) == 0
    names = [f["name"] for f in output(root, "daily_features_schema.json")["fields"]]
    assert "date" in names
    assert "activity_total_distance_km" in names
    assert "acwr" in output(root, "daily_features_schema.json")["excluded_derived_fields"]
