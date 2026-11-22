import json

from xlsx_helpers import create_xlsx, write_workbook_manifest


def test_parse_minimal_xlsx(case_root, module02) -> None:
    workbook = case_root / "data" / "input" / "garmin_export_fixture.xlsx"
    create_xlsx(workbook, [{"name": "Daily_Summary", "rows": [["calendarDate", "totalSteps"], ["2026-05-20", 10230]]}])
    write_workbook_manifest(case_root, "data/input/garmin_export_fixture.xlsx")

    exit_code = module02.execute(case_root)

    artifact_dir = case_root / "data" / "pipeline" / "02_read_xlsx_workbook"
    structure = json.loads((artifact_dir / "workbook_structure.json").read_text(encoding="utf-8"))
    raw_manifest = json.loads((artifact_dir / "raw_sheets_manifest.json").read_text(encoding="utf-8"))

    assert exit_code == 0
    assert structure["status"] == "parsed"
    assert structure["parser"]["type"] == "custom_zip_xml_reader"
    assert structure["sheets_count"] == 1
    assert structure["sheets"][0]["sheet_name"] == "Daily_Summary"
    assert structure["sheets"][0]["headers"] == ["calendarDate", "totalSteps"]
    assert raw_manifest["sheets"][0]["artifact_path"].endswith("Daily_Summary.json")
