from .helpers12 import first_record, full_fixture_records, run_module, setup_root


def test_no_coaching_or_medical_outputs(tmp_path):
    components, weights = full_fixture_records()
    root = setup_root(tmp_path, components=components, weights=weights)
    assert run_module(root) == 0
    forbidden = {"llm_adjusted_weights", "priority_component", "priority_recommendation", "coach_message", "training_recommendation", "medical_diagnosis", "injury_prediction"}
    assert not (forbidden & set(first_record(root)))
