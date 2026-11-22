from .helpers08 import by_date, load_output_records, make_records, output, read_json, run_module, setup_root


def test_ewma_restarts_after_calendar_gap(tmp_path):
    root = setup_root(tmp_path, records=make_records([100, 200], dates=["2026-01-01", "2026-01-03"]))
    assert run_module(root) == 0
    row = by_date(load_output_records(root), "2026-01-03")
    assert row["ewma_sequence_id"] == 2
    assert row["ewma_sequence_day_index"] == 1
    assert row["acute_ewma_7d"] == 200
    errors = read_json(output(root, "errors.json"))["errors"]
    assert any(error["code"] == "EWMA_SEQUENCE_RESTARTED" for error in errors)
