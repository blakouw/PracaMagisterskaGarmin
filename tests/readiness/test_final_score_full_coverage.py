from .helpers09 import first_record, run_module, setup_root, base_record


def test_final_score_full_coverage(tmp_path):
    root = setup_root(tmp_path, records=[base_record()])
    assert run_module(root) == 0
    row = first_record(root)
    assert row["available_components_count"] == 4
    assert row["readiness_score"] == 88.91
    assert row["readiness_status"] == "computed"
    assert row["readiness_label_id"] == "high"
