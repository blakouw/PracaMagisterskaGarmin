from .helpers08 import make_records, output, read_json, run_module, setup_root


def test_schema_documents_metrics_and_exclusions(tmp_path):
    root = setup_root(tmp_path, records=make_records([100] * 8))
    assert run_module(root) == 0
    schema = read_json(output(root, "load_metrics_schema.json"))
    names = {field["name"] for field in schema["fields"]}
    assert "load_active_kcal" in names
    assert "acute_rolling_7d" in names
    assert "readiness" in schema["excluded_future_fields"]
