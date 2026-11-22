from .helpers08 import by_date, load_output_records, make_records, run_module, setup_root


def test_acute_ewma_alpha(tmp_path):
    root = setup_root(tmp_path, records=make_records([100, 200]))
    assert run_module(root) == 0
    row = by_date(load_output_records(root), "2026-01-02")
    assert row["acute_ewma_7d"] == 125
