from helpers07 import setup_root, run_module, output
def test_json_output_shape(tmp_path):
    root = setup_root(tmp_path)
    assert run_module(root) == 0
    data = output(root)
    assert data["module_id"] == "07_build_daily_features"
    assert data["ready_for_next_module"] is True
    assert data["derived_metrics_computed"] is False
