from .helpers08 import by_date, load_output_records, make_records, run_module, setup_root


def test_chronic_rolling_28d_complete_window(tmp_path):
    root = setup_root(tmp_path, records=make_records(list(range(1, 29))))
    assert run_module(root) == 0
    row = by_date(load_output_records(root), "2026-01-28")
    assert row["chronic_rolling_28d"] == 14.5
    assert row["chronic_rolling_28d_complete"] is True
