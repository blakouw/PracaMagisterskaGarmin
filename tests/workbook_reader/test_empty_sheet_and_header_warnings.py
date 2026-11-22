import json

from xlsx_helpers import create_xlsx, write_workbook_manifest


def test_empty_sheet_empty_headers_and_duplicate_headers(case_root, module02) -> None:
    workbook = case_root / "data" / "input" / "garmin_export_headers.xlsx"
    create_xlsx(
        workbook,
        [
            {"name": "Empty", "rows": []},
            {"name": "Headers", "rows": [[None, "value", "value"], ["x", 1, 2]]},
        ],
    )
    write_workbook_manifest(case_root, "data/input/garmin_export_headers.xlsx")

    assert module02.execute(case_root) == 0

    artifact_dir = case_root / "data" / "pipeline" / "02_read_xlsx_workbook"
    structure = json.loads((artifact_dir / "workbook_structure.json").read_text(encoding="utf-8"))
    empty_summary = structure["sheets"][0]
    header_summary = structure["sheets"][1]

    assert empty_summary["row_count"] == 0
    assert empty_summary["has_header_row"] is False
    assert any("empty" in warning.lower() for warning in empty_summary["warnings"])
    assert header_summary["headers"] == ["__column_A", "value", "value__2"]
    assert any("Empty header" in warning for warning in header_summary["warnings"])
    assert any("Duplicate header" in warning for warning in header_summary["warnings"])
