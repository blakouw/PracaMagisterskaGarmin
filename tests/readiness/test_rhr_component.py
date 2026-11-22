from .helpers09 import first_record, run_module, setup_root, base_record


def test_rhr_penalty_and_below_baseline(tmp_path):
    root = setup_root(tmp_path, records=[base_record(resting_hr_bpm=55, resting_hr_baseline_bpm=50)])
    assert run_module(root) == 0
    row = first_record(root)
    assert row["rhr_delta_used_for_readiness"] == 5
    assert row["rhr_readiness_score"] == 60

    root2 = setup_root(tmp_path / "below", records=[base_record(resting_hr_bpm=48, resting_hr_baseline_bpm=50)])
    assert run_module(root2) == 0
    assert first_record(root2)["rhr_readiness_score"] == 100
