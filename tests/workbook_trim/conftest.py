import importlib.util
import json
import shutil
import sys
import uuid
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "pipeline" / "03_trim_workbook" / "main.py"
sys.path.insert(0, str(Path(__file__).parent))


@pytest.fixture
def case_root() -> Path:
    root = ROOT / ".tmp_test" / "module03" / uuid.uuid4().hex
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    return root


@pytest.fixture
def module03():
    spec = importlib.util.spec_from_file_location("trim_workbook", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def copy_policy(root: Path) -> None:
    (root / "config").mkdir(parents=True, exist_ok=True)
    source = ROOT / "config" / "garmin_trim_policy_v1.json"
    target = root / "config" / "garmin_trim_policy_v1.json"
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


def write_module02_artifacts(root: Path, sheets: list[dict], ready: bool = True, status: str = "parsed") -> None:
    artifact_dir = root / "data" / "pipeline" / "02_read_xlsx_workbook"
    raw_dir = artifact_dir / "raw_sheets"
    raw_dir.mkdir(parents=True, exist_ok=True)
    structure_sheets = []
    manifest_sheets = []
    for index, sheet in enumerate(sheets):
        name = sheet["sheet_name"]
        headers = sheet.get("headers", [])
        rows = sheet.get("rows", [])
        filename = f"{name}.json".replace("/", "_").replace(" ", "_")
        raw_path = raw_dir / filename
        raw_payload = {
            "sheet_index": index,
            "sheet_name": name,
            "source_workbook": "fixture.xlsx",
            "header_row_number": 1 if headers else None,
            "headers": headers,
            "row_count": len(rows),
            "column_count": len(headers),
            "rows": rows,
            "warnings": [],
        }
        raw_path.write_text(json.dumps(raw_payload), encoding="utf-8")
        artifact_path = f"data/pipeline/02_read_xlsx_workbook/raw_sheets/{filename}"
        structure_sheets.append({
            "sheet_index": index,
            "sheet_name": name,
            "artifact_filename": filename,
            "row_count": len(rows),
            "column_count": len(headers),
            "headers": headers,
            "has_header_row": bool(headers),
            "warnings": [],
        })
        manifest_sheets.append({
            "sheet_index": index,
            "sheet_name": name,
            "artifact_path": artifact_path,
            "row_count": len(rows),
            "column_count": len(headers),
            "headers": headers,
        })
    structure = {
        "module_id": "02_read_xlsx_workbook",
        "contract_version": "1.0.0",
        "status": status,
        "source_workbook": {"relative_path": "data/input/fixture.xlsx", "filename": "fixture.xlsx"},
        "parser": {"type": "custom_zip_xml_reader", "external_excel_dependencies_used": False, "shared_strings_present": False, "formulas_calculated_by_module": False},
        "sheets_count": len(sheets),
        "sheets": structure_sheets,
        "warnings": [],
        "ready_for_next_module": ready,
    }
    raw_manifest = {
        "module_id": "02_read_xlsx_workbook",
        "contract_version": "1.0.0",
        "source_workbook": {"relative_path": "data/input/fixture.xlsx", "filename": "fixture.xlsx"},
        "artifact_root": "data/pipeline/02_read_xlsx_workbook/raw_sheets",
        "sheets": manifest_sheets,
        "private_data_notice": "fixture",
        "ready_for_next_module": ready,
    }
    (artifact_dir / "workbook_structure.json").write_text(json.dumps(structure), encoding="utf-8")
    (artifact_dir / "raw_sheets_manifest.json").write_text(json.dumps(raw_manifest), encoding="utf-8")


def daily_summary_sheet(extra_headers=None, rows=None):
    headers = ["calendarDate", "activeKilocalories"] + list(extra_headers or [])
    return {
        "sheet_name": "Daily_Summary",
        "headers": headers,
        "rows": rows or [
            {"row_number": 2, "values": {"calendarDate": "2026-01-01", "activeKilocalories": 100, "totalSteps": 1234, "unknown": "drop-me"}},
            {"row_number": 3, "values": {"calendarDate": "2026-01-02", "activeKilocalories": None, "totalSteps": 2345, "unknown": "drop-me-2"}},
        ],
    }


def run_success_fixture(root: Path) -> None:
    copy_policy(root)
    write_module02_artifacts(root, [
        daily_summary_sheet(extra_headers=["totalSteps", "unknown"]),
        {"sheet_name": "Daily_Sleep", "headers": ["calendarDate", "sleepDuration", "extra"], "rows": [{"row_number": 2, "values": {"calendarDate": "2026-01-01", "sleepDuration": 3600, "extra": "drop"}}]},
        {"sheet_name": "Unused_Sheet", "headers": ["x"], "rows": [{"row_number": 2, "values": {"x": 1}}]},
    ])