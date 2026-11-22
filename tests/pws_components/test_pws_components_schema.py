from .helpers10 import output, read_json, run_module, setup_root


def test_schema(tmp_path):
    root = setup_root(tmp_path)
    assert run_module(root) == 0
    schema = read_json(output(root, "pws_components_schema.json"))
    names = {field["name"] for field in schema["fields"]}
    assert {"lq_score", "rec_score", "cap_score", "vs_score"} <= names
    assert "pws_score" in schema["excluded_future_fields"]
