from .helpers11 import component_record, read_json, run_module, setup_root


def test_llm_guardrails_artifact(tmp_path):
    root = setup_root(tmp_path, [component_record("2026-01-01")])
    assert run_module(root) == 0
    guardrails = read_json(root / "data/pipeline/11_compute_pws_weights/pws_weight_guardrails.json")
    future = guardrails["future_llm_adjustment"]
    assert future["maximum_absolute_delta_per_component"] == 0.20
    assert future["maximum_total_positive_weight_shift"] == 0.20
    assert future["maximum_total_absolute_delta"] == 0.40
    assert future["unavailable_component_weight_must_remain_zero"] is True
    assert future["must_preserve_deterministic_weights_separately"] is True
    assert future["must_reapply_overlap_controls_after_proposal"] is True
