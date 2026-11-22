from .helpers11 import component_record, first_record, run_module, setup_root


def test_candidate_weight_normalization(tmp_path):
    root = setup_root(tmp_path, [component_record("2026-01-01", lq=40, rec=90, cap=90, vs=90)])
    assert run_module(root) == 0
    weights = first_record(root)["candidate_deterministic_weights"]
    assert round(sum(weights.values()), 6) == 1.0
