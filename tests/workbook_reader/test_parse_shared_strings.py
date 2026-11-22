import json

from xlsx_helpers import create_xlsx, write_workbook_manifest


def test_parse_shared_strings(case_root, module02) -> None:
    workbook = case_root / "data" / "input" / "garmin_export_shared.xlsx"
    create_xlsx(
        workbook,
        [{"name": "Shared", "rows": [["name", "sport"], ["run", "cycling"]]}],
        string_mode="shared",
    )
    write_workbook_manifest(case_root, "data/input/garmin_export_shared.xlsx")

    assert module02.execute(case_root) == 0

    artifact_dir = case_root / "data" / "pipeline" / "02_read_xlsx_workbook"
    structure = json.loads((artifact_dir / "workbook_structure.json").read_text(encoding="utf-8"))
    raw_manifest = json.loads((artifact_dir / "raw_sheets_manifest.json").read_text(encoding="utf-8"))
    raw_sheet_path = case_root / raw_manifest["sheets"][0]["artifact_path"]
    raw_sheet = json.loads(raw_sheet_path.read_text(encoding="utf-8"))

    assert structure["parser"]["shared_strings_present"] is True
    assert raw_sheet["rows"][0]["values"] == {"name": "run", "sport": "cycling"}
