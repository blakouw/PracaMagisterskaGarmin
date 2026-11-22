from .helpers09 import first_record, run_module, setup_root, base_record


def test_stress_inverse(tmp_path):
    root = setup_root(tmp_path, records=[base_record(avg_stress=28)])
    assert run_module(root) == 0
    assert first_record(root)["stress_readiness_score"] == 72
