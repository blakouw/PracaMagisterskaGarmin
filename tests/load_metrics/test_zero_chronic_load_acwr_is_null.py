from .helpers08 import by_date, load_output_records, make_records, run_module, setup_root


def test_zero_chronic_load_makes_acwr_null(tmp_path):
    root = setup_root(tmp_path, records=make_records([0] * 28))
    assert run_module(root) == 0
    row = by_date(load_output_records(root), "2026-01-28")
    assert row["chronic_rolling_28d"] == 0
    assert row["acwr_rolling"] is None
    assert row["acwr_ewma"] is None
