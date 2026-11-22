from .helpers11 import component_record, read_json, run_module, setup_root


def test_llm_cannot_adjust_unavailable_component_contract(tmp_path):
    root = setup_root(tmp_path, [component_record("2026-01-01", cap=None)])
    assert run_module(root) == 0
    guardrails = read_json(root / "data/pipeline/11_compute_pws_weights/pws_weight_guardrails.json")
    assert "assign_weight_to_unavailable_component" in guardrails["forbidden_future_llm_actions"]
    assert guardrails["future_llm_adjustment"]["unavailable_component_weight_must_remain_zero"] is True
