from .helpers08 import load_output_records, make_records, run_module, setup_root


def test_active_kcal_remains_the_fallback_without_complete_rpe(tmp_path):
    records = make_records([100, 100, 100, 100, 100, 100, 100], extra={"activity_total_calories": 99999})
    root = setup_root(tmp_path, records=records)
    assert run_module(root) == 0
    out = load_output_records(root)
    assert all(record["load_active_kcal"] == 100 for record in out)
    assert all(record["load_value"] == 100 for record in out)
    assert all(record["load_source"] == "active_kcal_fallback" for record in out)
