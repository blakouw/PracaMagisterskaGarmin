from .helpers11 import component_record, first_record, run_module, setup_root


def test_unavailable_component_effective_weight_is_zero_only_as_exclusion(tmp_path):
    root = setup_root(tmp_path, [component_record("2026-01-01", cap=None)])
    assert run_module(root) == 0
    record = first_record(root)
    assert record["component_scores"]["CAP"] is None
    assert record["deterministic_effective_weights"]["CAP"] == 0
