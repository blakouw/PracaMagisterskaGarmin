from .helpers08 import make_records, output, read_json, run_module, setup_root


def test_quality_report_has_availability_and_proxy_warning(tmp_path):
    root = setup_root(tmp_path, records=make_records(list(range(1, 29))))
    assert run_module(root) == 0
    report = read_json(output(root, "load_metrics_quality_report.json"))
    assert report["load_source"]["field"] == "load_value"
    assert report["load_source"]["proxy_limitation_acknowledged"] is True
    assert report["metric_availability"]["chronic_rolling_28d"]["available_count"] == 1
    assert report["forbidden_metrics_computed"] is False
