from .helpers12 import component_record, first_record, run_module, setup_root, weight_record, errors


def test_positive_weight_for_missing_component_is_invalid(tmp_path):
    components = [component_record("2026-01-01", cap=None)]
    weights = [weight_record("2026-01-01", cap=None, weights={"LQ": 0.2, "REC": 0.35, "CAP": 0.15, "VS": 0.3}, ready=True, available=["LQ", "REC", "VS"], missing=["CAP"])]
    root = setup_root(tmp_path, components=components, weights=weights)
    assert run_module(root) == 0
    assert first_record(root)["pws_deterministic"] is None
    assert any(error["code"] == "POSITIVE_WEIGHT_FOR_MISSING_COMPONENT" for error in errors(root)["errors"])
