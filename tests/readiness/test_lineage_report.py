from .helpers09 import output, read_json, run_module, setup_root, base_record


def test_lineage_report(tmp_path):
    root = setup_root(tmp_path, records=[base_record()])
    assert run_module(root) == 0
    lineage = read_json(output(root, "readiness_lineage.json"))
    components = {item["component"] for item in lineage["component_lineage"]}
    assert {"hrv", "stress", "rhr", "load_balance"} == components
    assert lineage["forbidden_calculation_confirmation"]["pws_score_computed"] is False
    assert lineage["forbidden_calculation_confirmation"]["llm_used"] is False
