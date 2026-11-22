from __future__ import annotations

import importlib.util
import json
import shutil
from datetime import date, timedelta
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODULE_MAIN = PROJECT_ROOT / "pipeline/08_compute_load_metrics/main.py"


def load_module():
    spec = importlib.util.spec_from_file_location("module08_main", MODULE_MAIN)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def make_records(values, start="2026-01-01", dates=None, extra=None):
    if dates is None:
        first = date.fromisoformat(start)
        dates = [(first + timedelta(days=i)).isoformat() for i in range(len(values))]
    records = []
    for current_date, value in zip(dates, values):
        record = {
            "date": current_date,
            "active_kcal": value,
            "steps": None,
            "activity_total_calories": 9999,
        }
        if extra:
            record.update(extra)
        records.append(record)
    return records


def setup_root(tmp_path: Path, records=None, ready=True, write_features=True, activities=None):
    root = tmp_path
    config_dir = root / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(PROJECT_ROOT / "config/load_metrics_policy_v1.json", config_dir / "load_metrics_policy_v1.json")
    if write_features:
        records = records if records is not None else make_records([100, 200, 300])
        base = root / "data/pipeline/07_build_daily_features"
        write_json(
            base / "daily_features.json",
            {
                "module_id": "07_build_daily_features",
                "contract_version": "1.0.0",
                "policy_version": "daily_features_policy_v1",
                "status": "built",
                "records_count": len(records),
                "records": records,
                "ready_for_next_module": ready,
            },
        )
        write_json(base / "daily_features_schema.json", {"module_id": "07_build_daily_features", "fields": []})
        write_json(base / "daily_features_quality_report.json", {"module_id": "07_build_daily_features", "ready_for_next_module": ready})
        write_json(base / "daily_features_lineage.json", {"module_id": "07_build_daily_features", "field_groups": []})
    if activities is not None:
        write_json(
            root / "data/pipeline/06_normalize_activities/activities_normalized.json",
            {
                "module_id": "06_normalize_activities",
                "status": "normalized_from_workbook_only",
                "activities": activities,
                "ready_for_next_module": True,
            },
        )
    return root


def run_module(root: Path):
    module = load_module()
    return module.execute(root)


def output(root: Path, name: str = "load_metrics.json"):
    return root / "data/pipeline/08_compute_load_metrics" / name


def load_output_records(root: Path):
    return read_json(output(root))["records"]


def by_date(records, value):
    return next(record for record in records if record["date"] == value)
