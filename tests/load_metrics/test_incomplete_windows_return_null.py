from .helpers08 import by_date, load_output_records, make_records, run_module, setup_root


def test_incomplete_windows_are_null(tmp_path):
    root = setup_root(tmp_path, records=make_records([100, 200, 300]))
    assert run_module(root) == 0
    row = by_date(load_output_records(root), "2026-01-03")
    assert row["acute_rolling_7d"] is None
    assert row["chronic_rolling_28d"] is None
    assert row["acwr_rolling"] is None
