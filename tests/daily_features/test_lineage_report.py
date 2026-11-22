from helpers07 import setup_root, run_module, output
def test_lineage_report(tmp_path):
    root = setup_root(tmp_path)
    assert run_module(root) == 0
    l = output(root, "daily_features_lineage.json")
    assert l["forbidden_metrics_confirmation"]["pws_computed"] is False
    assert any(g["group_name"] == "activity_daily_counts_and_sums" for g in l["field_groups"])
