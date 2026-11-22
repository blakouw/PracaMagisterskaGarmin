from .helpers11 import component_record, first_record, run_module, setup_root


def test_lq_rec_overlap_cap(tmp_path):
    root = setup_root(tmp_path, [component_record("2026-01-01", lq=0, rec=0, cap=100, vs=100)])
    assert run_module(root) == 0
    weights = first_record(root)["deterministic_effective_weights"]
    assert weights["LQ"] + weights["REC"] <= 0.550001
