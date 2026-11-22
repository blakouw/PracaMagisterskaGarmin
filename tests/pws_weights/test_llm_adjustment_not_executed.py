from .helpers11 import component_record, first_record, read_json, run_module, setup_root


def test_llm_adjustment_not_executed(tmp_path):
    root = setup_root(tmp_path, [component_record("2026-01-01")])
    assert run_module(root) == 0
    assert first_record(root)["llm_adjustment_applied"] is False
    payload = read_json(root / "data/pipeline/11_compute_pws_weights/pws_weights.json")
    assert payload["llm_used"] is False
    assert payload["llm_adjustment_applied"] is False
