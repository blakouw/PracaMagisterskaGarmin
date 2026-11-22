from .helpers09 import first_record, run_module, setup_root, base_record


def test_missing_components_are_null_not_zero(tmp_path):
    root = setup_root(tmp_path, records=[base_record(resting_hr_bpm=None, resting_hr_baseline_bpm=None)])
    assert run_module(root) == 0
    row = first_record(root)
    assert row["rhr_readiness_score"] is None
    assert "rhr" in row["missing_readiness_components"]
