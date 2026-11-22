from .helpers10 import by_date, make_load_records, make_readiness_records, run_module, setup_root


def test_missing_components_are_null(tmp_path):
    load = make_load_records(days=29)
    load[-1]["acwr_ewma"] = None
    load[-1]["acwr_rolling"] = None
    root = setup_root(tmp_path, load_records=load, readiness_records=make_readiness_records(load))
    assert run_module(root) == 0
    row = by_date(root, load[-1]["date"])
    assert row["lq_score"] is None
    assert row["available_pws_components_count"] == 3
    assert row["pws_components_coverage_ratio"] == 0.75
