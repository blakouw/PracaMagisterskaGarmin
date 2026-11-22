from .helpers11 import component_record, first_record, run_module, setup_root


def test_partial_component_overlap_is_disclosed_not_forced(tmp_path):
    root = setup_root(tmp_path, [component_record("2026-01-01", cap=None)])
    assert run_module(root) == 0
    record = first_record(root)
    assert record["weights_ready_for_final_pws"] is True
    assert record["overlap_controls_applied"] == []
    assert any("not applied" in text for text in record["overlap_disclosures"])
