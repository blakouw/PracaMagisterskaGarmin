from .helpers10 import by_date, make_load_records, make_readiness_records, run_module, setup_root


def test_vs_minimum_signal_coverage(tmp_path):
    load = make_load_records(days=29)
    for row in load:
        row["hrv_last_night_avg_ms"] = None
        row["avg_sleep_spo2"] = None
        row["avg_sleep_respiration"] = None
    root = setup_root(tmp_path, load_records=load, readiness_records=make_readiness_records(load))
    assert run_module(root) == 0
    row = by_date(root, load[-1]["date"])
    assert row["vs_score"] is None
    assert row["vs_status"] == "insufficient_vital_signal_coverage"
