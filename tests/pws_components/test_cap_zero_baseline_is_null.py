from .helpers10 import by_date, make_load_records, make_readiness_records, run_module, setup_root


def test_cap_zero_baseline(tmp_path):
    load = make_load_records(days=29)
    for i in range(1, 22):
        load[i]["activity_total_duration_seconds"] = 0
    root = setup_root(tmp_path, load_records=load, readiness_records=make_readiness_records(load))
    assert run_module(root) == 0
    row = by_date(root, load[-1]["date"])
    assert row["cap_score"] is None
    assert row["cap_status"] == "unavailable_zero_baseline_activity_duration"
