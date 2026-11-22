from .helpers11 import component_record, first_record, run_module, setup_root


def test_future_pws_eligibility_requires_three_weight_sum_and_rec_or_vs(tmp_path):
    root = setup_root(tmp_path, [component_record("2026-01-01", cap=None)])
    assert run_module(root) == 0
    assert first_record(root)["weights_ready_for_final_pws"] is True

    root = setup_root(tmp_path / "b", [component_record("2026-01-01", rec=None, cap=None)])
    assert run_module(root) == 0
    record = first_record(root)
    assert record["weights_ready_for_final_pws"] is False
    assert "minimum_available_components_not_satisfied" in record["weights_readiness_reasons"]
