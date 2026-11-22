from .helpers10 import by_date, make_load_records, make_readiness_records, run_module, setup_root


def test_lq_rolling_fallback(tmp_path):
    load = make_load_records(days=29)
    load[-1]["acwr_ewma"] = None
    load[-1]["acwr_rolling"] = 0.4
    root = setup_root(tmp_path, load_records=load, readiness_records=make_readiness_records(load))
    assert run_module(root) == 0
    row = by_date(root, load[-1]["date"])
    assert row["lq_source_metric"] == "acwr_rolling"
    assert row["lq_score"] == 70
