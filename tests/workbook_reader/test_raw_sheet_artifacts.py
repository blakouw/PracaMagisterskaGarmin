import json

from xlsx_helpers import create_xlsx, write_workbook_manifest


def test_raw_sheet_artifacts_are_written_per_sheet_with_safe_names(case_root, module02) -> None:
    workbook = case_root / "data" / "input" / "garmin_export_multi.xlsx"
    create_xlsx(
        workbook,
        [
            {"name": "Daily Sleep", "rows": [["date"], ["2026-01-01"]]},
            {"name": "Range/Body Composition", "rows": [["weight"], [70]]},
            {"name": "Range Body Composition", "rows": [["weight"], [71]]},
        ],
    )
    write_workbook_manifest(case_root, "data/input/garmin_export_multi.xlsx")

    assert module02.execute(case_root) == 0

    artifact_dir = case_root / "data" / "pipeline" / "02_read_xlsx_workbook"
    raw_manifest = json.loads((artifact_dir / "raw_sheets_manifest.json").read_text(encoding="utf-8"))
    artifact_paths = [sheet["artifact_path"] for sheet in raw_manifest["sheets"]]

    assert len(artifact_paths) == 3
    assert len(set(artifact_paths)) == 3
    assert any(path.endswith("Daily_Sleep.json") for path in artifact_paths)
    assert any(path.endswith("Range_Body_Composition.json") for path in artifact_paths)
    assert any(path.endswith("Range_Body_Composition__2.json") for path in artifact_paths)
    for artifact_path in artifact_paths:
        assert (case_root / artifact_path).is_file()
