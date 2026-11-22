from .helpers12 import component_record, weight_record, run_module, setup_root, errors


def test_duplicate_dates_are_blocking(tmp_path):
    components = [component_record("2026-01-01")]
    weights = [weight_record("2026-01-01"), weight_record("2026-01-01")]
    root = setup_root(tmp_path, components=components, weights=weights)
    assert run_module(root) == 1
    assert any(error["code"] == "DUPLICATE_DATE_FOUND" for error in errors(root)["errors"])
