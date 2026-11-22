from .helpers12 import first_record, full_fixture_records, run_module, setup_root


def test_llm_assisted_score_remains_null(tmp_path):
    components, weights = full_fixture_records()
    root = setup_root(tmp_path, components=components, weights=weights)
    assert run_module(root) == 0
    assert first_record(root)["pws_llm_assisted"] is None
