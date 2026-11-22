from .helpers10 import by_date, make_load_records, make_readiness_records, run_module, setup_root


def test_lq_prefers_ewma(tmp_path):
    load = make_load_records(days=29)
    load[-1]["acwr_ewma"] = 1.4
    load[-1]["acwr_rolling"] = 1.0
    root = setup_root(tmp_path, load_records=load, readiness_records=make_readiness_records(load))
    assert run_module(root) == 0
    row = by_date(root, load[-1]["date"])
    assert row["lq_source_metric"] == "acwr_ewma"
    assert row["lq_score"] == 80
