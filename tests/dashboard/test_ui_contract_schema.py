import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_ui_contract_schema():
    schema = json.loads((ROOT / "pipeline/18_angular_dashboard_ui/ui_contract_schema.json").read_text(encoding="utf-8"))
    assert schema["module_id"] == "18_angular_dashboard_ui"
    assert schema["data_source"]["source_type"] == "local_read_only_api_only"
    assert schema["data_source"]["direct_file_reading_allowed"] is False
    assert schema["primary_score_contract"]["required_score_type"] == "deterministic"
    assert schema["optional_assisted_score_contract"]["must_not_replace_primary"] is True
    assert "AppStatusHeader" in schema["required_components"]
