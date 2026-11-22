from .helpers08 import by_date, load_output_records, make_records, run_module, setup_root


def test_acwr_rolling_ratio(tmp_path):
    root = setup_root(tmp_path, records=make_records(list(range(1, 29))))
    assert run_module(root) == 0
    row = by_date(load_output_records(root), "2026-01-28")
    assert row["acute_rolling_7d"] == 25
    assert row["chronic_rolling_28d"] == 14.5
    assert row["acwr_rolling"] == round(25 / 14.5, 6)
