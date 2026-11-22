from .helpers11 import component_record, first_record, run_module, setup_root


def test_rec_vs_overlap_cap(tmp_path):
    root = setup_root(tmp_path, [component_record("2026-01-01", rec=0, vs=0, lq=100, cap=100)])
    assert run_module(root) == 0
    weights = first_record(root)["deterministic_effective_weights"]
    assert weights["REC"] + weights["VS"] <= 0.650001
