from __future__ import annotations

import importlib.util
import json
import shutil
from datetime import date, timedelta
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODULE_MAIN = PROJECT_ROOT / "pipeline/10_compute_pws_components/main.py"


def load_module():
    spec = importlib.util.spec_from_file_location("module10_main", MODULE_MAIN)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def make_load_records(days=29, start="2026-01-01", duration=3600):
    first = date.fromisoformat(start)
    records = []
    for i in range(days):
        d = first + timedelta(days=i)
        value = duration
        if i >= 22:
            value = 1800
        records.append({
            "date": d.isoformat(),
            "acwr_ewma": 1.0,
            "acwr_rolling": 1.2,
            "monotony_7d": 99.0,
            "strain_7d": 9999.0,
            "activity_total_duration_seconds": value,
            "activity_total_distance_km": 999,
            "average_power_w": 999,
            "average_hr_bpm": 999,
            "resting_hr_bpm": 50,
            "hrv_last_night_avg_ms": 60,
            "avg_sleep_spo2": 95,
            "avg_sleep_respiration": 14,
        })
    records[-1].update({
        "resting_hr_bpm": 52,
        "hrv_last_night_avg_ms": 54,
        "avg_sleep_spo2": 94,
        "avg_sleep_respiration": 15,
    })
    return records


def make_readiness_records(load_records, score=80):
    return [{
        "date": row["date"],
        "readiness_score": score,
        "readiness_status": "computed" if score is not None else "insufficient_data",
        "readiness_coverage_ratio": 1.0 if score is not None else 0.0,
    } for row in load_records]


def setup_root(tmp_path: Path, load_records=None, readiness_records=None, load_ready=True, readiness_ready=True, write_load=True, write_readiness=True):
    root = tmp_path
    (root / "config").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(PROJECT_ROOT / "config/pws_components_policy_v1.json", root / "config/pws_components_policy_v1.json")
    load_records = load_records if load_records is not None else make_load_records()
    readiness_records = readiness_records if readiness_records is not None else make_readiness_records(load_records)
    if write_load:
        base = root / "data/pipeline/08_compute_load_metrics"
        write_json(base / "load_metrics.json", {"module_id": "08_compute_load_metrics", "records": load_records, "ready_for_next_module": load_ready})
        write_json(base / "load_metrics_schema.json", {"module_id": "08_compute_load_metrics"})
        write_json(base / "load_metrics_quality_report.json", {"module_id": "08_compute_load_metrics"})
        write_json(base / "load_metrics_lineage.json", {"module_id": "08_compute_load_metrics"})
    if write_readiness:
        base = root / "data/pipeline/09_compute_readiness"
        write_json(base / "readiness.json", {"module_id": "09_compute_readiness", "records": readiness_records, "ready_for_next_module": readiness_ready})
        write_json(base / "readiness_schema.json", {"module_id": "09_compute_readiness"})
        write_json(base / "readiness_quality_report.json", {"module_id": "09_compute_readiness"})
        write_json(base / "readiness_lineage.json", {"module_id": "09_compute_readiness"})
    return root


def run_module(root: Path):
    return load_module().execute(root)


def output(root: Path, name="pws_components.json"):
    return root / "data/pipeline/10_compute_pws_components" / name


def records(root: Path):
    return read_json(output(root))["records"]


def by_date(root: Path, value: str):
    return next(row for row in records(root) if row["date"] == value)
