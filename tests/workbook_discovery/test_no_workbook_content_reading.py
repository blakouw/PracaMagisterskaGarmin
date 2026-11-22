from __future__ import annotations

from pathlib import Path

import pytest

from synthetic_input_factory import create_file, execute, load_module, make_case_root, selected_relative_path


def test_empty_invalid_xlsx_candidate_can_be_selected_without_parsing(tmp_path: Path) -> None:
    root = make_case_root(tmp_path)
    create_file(root, "data/input/garmin_export_2026-05-01.xlsx", b"")

    assert execute(root) == 0
    assert selected_relative_path(root) == "data/input/garmin_export_2026-05-01.xlsx"


def test_module_01_never_opens_workbook_file_contents(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = make_case_root(tmp_path)
    create_file(root, "data/input/garmin_export_2026-05-01.xlsx")
    module = load_module("find_input_workbook_no_content_reading")
    original_open = Path.open
    opened_workbooks: list[str] = []

    def guarded_open(self: Path, *args, **kwargs):
        if self.name.startswith("garmin_export_") and self.suffix == ".xlsx":
            opened_workbooks.append(str(self))
            raise AssertionError("Module 01 must not open workbook contents")
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_open)

    assert module.execute(root) == 0
    assert opened_workbooks == []


def test_module_01_source_does_not_import_xlsx_parsers() -> None:
    source = (Path(__file__).resolve().parents[2] / "pipeline" / "01_find_input_workbook" / "main.py").read_text(
        encoding="utf-8"
    )
    forbidden_terms = ["zipfile", "openpyxl", "pandas", "load_workbook", "read_excel", "xml.etree"]
    assert [term for term in forbidden_terms if term in source] == []
