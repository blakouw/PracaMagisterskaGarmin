from .helpers08 import by_date, load_output_records, make_records, run_module, setup_root


def test_strain_7d(tmp_path):
    root = setup_root(tmp_path, records=make_records([1, 2, 3, 4, 5, 6, 7]))
    assert run_module(root) == 0
    row = by_date(load_output_records(root), "2026-01-07")
    assert row["weekly_load_sum_7d"] == 28
    assert row["strain_7d"] == 56
