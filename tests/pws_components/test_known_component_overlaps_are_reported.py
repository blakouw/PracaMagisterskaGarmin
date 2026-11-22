from .helpers10 import output, read_json, run_module, setup_root


def test_overlaps_reported(tmp_path):
    root = setup_root(tmp_path)
    assert run_module(root) == 0
    data = read_json(output(root))
    assert len(data["known_component_overlaps"]) == 2
    report = read_json(output(root, "pws_components_quality_report.json"))
    assert len(report["known_component_overlaps"]) == 2
