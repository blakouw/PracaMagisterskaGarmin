from .helpers11 import component_record, output, read_json, run_module, setup_root


def test_pws_weights_json_output(tmp_path):
    root = setup_root(tmp_path, [component_record("2026-01-01")])
    assert run_module(root) == 0
    payload = read_json(output(root))
    assert payload["module_id"] == "11_compute_pws_weights"
    assert payload["ready_for_next_module"] is True
    assert payload["records_count"] == 1
