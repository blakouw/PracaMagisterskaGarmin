from .helpers11 import component_record, first_record, run_module, setup_root


def test_cap_reliability_requires_complete_window(tmp_path):
    root = setup_root(tmp_path, [component_record("2026-01-01", cap_window_complete=False)])
    assert run_module(root) == 0
    assert first_record(root)["component_reliability_factors"]["CAP"] == 0.75
