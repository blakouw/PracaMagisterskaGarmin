from .helpers11 import component_record, first_record, run_module, setup_root


def test_total_movement_limit(tmp_path):
    root = setup_root(tmp_path, [component_record("2026-01-01", lq=0, rec=0, cap=100, vs=100)])
    assert run_module(root) == 0
    assert first_record(root)["deterministic_total_absolute_weight_change"] <= 0.200001
