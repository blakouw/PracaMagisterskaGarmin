from .helpers11 import component_record, errors, run_module, setup_root


def test_duplicate_dates_are_blocking(tmp_path):
    records = [component_record("2026-01-01"), component_record("2026-01-01")]
    root = setup_root(tmp_path, records)
    assert run_module(root) == 1
    assert any(error["code"] == "DUPLICATE_DATE_FOUND" for error in errors(root)["errors"])
