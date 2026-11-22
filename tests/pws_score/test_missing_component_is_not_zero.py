from .helpers12 import first_record, partial_fixture_records, run_module, setup_root


def test_missing_component_is_not_zero(tmp_path):
    components, weights = partial_fixture_records()
    root = setup_root(tmp_path, components=components, weights=weights)
    assert run_module(root) == 0
    record = first_record(root)
    assert record["pws_component_scores"]["CAP"] is None
    assert record["pws_component_scores"]["CAP"] != 0
    assert record["pws_weighted_contributions"]["CAP"] == 0.0
