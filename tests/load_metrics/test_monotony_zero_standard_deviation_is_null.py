from .helpers08 import by_date, load_output_records, make_records, output, read_json, run_module, setup_root


def test_zero_standard_deviation_monotony_null(tmp_path):
    root = setup_root(tmp_path, records=make_records([100] * 7))
    assert run_module(root) == 0
    row = by_date(load_output_records(root), "2026-01-07")
    assert row["monotony_7d"] is None
    assert row["strain_7d"] is None
    errors = read_json(output(root, "errors.json"))["errors"]
    assert any(error["code"] == "MONOTONY_ZERO_STANDARD_DEVIATION" for error in errors)
