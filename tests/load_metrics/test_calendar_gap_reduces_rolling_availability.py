from .helpers08 import output, read_json, run_module, setup_root, make_records


def test_calendar_gap_reports_status_and_missing_date(tmp_path):
    root = setup_root(tmp_path, records=make_records([100, 200], dates=["2026-01-01", "2026-01-03"]))
    assert run_module(root) == 0
    report = read_json(output(root, "load_metrics_quality_report.json"))
    assert report["status"] == "computed_with_calendar_gaps"
    assert report["calendar_axis_quality"]["missing_calendar_dates"] == ["2026-01-02"]
