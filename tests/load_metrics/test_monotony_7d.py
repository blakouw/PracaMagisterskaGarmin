from .helpers08 import by_date, load_output_records, make_records, run_module, setup_root


def test_monotony_7d_population_std(tmp_path):
    root = setup_root(tmp_path, records=make_records([1, 2, 3, 4, 5, 6, 7]))
    assert run_module(root) == 0
    row = by_date(load_output_records(root), "2026-01-07")
    assert row["weekly_load_mean_7d"] == 4
    assert row["weekly_load_population_std_7d"] == 2
    assert row["monotony_7d"] == 2
