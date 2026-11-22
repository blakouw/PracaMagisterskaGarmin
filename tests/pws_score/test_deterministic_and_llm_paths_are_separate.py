from .helpers12 import first_record, full_fixture_records, run_module, setup_root


def test_deterministic_and_llm_paths_are_separate(tmp_path):
    components, weights = full_fixture_records()
    root = setup_root(tmp_path, components=components, weights=weights)
    assert run_module(root) == 0
    record = first_record(root)
    assert record["pws_deterministic_computed"] is True
    assert record["pws_llm_assisted_computed"] is False
    assert record["future_llm_assisted_path_status"] == "eligible_but_not_executed"
