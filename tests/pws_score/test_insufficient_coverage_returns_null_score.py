from .helpers12 import first_record, insufficient_fixture_records, run_module, setup_root


def test_insufficient_coverage_returns_null_score(tmp_path):
    components, weights = insufficient_fixture_records()
    root = setup_root(tmp_path, components=components, weights=weights)
    assert run_module(root) == 0
    record = first_record(root)
    assert record["pws_deterministic"] is None
    assert record["pws_status"] == "not_computed_insufficient_component_coverage"
