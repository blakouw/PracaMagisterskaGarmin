from .helpers10 import by_date, make_load_records, make_readiness_records, run_module, setup_root


def test_vs_baseline_excludes_current_day(tmp_path):
    load = make_load_records(days=29)
    load[-1]["resting_hr_bpm"] = 1000
    root = setup_root(tmp_path, load_records=load, readiness_records=make_readiness_records(load))
    assert run_module(root) == 0
    details = by_date(root, load[-1]["date"])["vs_signal_details"]["rhr_stability"]
    assert details["baseline_median"] == 50
