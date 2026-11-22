from .helpers12 import full_fixture_records, insufficient_fixture_records, partial_fixture_records, first_record, run_module, setup_root


def test_coverage_tiers(tmp_path):
    components, weights = full_fixture_records()
    root = setup_root(tmp_path / "a", components=components, weights=weights)
    assert run_module(root) == 0
    assert first_record(root)["pws_coverage_tier"] == "full"
    components, weights = partial_fixture_records()
    root = setup_root(tmp_path / "b", components=components, weights=weights)
    assert run_module(root) == 0
    assert first_record(root)["pws_coverage_tier"] == "partial_eligible"
    components, weights = insufficient_fixture_records()
    root = setup_root(tmp_path / "c", components=components, weights=weights)
    assert run_module(root) == 0
    assert first_record(root)["pws_coverage_tier"] == "insufficient"
