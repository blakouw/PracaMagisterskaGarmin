from .helpers11 import component_record, first_record, run_module, setup_root


def test_insufficient_components_do_not_produce_effective_weights(tmp_path):
    root = setup_root(tmp_path, [component_record("2026-01-01", rec=None, cap=None)])
    assert run_module(root) == 0
    record = first_record(root)
    assert record["deterministic_effective_weights"] is None
    assert record["llm_adjustment_eligible"] is False
