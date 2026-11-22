from .helpers11 import component_record, read_json, run_module, setup_root


def test_pws_weights_schema(tmp_path):
    root = setup_root(tmp_path, [component_record("2026-01-01")])
    assert run_module(root) == 0
    schema = read_json(root / "data/pipeline/11_compute_pws_weights/pws_weights_schema.json")
    assert schema["schema_version"] == "pws_weights_schema_v1"
    assert "pws_score" in schema["excluded_future_fields"]
