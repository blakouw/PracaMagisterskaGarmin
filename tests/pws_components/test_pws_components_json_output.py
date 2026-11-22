from .helpers10 import output, read_json, run_module, setup_root


def test_json_output_shape(tmp_path):
    root = setup_root(tmp_path)
    assert run_module(root) == 0
    data = read_json(output(root))
    assert data["module_id"] == "10_compute_pws_components"
    assert data["ready_for_next_module"] is True
    assert data["final_pws_computed"] is False
    assert data["pws_weights_computed"] is False
    assert data["llm_used"] is False
