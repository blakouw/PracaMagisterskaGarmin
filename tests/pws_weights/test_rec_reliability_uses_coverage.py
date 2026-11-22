from .helpers11 import component_record, first_record, run_module, setup_root


def test_rec_reliability_uses_coverage(tmp_path):
    root = setup_root(tmp_path, [component_record("2026-01-01", rec_coverage=0.4)])
    assert run_module(root) == 0
    assert first_record(root)["component_reliability_factors"]["REC"] == 0.5
