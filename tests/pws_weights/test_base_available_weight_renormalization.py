from .helpers11 import component_record, first_record, run_module, setup_root


def test_base_available_weight_renormalization(tmp_path):
    root = setup_root(tmp_path, [component_record("2026-01-01", cap=None)])
    assert run_module(root) == 0
    weights = first_record(root)["base_available_weights"]
    assert round(weights["LQ"], 6) == 0.235294
    assert round(weights["REC"], 6) == 0.411765
    assert weights["CAP"] == 0
    assert round(weights["VS"], 6) == 0.352941
