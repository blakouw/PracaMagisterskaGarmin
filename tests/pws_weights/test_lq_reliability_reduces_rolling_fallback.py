from .helpers11 import component_record, first_record, run_module, setup_root


def test_lq_reliability_reduces_rolling_fallback(tmp_path):
    root = setup_root(tmp_path, [component_record("2026-01-01", lq_source_metric="acwr_rolling")])
    assert run_module(root) == 0
    assert first_record(root)["component_reliability_factors"]["LQ"] == 0.85
