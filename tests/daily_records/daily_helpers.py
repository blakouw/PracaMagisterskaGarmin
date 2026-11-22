import csv
import importlib.util
import json
import shutil
import sys
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "pipeline" / "05_normalize_daily_records" / "main.py"


@pytest.fixture
def case_root() -> Path:
    root = ROOT / ".tmp_test" / "module05" / uuid.uuid4().hex
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    return root


@pytest.fixture
def module05():
    spec = importlib.util.spec_from_file_location("normalize_daily_records", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def copy_policy(root: Path) -> None:
    (root / "config").mkdir(parents=True, exist_ok=True)
    target = root / "config" / "garmin_daily_normalization_v1.json"
    target.write_text((ROOT / "config" / "garmin_daily_normalization_v1.json").read_text(encoding="utf-8"), encoding="utf-8")


def load_policy(root: Path) -> dict:
    return read_json(root / "config" / "garmin_daily_normalization_v1.json")


def write_policy(root: Path, policy: dict) -> None:
    (root / "config").mkdir(parents=True, exist_ok=True)
    (root / "config" / "garmin_daily_normalization_v1.json").write_text(json.dumps(policy), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, object]], headers: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if headers is None:
        headers = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({h: "" if row.get(h) is None else row.get(h) for h in headers})


def write_trim_artifacts(root: Path, sheets: dict[str, list[dict[str, object]]], ready: bool = True) -> None:
    base = root / "data" / "pipeline" / "03_trim_workbook"
    csv_root = base / "trimmed_sheets"
    csv_root.mkdir(parents=True, exist_ok=True)
    manifest_sheets = []
    for name, rows in sheets.items():
        path = csv_root / f"{name}.csv"
        write_csv(path, rows)
        manifest_sheets.append({"sheet_name": name, "classification": "KEEP_REQUIRED" if name == "Daily_Summary" else "KEEP_OPTIONAL", "artifact_path": f"data/pipeline/03_trim_workbook/trimmed_sheets/{name}.csv", "row_count": len(rows)})
    manifest = {"module_id": "03_trim_workbook", "status": "trimmed", "sheets": manifest_sheets, "missing_sheets": [], "dropped_sheets": [], "ready_for_next_module": ready}
    (base / "trimmed_sheets_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def base_sheets() -> dict[str, list[dict[str, object]]]:
    return {
        "Daily_Summary": [
            {"calendarDate": "2026-05-20", "activeKilocalories": "580", "totalSteps": "10000", "averageStressLevel": "30"},
            {"calendarDate": "2026-05-21", "activeKilocalories": "", "totalSteps": "", "averageStressLevel": "35"},
        ],
        "Daily_Sleep": [
            {"calendarDate": "2026-05-20", "sleepDuration": "27000", "averageSpo2": "95"},
            {"calendarDate": "2026-05-22", "sleepDuration": "28000", "averageSpo2": "96"},
        ],
    }


def run_success_fixture(root: Path) -> None:
    copy_policy(root)
    write_trim_artifacts(root, base_sheets())


def output_dir(root: Path) -> Path:
    return root / "data" / "pipeline" / "05_normalize_daily_records"
