from .helpers10 import by_date, make_load_records, make_readiness_records, run_module, setup_root


def test_rec_identity(tmp_path):
    load = make_load_records(days=29)
    readiness = make_readiness_records(load, score=72.5)
    root = setup_root(tmp_path, load_records=load, readiness_records=readiness)
    assert run_module(root) == 0
    assert by_date(root, load[-1]["date"])["rec_score"] == 72.5
