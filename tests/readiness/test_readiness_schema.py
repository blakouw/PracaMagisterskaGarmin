from .helpers09 import output, read_json, run_module, setup_root, base_record


def test_schema_documents_components(tmp_path):
    root = setup_root(tmp_path, records=[base_record()])
    assert run_module(root) == 0
    schema = read_json(output(root, "readiness_schema.json"))
    names = {field["name"] for field in schema["fields"]}
    assert "readiness_score" in names
    assert {"hrv_readiness_score", "stress_readiness_score", "rhr_readiness_score", "load_balance_readiness_score"} <= names
    assert "pws_weights" in schema["excluded_future_fields"]
