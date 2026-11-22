from .helpers11 import component_record, read_json, run_module, setup_root


def test_quality_report(tmp_path):
    root = setup_root(tmp_path, [component_record("2026-01-01", cap=None)])
    assert run_module(root) == 0
    quality = read_json(root / "data/pipeline/11_compute_pws_weights/pws_weights_quality_report.json")
    assert quality["component_availability"]["CAP"]["missing_count"] == 1
    assert quality["weight_readiness"]["weights_ready_for_final_pws_count"] == 1
