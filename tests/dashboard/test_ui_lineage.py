import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_ui_lineage(validate_module):
    assert validate_module.main(["--build-exit-code", "0", "--frontend-test-exit-code", "0"]) == 0
    lineage = json.loads((ROOT / "data/pipeline/18_angular_dashboard_ui/ui_lineage.json").read_text(encoding="utf-8"))
    assert lineage["source_api"]["module_id"] == "17_local_api_server"
    assert lineage["presentation_mapping"]["PrimaryPwsCard"] == "current_state.primary_pws"
    assert lineage["transformation_policy"]["analytical_values_recomputed"] is False
    assert lineage["forbidden_action_confirmation"]["pipeline_triggered"] is False
