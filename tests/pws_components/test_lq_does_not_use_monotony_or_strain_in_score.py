from .helpers10 import by_date, make_load_records, make_readiness_records, run_module, setup_root


def test_lq_context_does_not_change_score(tmp_path):
    load1 = make_load_records(days=29)
    load2 = make_load_records(days=29)
    load2[-1]["monotony_7d"] = 9999
    load2[-1]["strain_7d"] = 999999
    root1 = setup_root(tmp_path / "a", load_records=load1, readiness_records=make_readiness_records(load1))
    root2 = setup_root(tmp_path / "b", load_records=load2, readiness_records=make_readiness_records(load2))
    assert run_module(root1) == 0
    assert run_module(root2) == 0
    assert by_date(root1, load1[-1]["date"])["lq_score"] == by_date(root2, load2[-1]["date"])["lq_score"]
