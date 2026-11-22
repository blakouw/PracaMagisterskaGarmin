from .helpers10 import by_date, make_load_records, make_readiness_records, run_module, setup_root


def test_cap_formula(tmp_path):
    load = make_load_records(days=29)
    root = setup_root(tmp_path, load_records=load, readiness_records=make_readiness_records(load))
    assert run_module(root) == 0
    row = by_date(root, load[-1]["date"])
    assert row["cap_recent_duration_seconds_7d"] == 12600
    assert row["cap_baseline_duration_seconds_21d"] == 75600
    assert row["cap_baseline_weekly_equivalent_seconds"] == 25200
    assert row["cap_recent_to_baseline_ratio"] == 0.5
    assert row["cap_score"] == 50
