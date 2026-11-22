from .helpers08 import make_records, output, read_json, run_module, setup_root


def test_lineage_report_documents_source_and_groups(tmp_path):
    root = setup_root(tmp_path, records=make_records([100] * 8))
    assert run_module(root) == 0
    lineage = read_json(output(root, "load_metrics_lineage.json"))
    assert lineage["load_source"]["fallback_input_field"] == "active_kcal"
    groups = {group["group_name"] for group in lineage["metric_groups"]}
    assert {"dashboard_rolling_load", "analytical_ewma_load", "weekly_variability"} <= groups
    assert lineage["forbidden_calculation_confirmation"]["llm_used"] is False
