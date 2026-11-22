from .helpers09 import first_record, run_module, setup_root, base_record


def test_load_balance_rolling_fallback(tmp_path):
    root = setup_root(tmp_path, records=[base_record(acwr_ewma=None, acwr_rolling=0.4)])
    assert run_module(root) == 0
    row = first_record(root)
    assert row["load_balance_source_metric"] == "acwr_rolling"
    assert row["load_balance_readiness_score"] == 70
