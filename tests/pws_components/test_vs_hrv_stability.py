from .helpers10 import by_date, make_load_records, make_readiness_records, run_module, setup_root


def test_vs_hrv_stability(tmp_path):
    load = make_load_records(days=29)
    root = setup_root(tmp_path, load_records=load, readiness_records=make_readiness_records(load))
    assert run_module(root) == 0
    assert by_date(root, load[-1]["date"])["vs_hrv_stability_score"] == 60
