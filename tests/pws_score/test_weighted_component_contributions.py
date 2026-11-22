from .helpers12 import full_fixture_records, first_record, run_module, setup_root


def test_weighted_component_contributions(tmp_path):
    components, weights = full_fixture_records()
    root = setup_root(tmp_path, components=components, weights=weights)
    assert run_module(root) == 0
    contrib = first_record(root)["pws_weighted_contributions"]
    assert contrib == {"LQ": 20.0, "REC": 30.366, "CAP": 13.86, "VS": 27.405}
