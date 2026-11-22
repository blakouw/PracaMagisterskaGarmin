from .helpers11 import component_record, first_record, run_module, setup_root


def test_effective_weights_sum_to_one(tmp_path):
    root = setup_root(tmp_path, [component_record("2026-01-01")])
    assert run_module(root) == 0
    assert round(sum(first_record(root)["deterministic_effective_weights"].values()), 6) == 1.0
