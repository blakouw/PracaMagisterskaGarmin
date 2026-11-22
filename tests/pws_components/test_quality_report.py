from .helpers10 import output, read_json, run_module, setup_root


def test_quality_report(tmp_path):
    root = setup_root(tmp_path)
    assert run_module(root) == 0
    report = read_json(output(root, "pws_components_quality_report.json"))
    assert "component_availability" in report
    assert report["component_availability"]["LQ"]["available_count"] >= 1
    assert report["final_pws_computed"] is False
