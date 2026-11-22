from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODULE_MAIN = PROJECT_ROOT / "pipeline/09_compute_readiness/main.py"


def load_module():
    spec = importlib.util.spec_from_file_location("module09_main", MODULE_MAIN)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def base_record(**overrides):
    record = {
        "date": "2026-01-01",
        "active_kcal": 500,
        "load_active_kcal": 500,
        "sleep_seconds": 28800,
        "hrv_last_night_avg_ms": 60,
        "hrv_weekly_avg_ms": 55,
        "hrv_baseline_balanced_low_ms": 50,
        "hrv_baseline_balanced_upper_ms": 70,
        "avg_stress": 30,
        "resting_hr_bpm": 52,
        "resting_hr_baseline_bpm": 50,
        "acwr_ewma": 1.0,
        "acwr_rolling": 1.2,
    }
    record.update(overrides)
    return record


def setup_root(tmp_path: Path, records=None, ready=True, write_load=True):
    root = tmp_path
    config_dir = root / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(PROJECT_ROOT / "config/readiness_policy_v1.json", config_dir / "readiness_policy_v1.json")
    if write_load:
        records = records if records is not None else [base_record()]
        base = root / "data/pipeline/08_compute_load_metrics"
        write_json(
            base / "load_metrics.json",
            {
                "module_id": "08_compute_load_metrics",
                "contract_version": "1.0.0",
                "policy_version": "load_metrics_policy_v1",
                "status": "computed",
                "records_count": len(records),
                "records": records,
                "ready_for_next_module": ready,
            },
        )
        write_json(base / "load_metrics_schema.json", {"module_id": "08_compute_load_metrics", "fields": []})
        write_json(base / "load_metrics_quality_report.json", {"module_id": "08_compute_load_metrics", "ready_for_next_module": ready})
        write_json(base / "load_metrics_lineage.json", {"module_id": "08_compute_load_metrics", "metric_groups": []})
    return root


def run_module(root: Path):
    return load_module().execute(root)


def output(root: Path, name: str = "readiness.json"):
    return root / "data/pipeline/09_compute_readiness" / name


def records(root: Path):
    return read_json(output(root))["records"]


def first_record(root: Path):
    return records(root)[0]
