from .helpers11 import component_record, first_record, run_module, setup_root


def test_vs_reliability_uses_coverage(tmp_path):
    root = setup_root(tmp_path, [component_record("2026-01-01", vs_coverage=0.75)])
    assert run_module(root) == 0
    assert first_record(root)["component_reliability_factors"]["VS"] == 0.75
