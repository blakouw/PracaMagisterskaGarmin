from .helpers08 import by_date, load_output_records, make_records, run_module, setup_root


def test_windows_use_calendar_days_not_last_available_records(tmp_path):
    dates = ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04", "2026-01-05", "2026-01-06", "2026-01-08"]
    root = setup_root(tmp_path, records=make_records([10, 20, 30, 40, 50, 60, 70], dates=dates))
    assert run_module(root) == 0
    row = by_date(load_output_records(root), "2026-01-08")
    assert row["acute_rolling_7d"] is None
    assert row["acute_rolling_7d_coverage_days"] == 6
