from .helpers09 import first_record, output, read_json, run_module, setup_root, base_record


def test_component_clipping_warning(tmp_path):
    root = setup_root(tmp_path, records=[base_record(avg_stress=-20)])
    assert run_module(root) == 0
    row = first_record(root)
    assert row["stress_readiness_score"] == 100
    report = read_json(output(root, "readiness_quality_report.json"))
    assert report["days_with_clipped_component_values"] == ["2026-01-01"]
