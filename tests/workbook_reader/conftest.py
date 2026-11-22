import importlib.util
import sys
import json
import shutil
import uuid
import zipfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "pipeline" / "02_read_xlsx_workbook" / "main.py"
sys.path.insert(0, str(Path(__file__).parent))


@pytest.fixture
def case_root() -> Path:
    root = ROOT / ".tmp_test" / "module02" / uuid.uuid4().hex
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    return root


@pytest.fixture
def module02():
    spec = importlib.util.spec_from_file_location("read_xlsx_workbook", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def column_name(index: int) -> str:
    result = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(ord("A") + remainder) + result
    return result


def escape(value: object) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def write_workbook_manifest(root: Path, workbook_relative_path: str | None, status: str = "found") -> None:
    manifest_dir = root / "data" / "pipeline" / "01_find_input_workbook"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    selected = None
    ready = False
    if workbook_relative_path is not None and status == "found":
        selected = {
            "relative_path": workbook_relative_path,
            "filename": Path(workbook_relative_path).name,
            "extension": ".xlsx",
            "size_bytes": 1,
            "modified_at": "2026-01-01T00:00:00",
            "exists": True,
        }
        ready = True
    payload = {
        "module_id": "01_find_input_workbook",
        "contract_version": "1.0.0",
        "status": status,
        "search_configuration": {
            "filename_pattern": "garmin_export_*.xlsx",
            "search_directories": [".", "data/input"],
            "recursive": False,
            "selection_strategy": "first_path_sorted_ascending",
        },
        "candidates_count": 1 if selected else 0,
        "candidates": [selected] if selected else [],
        "selected_workbook": selected,
        "warnings": [],
        "ready_for_next_module": ready,
    }
    (manifest_dir / "workbook_manifest.json").write_text(json.dumps(payload), encoding="utf-8")


def create_xlsx(path: Path, sheets: list[dict], string_mode: str = "inline") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    shared_values: list[str] = []
    shared_index: dict[str, int] = {}

    def shared_id(value: str) -> int:
        if value not in shared_index:
            shared_index[value] = len(shared_values)
            shared_values.append(value)
        return shared_index[value]

    def cell_xml(row_index: int, col_index: int, value: object) -> str:
        ref = f"{column_name(col_index)}{row_index}"
        if value is None:
            return ""
        if isinstance(value, bool):
            return f'<c r="{ref}" t="b"><v>{1 if value else 0}</v></c>'
        if isinstance(value, (int, float)):
            return f'<c r="{ref}"><v>{value}</v></c>'
        text = escape(value)
        if string_mode == "shared":
            return f'<c r="{ref}" t="s"><v>{shared_id(str(value))}</v></c>'
        return f'<c r="{ref}" t="inlineStr"><is><t>{text}</t></is></c>'

    worksheet_parts: list[str] = []
    for sheet in sheets:
        rows_xml: list[str] = []
        for row_index, row_values in enumerate(sheet.get("rows", []), start=1):
            cells = "".join(cell_xml(row_index, col_index, value) for col_index, value in enumerate(row_values, start=1))
            rows_xml.append(f'<row r="{row_index}">{cells}</row>')
        worksheet_parts.append(
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            f'<sheetData>{"".join(rows_xml)}</sheetData></worksheet>'
        )

    workbook_sheets = []
    rels = []
    for index, sheet in enumerate(sheets, start=1):
        workbook_sheets.append(
            f'<sheet name="{escape(sheet["name"])}" sheetId="{index}" r:id="rId{index}"/>'
        )
        rels.append(
            f'<Relationship Id="rId{index}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{index}.xml"/>'
        )

    content_types = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
    ]
    for index in range(1, len(sheets) + 1):
        content_types.append(
            f'<Override PartName="/xl/worksheets/sheet{index}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        )
    if shared_values:
        content_types.append(
            '<Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>'
        )
    content_types.append("</Types>")

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "".join(content_types))
        archive.writestr(
            "_rels/.rels",
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            '</Relationships>',
        )
        archive.writestr(
            "xl/workbook.xml",
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            f'<sheets>{"".join(workbook_sheets)}</sheets></workbook>',
        )
        archive.writestr(
            "xl/_rels/workbook.xml.rels",
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f'{"".join(rels)}</Relationships>',
        )
        if shared_values:
            items = "".join(f'<si><t>{escape(value)}</t></si>' for value in shared_values)
            archive.writestr(
                "xl/sharedStrings.xml",
                '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                f'{items}</sst>',
            )
        for index, worksheet_xml in enumerate(worksheet_parts, start=1):
            archive.writestr(f"xl/worksheets/sheet{index}.xml", worksheet_xml)


