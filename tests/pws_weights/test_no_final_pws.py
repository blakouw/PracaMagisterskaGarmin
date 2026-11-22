from .helpers11 import component_record, first_record, read_json, run_module, setup_root


def test_no_final_pws_fields_or_values(tmp_path):
    root = setup_root(tmp_path, [component_record("2026-01-01")])
    assert run_module(root) == 0
    record = first_record(root)
    forbidden = {"pws_score", "pws_deterministic", "pws_llm_assisted", "llm_adjusted_weights", "priority_component", "priority_recommendation", "coach_message", "training_recommendation"}
    assert not (forbidden & set(record))
    payload = read_json(root / "data/pipeline/11_compute_pws_weights/pws_weights.json")
    assert payload["final_pws_computed"] is False
