import importlib.util
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "pipeline" / "07_build_daily_features" / "main.py"


def load_module():
    spec = importlib.util.spec_from_file_location("module07_main", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_json(root: Path, rel: str) -> dict:
    return json.loads((root / rel).read_text(encoding="utf-8"))


def daily_payload(records=None, ready=True):
    records = records or [
        {"date": "2026-01-01", "active_kcal": 100, "steps": None, "sleep_seconds": None},
        {"date": "2026-01-02", "active_kcal": 200, "steps": 1234, "sleep_seconds": 3600},
    ]
    return {
        "module_id": "05_normalize_daily_records",
        "contract_version": "1.0.0",
        "policy_version": "garmin_daily_normalization_v1",
        "status": "normalized",
        "records_count": len(records),
        "fields": list(records[0].keys()) if records else ["date"],
        "records": records,
        "missing_values_policy": "preserve_as_null",
        "ready_for_next_module": ready,
    }


def activity(activity_id="a1", date="2026-01-01", duration=1000, distance=5.0, calories=300, hr=150, power=250, speed=10.0, z1=10):
    return {
        "activity_id": activity_id,
        "date": date,
        "start_time_local": f"{date}T07:00:00",
        "activity_type": "running",
        "activity_name": "Run",
        "distance_km": distance,
        "duration_seconds": duration,
        "calories": calories,
        "average_speed_kmh": speed,
        "maximum_speed_kmh": None,
        "average_hr_bpm": hr,
        "maximum_hr_bpm": 170,
        "average_power_w": power,
        "maximum_power_w": 400,
        "elevation_gain_m": 20,
        "elevation_loss_m": 18,
        "hr_zone_1_seconds": z1,
        "hr_zone_2_seconds": 20,
        "hr_zone_3_seconds": 30,
        "hr_zone_4_seconds": 40,
        "hr_zone_5_seconds": 50,
    }


def setup_root(tmp_path: Path, *, records=None, daily_ready=True, activities=None, write_activity=True, write_daily=True):
    root = tmp_path
    (root / "config").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "config" / "daily_features_policy_v1.json", root / "config" / "daily_features_policy_v1.json")
    if write_daily:
        payload = daily_payload(records, daily_ready)
        base05 = root / "data" / "pipeline" / "05_normalize_daily_records"
        write_json(base05 / "daily_records.json", payload)
        write_json(base05 / "daily_records_schema.json", {"module_id": "05_normalize_daily_records", "fields": [{"name": f} for f in payload["fields"]]})
        write_json(base05 / "data_quality_report.json", {"module_id": "05_normalize_daily_records", "ready_for_next_module": daily_ready})
    if write_activity:
        acts = activities or []
        base06 = root / "data" / "pipeline" / "06_normalize_activities"
        write_json(base06 / "activities_normalized.json", {"module_id": "06_normalize_activities", "status": "normalized_from_workbook_only" if acts else "normalized_empty_no_activity_sources", "activities_count": len(acts), "activities": acts, "ready_for_next_module": True})
        grouped = {}
        for act in acts:
            grouped.setdefault(act["date"], []).append(act)
        write_json(base06 / "activities_by_date.json", {"module_id": "06_normalize_activities", "status": "grouped", "activities_by_date": grouped, "ready_for_next_module": True})
        write_json(base06 / "activity_schema.json", {"module_id": "06_normalize_activities"})
        write_json(base06 / "activity_data_quality_report.json", {"module_id": "06_normalize_activities", "status": "normalized_from_workbook_only", "ready_for_next_module": True})
    return root


def run_module(root: Path) -> int:
    return load_module().execute(root)


def output(root: Path, name="daily_features.json") -> dict:
    return read_json(root, f"data/pipeline/07_build_daily_features/{name}")
