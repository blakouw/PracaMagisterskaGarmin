from .helpers11 import component_record, first_record, run_module, setup_root


def test_movement_limit_per_component(tmp_path):
    root = setup_root(tmp_path, [component_record("2026-01-01", rec=0, lq=100, cap=100, vs=100)])
    assert run_module(root) == 0
    deltas = first_record(root)["deterministic_weight_deltas_from_base_available"]
    assert max(abs(value) for value in deltas.values()) <= 0.070001
