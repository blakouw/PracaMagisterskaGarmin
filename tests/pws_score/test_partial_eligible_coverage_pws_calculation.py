from .helpers12 import first_record, partial_fixture_records, run_module, setup_root


def test_partial_eligible_coverage_pws_calculation(tmp_path):
    components, weights = partial_fixture_records()
    root = setup_root(tmp_path, components=components, weights=weights)
    assert run_module(root) == 0
    record = first_record(root)
    assert record["pws_deterministic"] == 75.44
    assert record["pws_coverage_tier"] == "partial_eligible"
    assert record["pws_computed_from_partial_coverage"] is True
