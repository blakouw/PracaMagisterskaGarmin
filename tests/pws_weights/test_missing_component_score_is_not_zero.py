from .helpers11 import component_record, first_record, run_module, setup_root


def test_missing_component_score_is_not_zero(tmp_path):
    root = setup_root(tmp_path, [component_record("2026-01-01", rec=None, cap=None)])
    assert run_module(root) == 0
    record = first_record(root)
    assert record["component_scores"]["REC"] is None
    assert record["component_scores"]["REC"] != 0
    assert record["base_available_weights"]["REC"] == 0
