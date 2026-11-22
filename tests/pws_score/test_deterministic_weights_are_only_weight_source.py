from .helpers12 import full_fixture_records, first_record, run_module, setup_root


def test_deterministic_weights_are_only_weight_source(tmp_path):
    components, weights = full_fixture_records()
    root = setup_root(tmp_path, components=components, weights=weights)
    assert run_module(root) == 0
    assert first_record(root)["pws_deterministic_weights"] == weights[0]["deterministic_effective_weights"]
