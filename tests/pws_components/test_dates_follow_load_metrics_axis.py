from .helpers10 import make_load_records, make_readiness_records, records, run_module, setup_root


def test_dates_follow_load_metrics_axis(tmp_path):
    load = make_load_records(days=3)
    readiness = make_readiness_records(load) + [{"date": "2026-02-01", "readiness_score": 90, "readiness_status": "computed", "readiness_coverage_ratio": 1}]
    root = setup_root(tmp_path, load_records=load, readiness_records=readiness)
    assert run_module(root) == 0
    assert [row["date"] for row in records(root)] == [row["date"] for row in load]
