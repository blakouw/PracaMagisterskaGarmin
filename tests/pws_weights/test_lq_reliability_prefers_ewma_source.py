from .helpers11 import component_record, first_record, run_module, setup_root


def test_lq_reliability_prefers_ewma_source(tmp_path):
    root = setup_root(tmp_path, [component_record("2026-01-01", lq_source_metric="acwr_ewma")])
    assert run_module(root) == 0
    record = first_record(root)
    assert record["component_reliability_factors"]["LQ"] == 1.0
    assert record["component_reliability_methods"]["LQ"] == "preferred_ewma_acwr_source"
