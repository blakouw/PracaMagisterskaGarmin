import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def r(p): return json.loads((ROOT/p).read_text(encoding="utf-8"))
def test_contract():
 c=r("pipeline/06_normalize_activities/contract.json"); assert c["status"]=="implemented"; assert c["optional"] is False; assert "04_garmin_activity_ingest" in c["optional_inputs_from"]; assert "parse_fit_files" in c["prohibited_responsibilities"]; assert "calculate_pws" in c["prohibited_responsibilities"]
def test_registry_statuses_after_06():
 mods=r("config/pipeline_modules.json")["modules"]
 for m in mods[:14]: assert m["status"]=="implemented", m["id"]
 for m in mods[14:]:
  expected = "implemented" if m["id"] in {"15_build_dashboard_payload", "16_persist_local_snapshot", "17_local_api_server", "18_angular_dashboard_ui", "19_packaging_windows"} else "planned"
  assert m["status"]==expected, m["id"]


