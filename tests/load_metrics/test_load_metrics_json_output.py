from .helpers08 import make_records, output, read_json, run_module, setup_root


def test_json_output_shape(tmp_path):
    root = setup_root(tmp_path, records=make_records([100] * 8))
    assert run_module(root) == 0
    data = read_json(output(root))
    assert data["module_id"] == "08_compute_load_metrics"
    assert data["ready_for_next_module"] is True
    assert data["records_count"] == 8
    assert "acute_rolling_7d" in data["metrics_computed"]
