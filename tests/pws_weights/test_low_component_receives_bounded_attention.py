from .helpers11 import component_record, first_record, run_module, setup_root


def test_low_component_receives_bounded_attention(tmp_path):
    root = setup_root(tmp_path, [component_record("2026-01-01", lq=0)])
    assert run_module(root) == 0
    record = first_record(root)
    assert record["component_urgency_factors"]["LQ"] == 1.5
    assert record["deterministic_weight_deltas_from_base_available"]["LQ"] <= 0.07
