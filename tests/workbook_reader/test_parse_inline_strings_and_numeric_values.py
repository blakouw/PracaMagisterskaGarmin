import json

from xlsx_helpers import create_xlsx, write_workbook_manifest


def test_parse_inline_strings_numeric_booleans_and_empty_values(case_root, module02) -> None:
    workbook = case_root / "data" / "input" / "garmin_export_inline.xlsx"
    create_xlsx(
        workbook,
        [{"name": "Inline", "rows": [["label", "score", "flag", "blank", "tail"], ["row1", 12.5, True, None, "end"]]}],
    )
    write_workbook_manifest(case_root, "data/input/garmin_export_inline.xlsx")

    assert module02.execute(case_root) == 0

    raw_manifest = json.loads(
        (case_root / "data" / "pipeline" / "02_read_xlsx_workbook" / "raw_sheets_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    raw_sheet = json.loads((case_root / raw_manifest["sheets"][0]["artifact_path"]).read_text(encoding="utf-8"))
    values = raw_sheet["rows"][0]["values"]

    assert values["label"] == "row1"
    assert values["score"] == 12.5
    assert values["flag"] is True
    assert values["blank"] is None
    assert values["tail"] == "end"
