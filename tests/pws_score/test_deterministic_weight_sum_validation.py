from .helpers12 import component_record, first_record, run_module, setup_root, weight_record, errors


def test_weight_sum_validation(tmp_path):
    components = [component_record("2026-01-01")]
    weights = [weight_record("2026-01-01", weights={"LQ": 0.2, "REC": 0.35, "CAP": 0.15, "VS": 0.29})]
    root = setup_root(tmp_path, components=components, weights=weights)
    assert run_module(root) == 0
    assert first_record(root)["pws_deterministic"] is None
    assert any(error["code"] == "DETERMINISTIC_WEIGHT_SUM_INVALID" for error in errors(root)["errors"])
