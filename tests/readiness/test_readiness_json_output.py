from .helpers09 import output, read_json, run_module, setup_root, base_record


def test_json_output_shape(tmp_path):
    root = setup_root(tmp_path, records=[base_record()])
    assert run_module(root) == 0
    data = read_json(output(root))
    assert data["module_id"] == "09_compute_readiness"
    assert data["ready_for_next_module"] is True
    assert data["pws_computed"] is False
    assert data["llm_used"] is False
    assert data["records_count"] == 1
