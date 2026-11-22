from .helpers10 import make_load_records, make_readiness_records, output, read_json, run_module, setup_root


def test_orphan_readiness_dates_reported(tmp_path):
    load = make_load_records(days=3)
    readiness = make_readiness_records(load) + [{"date": "2026-02-01", "readiness_score": 90, "readiness_status": "computed", "readiness_coverage_ratio": 1}]
    root = setup_root(tmp_path, load_records=load, readiness_records=readiness)
    assert run_module(root) == 0
    report = read_json(output(root, "pws_components_quality_report.json"))
    assert report["orphan_readiness_dates"] == ["2026-02-01"]
