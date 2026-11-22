from .helpers12 import full_fixture_records, first_record, run_module, setup_root


def test_full_coverage_pws_calculation(tmp_path):
    components, weights = full_fixture_records()
    root = setup_root(tmp_path, components=components, weights=weights)
    assert run_module(root) == 0
    record = first_record(root)
    assert record["pws_deterministic"] == 91.63
    assert record["pws_status"] == "computed_full_coverage"
