from .helpers10 import by_date, make_load_records, make_readiness_records, run_module, setup_root


def test_rec_unavailable_without_score(tmp_path):
    load = make_load_records(days=29)
    readiness = make_readiness_records(load)
    readiness[-1]["readiness_score"] = None
    readiness[-1]["readiness_status"] = "insufficient_data"
    root = setup_root(tmp_path, load_records=load, readiness_records=readiness)
    assert run_module(root) == 0
    row = by_date(root, load[-1]["date"])
    assert row["rec_score"] is None
    assert row["rec_status"] == "unavailable_insufficient_readiness_data"
