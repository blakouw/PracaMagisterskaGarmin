from __future__ import annotations

import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MODULE_ID = "02_read_xlsx_workbook"
CONTRACT_VERSION = "1.0.0"
ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_RELATIVE_DIR = Path("data/pipeline") / MODULE_ID
RAW_SHEETS_RELATIVE_DIR = ARTIFACT_RELATIVE_DIR / "raw_sheets"
INPUT_MANIFEST_RELATIVE_PATH = Path("data/pipeline/01_find_input_workbook/workbook_manifest.json")
WORKBOOK_STRUCTURE_NAME = "workbook_structure.json"
RAW_SHEETS_MANIFEST_NAME = "raw_sheets_manifest.json"
RUN_MANIFEST_NAME = "run_manifest.json"
RUN_LOG_NAME = "run_log.txt"
ERRORS_NAME = "errors.json"

NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"


class ModuleError(Exception):
    def __init__(self, code: str, message: str, domain_status: str, context: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.domain_status = domain_status
        self.context = context or {}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def column_letters_to_index(letters: str) -> int:
    result = 0
    for char in letters.upper():
        result = result * 26 + (ord(char) - ord("A") + 1)
    return result


def index_to_column_letters(index: int) -> str:
    letters = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        letters = chr(ord("A") + remainder) + letters
    return letters or "A"


def parse_cell_reference(reference: str) -> tuple[int | None, int | None]:
    match = re.match(r"^([A-Za-z]+)(\d+)$", reference or "")
    if not match:
        return None, None
    return column_letters_to_index(match.group(1)), int(match.group(2))


def parse_number(text: str | None) -> int | float | str | None:
    if text is None or text == "":
        return None
    try:
        if re.match(r"^-?\d+$", text):
            return int(text)
        return float(text)
    except ValueError:
        return text


def read_xml_from_zip(archive: zipfile.ZipFile, name: str, code: str, domain_status: str) -> ET.Element:
    try:
        with archive.open(name) as handle:
            return ET.parse(handle).getroot()
    except KeyError as exc:
        raise ModuleError(code, f"Required XLSX XML part was not found: {name}", domain_status, {"part": name}) from exc
    except ET.ParseError as exc:
        raise ModuleError(code, f"Could not parse XLSX XML part: {name}", domain_status, {"part": name, "error": str(exc)}) from exc


def load_input_manifest(root: Path) -> tuple[dict[str, Any], Path]:
    manifest_path = root / INPUT_MANIFEST_RELATIVE_PATH
    if not manifest_path.is_file():
        raise ModuleError(
            "INPUT_MANIFEST_NOT_FOUND",
            "Workbook manifest from module 01 was not found.",
            "blocked_missing_input_manifest",
            {},
        )
    try:
        manifest = read_json(manifest_path)
    except json.JSONDecodeError as exc:
        raise ModuleError(
            "INPUT_MANIFEST_INVALID",
            "Workbook manifest from module 01 is not valid JSON.",
            "blocked_missing_input_manifest",
            {"error": str(exc)},
        ) from exc
    return manifest, manifest_path


def resolve_selected_workbook(root: Path, manifest: dict[str, Any]) -> tuple[dict[str, Any], Path]:
    if manifest.get("status") != "found" or manifest.get("ready_for_next_module") is not True:
        raise ModuleError(
            "INPUT_WORKBOOK_NOT_SELECTED",
            "Module 01 did not select an input workbook.",
            "blocked_missing_input_workbook",
            {"manifest_status": manifest.get("status"), "ready_for_next_module": manifest.get("ready_for_next_module")},
        )
    selected = manifest.get("selected_workbook")
    if not isinstance(selected, dict) or not selected.get("relative_path"):
        raise ModuleError(
            "INPUT_WORKBOOK_NOT_SELECTED",
            "Module 01 manifest does not contain selected_workbook.relative_path.",
            "blocked_missing_input_workbook",
            {},
        )
    relative_path = Path(str(selected["relative_path"]))
    if relative_path.is_absolute():
        raise ModuleError(
            "INPUT_WORKBOOK_OUTSIDE_ALLOWED_SCOPE",
            "Selected workbook path must be relative to the project root.",
            "blocked_missing_input_workbook",
            {"relative_path": str(selected["relative_path"])},
        )
    workbook_path = (root / relative_path).resolve()
    root_resolved = root.resolve()
    if workbook_path != root_resolved and root_resolved not in workbook_path.parents:
        raise ModuleError(
            "INPUT_WORKBOOK_OUTSIDE_ALLOWED_SCOPE",
            "Selected workbook path points outside the project root.",
            "blocked_missing_input_workbook",
            {"relative_path": str(selected["relative_path"])},
        )
    if not workbook_path.is_file():
        raise ModuleError(
            "INPUT_WORKBOOK_FILE_NOT_FOUND",
            "Selected workbook file does not exist.",
            "blocked_missing_input_workbook",
            {"relative_path": str(selected["relative_path"])},
        )
    return selected, workbook_path


def read_relationships(archive: zipfile.ZipFile) -> dict[str, str]:
    root = read_xml_from_zip(
        archive,
        "xl/_rels/workbook.xml.rels",
        "WORKBOOK_RELATIONSHIP_PARSE_ERROR",
        "parse_failed",
    )
    relationships: dict[str, str] = {}
    for relationship in root.findall(f"{{{NS_PKG_REL}}}Relationship"):
        rel_id = relationship.attrib.get("Id")
        target = relationship.attrib.get("Target")
        if rel_id and target:
            if target.startswith("/"):
                normalized = target.lstrip("/")
            else:
                normalized = "xl/" + target
            relationships[rel_id] = normalized.replace("\\", "/")
    return relationships


def read_workbook_sheets(archive: zipfile.ZipFile, relationships: dict[str, str]) -> list[dict[str, Any]]:
    root = read_xml_from_zip(archive, "xl/workbook.xml", "WORKBOOK_XML_NOT_FOUND", "parse_failed")
    sheets_parent = root.find(f"{{{NS_MAIN}}}sheets")
    if sheets_parent is None:
        return []
    sheets: list[dict[str, Any]] = []
    for index, sheet in enumerate(sheets_parent.findall(f"{{{NS_MAIN}}}sheet")):
        rel_id = sheet.attrib.get(f"{{{NS_REL}}}id")
        path = relationships.get(rel_id or "")
        if not path:
            raise ModuleError(
                "WORKBOOK_RELATIONSHIP_PARSE_ERROR",
                "Worksheet relationship target was not found.",
                "parse_failed",
                {"sheet_name": sheet.attrib.get("name"), "relationship_id": rel_id},
            )
        sheets.append(
            {
                "sheet_index": index,
                "sheet_name": sheet.attrib.get("name", f"Sheet{index + 1}"),
                "xml_path": path,
            }
        )
    return sheets


def read_shared_strings(archive: zipfile.ZipFile) -> tuple[list[str], bool]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return [], False
    root = read_xml_from_zip(archive, "xl/sharedStrings.xml", "SHEET_XML_PARSE_ERROR", "parse_failed")
    strings: list[str] = []
    for item in root.findall(f"{{{NS_MAIN}}}si"):
        parts = [element.text or "" for element in item.iter() if local_name(element.tag) == "t"]
        strings.append("".join(parts))
    return strings, True


def cell_text_from_inline(cell: ET.Element) -> str | None:
    parts = [element.text or "" for element in cell.iter() if local_name(element.tag) == "t"]
    if not parts:
        return None
    return "".join(parts)


def cell_value(cell: ET.Element, shared_strings: list[str]) -> tuple[Any, bool]:
    cell_type = cell.attrib.get("t")
    formula_present = cell.find(f"{{{NS_MAIN}}}f") is not None
    value_element = cell.find(f"{{{NS_MAIN}}}v")
    raw_value = value_element.text if value_element is not None else None

    if cell_type == "inlineStr":
        return cell_text_from_inline(cell), formula_present
    if cell_type == "s":
        index = parse_number(raw_value)
        if isinstance(index, int) and 0 <= index < len(shared_strings):
            return shared_strings[index], formula_present
        return None, formula_present
    if cell_type == "b":
        if raw_value is None:
            return None, formula_present
        return raw_value == "1", formula_present
    if cell_type in {"str", "e"}:
        return raw_value, formula_present
    return parse_number(raw_value), formula_present


def parse_sheet_rows(root: ET.Element, shared_strings: list[str]) -> list[dict[str, Any]]:
    sheet_data = root.find(f"{{{NS_MAIN}}}sheetData")
    if sheet_data is None:
        return []
    rows: list[dict[str, Any]] = []
    for row_position, row in enumerate(sheet_data.findall(f"{{{NS_MAIN}}}row"), start=1):
        row_number = int(row.attrib.get("r", row_position))
        cells: dict[int, Any] = {}
        formula_columns: list[int] = []
        next_column = 1
        for cell in row.findall(f"{{{NS_MAIN}}}c"):
            reference = cell.attrib.get("r", "")
            column_index, _ = parse_cell_reference(reference)
            if column_index is None:
                column_index = next_column
            value, formula_present = cell_value(cell, shared_strings)
            cells[column_index] = value
            if formula_present:
                formula_columns.append(column_index)
            next_column = column_index + 1
        rows.append({"row_number": row_number, "cells": cells, "formula_columns": formula_columns})
    return rows


def is_non_empty_row(row: dict[str, Any]) -> bool:
    return any(value not in (None, "") for value in row["cells"].values())


def build_headers(header_row: dict[str, Any] | None, column_count: int) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    headers: list[str] = []
    seen: dict[str, int] = {}
    for index in range(1, column_count + 1):
        raw = None if header_row is None else header_row["cells"].get(index)
        if raw is None or str(raw).strip() == "":
            base = f"__column_{index_to_column_letters(index)}"
            warnings.append(f"Empty header at column {index_to_column_letters(index)} was replaced with {base}.")
        else:
            base = str(raw).strip()
        count = seen.get(base, 0) + 1
        seen[base] = count
        if count > 1:
            header = f"{base}__{count}"
            warnings.append(f"Duplicate header {base} was renamed to {header}.")
        else:
            header = base
        headers.append(header)
    return headers, warnings


def safe_sheet_filename(sheet_name: str, used: set[str]) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", sheet_name).strip("_")
    safe = re.sub(r"_+", "_", safe) or "Sheet"
    candidate = f"{safe}.json"
    suffix = 2
    while candidate.lower() in used:
        candidate = f"{safe}__{suffix}.json"
        suffix += 1
    used.add(candidate.lower())
    return candidate


def build_sheet_artifact(
    sheet: dict[str, Any],
    sheet_root: ET.Element,
    shared_strings: list[str],
    source_workbook_filename: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    parsed_rows = parse_sheet_rows(sheet_root, shared_strings)
    non_empty_rows = [row for row in parsed_rows if is_non_empty_row(row)]
    warnings: list[str] = []

    if not non_empty_rows:
        warnings.append("Sheet is empty or contains no non-empty rows.")
        raw_artifact = {
            "sheet_index": sheet["sheet_index"],
            "sheet_name": sheet["sheet_name"],
            "source_workbook": source_workbook_filename,
            "header_row_number": None,
            "headers": [],
            "row_count": 0,
            "column_count": 0,
            "rows": [],
            "warnings": warnings,
        }
        summary = {
            "sheet_index": sheet["sheet_index"],
            "sheet_name": sheet["sheet_name"],
            "row_count": 0,
            "column_count": 0,
            "headers": [],
            "has_header_row": False,
            "warnings": warnings,
        }
        return raw_artifact, summary

    header_row = non_empty_rows[0]
    max_column = max(max(row["cells"].keys(), default=0) for row in non_empty_rows)
    headers, header_warnings = build_headers(header_row, max_column)
    warnings.extend(header_warnings)

    data_rows: list[dict[str, Any]] = []
    for row in parsed_rows:
        if row["row_number"] <= header_row["row_number"]:
            continue
        if not row["cells"]:
            continue
        values = {headers[index - 1]: row["cells"].get(index) for index in range(1, max_column + 1)}
        row_payload: dict[str, Any] = {"row_number": row["row_number"], "values": values}
        if row["formula_columns"]:
            row_payload["formula_columns"] = [headers[index - 1] for index in row["formula_columns"] if 1 <= index <= len(headers)]
        data_rows.append(row_payload)

    raw_artifact = {
        "sheet_index": sheet["sheet_index"],
        "sheet_name": sheet["sheet_name"],
        "source_workbook": source_workbook_filename,
        "header_row_number": header_row["row_number"],
        "headers": headers,
        "row_count": len(data_rows),
        "column_count": max_column,
        "rows": data_rows,
        "warnings": warnings,
    }
    summary = {
        "sheet_index": sheet["sheet_index"],
        "sheet_name": sheet["sheet_name"],
        "row_count": len(data_rows),
        "column_count": max_column,
        "headers": headers,
        "has_header_row": True,
        "warnings": warnings,
    }
    return raw_artifact, summary


def parse_workbook(workbook_path: Path, selected_workbook: dict[str, Any], artifact_dir: Path, root: Path) -> dict[str, Any]:
    raw_dir = artifact_dir / "raw_sheets"
    raw_dir.mkdir(parents=True, exist_ok=True)
    for stale_file in raw_dir.glob("*.json"):
        stale_file.unlink()

    try:
        archive = zipfile.ZipFile(workbook_path, "r")
    except zipfile.BadZipFile as exc:
        raise ModuleError("INVALID_XLSX_ARCHIVE", "Selected workbook is not a valid XLSX ZIP archive.", "invalid_xlsx", {}) from exc

    with archive:
        relationships = read_relationships(archive)
        sheets = read_workbook_sheets(archive, relationships)
        shared_strings, shared_strings_present = read_shared_strings(archive)

        used_filenames: set[str] = set()
        sheet_summaries: list[dict[str, Any]] = []
        raw_manifest_sheets: list[dict[str, Any]] = []
        generated_raw_artifacts: list[str] = []
        all_warnings: list[str] = []

        for sheet in sheets:
            sheet_root = read_xml_from_zip(archive, sheet["xml_path"], "SHEET_XML_PARSE_ERROR", "parse_failed")
            raw_artifact, summary = build_sheet_artifact(sheet, sheet_root, shared_strings, workbook_path.name)
            artifact_filename = safe_sheet_filename(sheet["sheet_name"], used_filenames)
            artifact_path = raw_dir / artifact_filename
            write_json(artifact_path, raw_artifact)
            artifact_relative_path = rel(artifact_path, root)
            generated_raw_artifacts.append(artifact_relative_path)

            summary["artifact_filename"] = artifact_filename
            sheet_summaries.append(summary)
            raw_manifest_sheets.append(
                {
                    "sheet_index": sheet["sheet_index"],
                    "sheet_name": sheet["sheet_name"],
                    "artifact_path": artifact_relative_path,
                    "row_count": summary["row_count"],
                    "column_count": summary["column_count"],
                    "headers": summary["headers"],
                }
            )
            all_warnings.extend(f"{sheet['sheet_name']}: {warning}" for warning in summary["warnings"])

    source = {
        "relative_path": selected_workbook["relative_path"],
        "filename": selected_workbook.get("filename", workbook_path.name),
    }
    workbook_structure = {
        "module_id": MODULE_ID,
        "contract_version": CONTRACT_VERSION,
        "status": "parsed",
        "source_workbook": source,
        "parser": {
            "type": "custom_zip_xml_reader",
            "external_excel_dependencies_used": False,
            "shared_strings_present": shared_strings_present,
            "formulas_calculated_by_module": False,
        },
        "sheets_count": len(sheet_summaries),
        "sheets": sheet_summaries,
        "warnings": all_warnings,
        "ready_for_next_module": True,
    }
    raw_sheets_manifest = {
        "module_id": MODULE_ID,
        "contract_version": CONTRACT_VERSION,
        "source_workbook": source,
        "artifact_root": RAW_SHEETS_RELATIVE_DIR.as_posix(),
        "sheets": raw_manifest_sheets,
        "private_data_notice": "Raw sheet artifacts may contain private health and activity data and must not be committed to version control.",
        "ready_for_next_module": True,
    }
    return {
        "workbook_structure": workbook_structure,
        "raw_sheets_manifest": raw_sheets_manifest,
        "generated_raw_artifacts": generated_raw_artifacts,
        "shared_strings_present": shared_strings_present,
    }


def blocked_structure(domain_status: str, message: str, selected_workbook: dict[str, Any] | None = None) -> dict[str, Any]:
    source = None
    if selected_workbook is not None:
        source = {
            "relative_path": selected_workbook.get("relative_path"),
            "filename": selected_workbook.get("filename"),
        }
    return {
        "module_id": MODULE_ID,
        "contract_version": CONTRACT_VERSION,
        "status": domain_status,
        "source_workbook": source,
        "parser": {
            "type": "custom_zip_xml_reader",
            "external_excel_dependencies_used": False,
            "shared_strings_present": False,
            "formulas_calculated_by_module": False,
        },
        "sheets_count": 0,
        "sheets": [],
        "warnings": [message],
        "ready_for_next_module": False,
    }


def blocked_raw_manifest(domain_status: str, selected_workbook: dict[str, Any] | None = None) -> dict[str, Any]:
    source = None
    if selected_workbook is not None:
        source = {
            "relative_path": selected_workbook.get("relative_path"),
            "filename": selected_workbook.get("filename"),
        }
    return {
        "module_id": MODULE_ID,
        "contract_version": CONTRACT_VERSION,
        "source_workbook": source,
        "artifact_root": RAW_SHEETS_RELATIVE_DIR.as_posix(),
        "sheets": [],
        "private_data_notice": "Raw sheet artifacts may contain private health and activity data and must not be committed to version control.",
        "ready_for_next_module": False,
        "status": domain_status,
    }


def write_run_log(
    path: Path,
    started_at: str,
    finished_at: str,
    execution_status: str,
    domain_status: str,
    selected_workbook: dict[str, Any] | None,
    structure: dict[str, Any] | None,
    errors: list[dict[str, Any]],
) -> None:
    lines = [
        f"module_id={MODULE_ID}",
        f"started_at={started_at}",
        f"input_manifest={INPUT_MANIFEST_RELATIVE_PATH.as_posix()}",
    ]
    if selected_workbook is not None:
        lines.append(f"selected_workbook={selected_workbook.get('relative_path')}")
    else:
        lines.append("selected_workbook=none")
    lines.append("parser=custom_zip_xml_reader")
    if structure is not None:
        parser = structure.get("parser", {})
        lines.append(f"shared_strings_present={parser.get('shared_strings_present')}")
        lines.append(f"sheets_count={structure.get('sheets_count', 0)}")
        for sheet in structure.get("sheets", []):
            lines.append(
                f"sheet={sheet.get('sheet_name')} rows={sheet.get('row_count')} columns={sheet.get('column_count')}"
            )
            for warning in sheet.get("warnings", []):
                lines.append(f"warning={sheet.get('sheet_name')}: {warning}")
        for warning in structure.get("warnings", []):
            if not any(warning.endswith(f": {sheet_warning}") for sheet in structure.get("sheets", []) for sheet_warning in sheet.get("warnings", [])):
                lines.append(f"warning={warning}")
    lines.append("keep_drop_filtering_performed=false")
    lines.append("domain_calculations_performed=false")
    if errors:
        for error in errors:
            lines.append(f"error={error['code']}: {error['message']}")
    lines.append(f"finished_at={finished_at}")
    lines.append(f"execution_status={execution_status}")
    lines.append(f"domain_status={domain_status}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def execute(root: Path = ROOT) -> int:
    started_at = now_iso()
    artifact_dir = root / ARTIFACT_RELATIVE_DIR
    artifact_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = root / RAW_SHEETS_RELATIVE_DIR
    raw_dir.mkdir(parents=True, exist_ok=True)

    workbook_structure_path = artifact_dir / WORKBOOK_STRUCTURE_NAME
    raw_sheets_manifest_path = artifact_dir / RAW_SHEETS_MANIFEST_NAME
    run_manifest_path = artifact_dir / RUN_MANIFEST_NAME
    run_log_path = artifact_dir / RUN_LOG_NAME
    errors_path = artifact_dir / ERRORS_NAME

    generated_artifacts = [
        (ARTIFACT_RELATIVE_DIR / WORKBOOK_STRUCTURE_NAME).as_posix(),
        (ARTIFACT_RELATIVE_DIR / RAW_SHEETS_MANIFEST_NAME).as_posix(),
        (ARTIFACT_RELATIVE_DIR / RUN_MANIFEST_NAME).as_posix(),
        (ARTIFACT_RELATIVE_DIR / RUN_LOG_NAME).as_posix(),
        (ARTIFACT_RELATIVE_DIR / ERRORS_NAME).as_posix(),
    ]

    errors: list[dict[str, Any]] = []
    execution_status = "success"
    domain_status = "parsed"
    selected_workbook: dict[str, Any] | None = None
    structure: dict[str, Any] | None = None

    try:
        manifest, _ = load_input_manifest(root)
        selected_workbook, workbook_path = resolve_selected_workbook(root, manifest)
        parsed = parse_workbook(workbook_path, selected_workbook, artifact_dir, root)
        structure = parsed["workbook_structure"]
        write_json(workbook_structure_path, structure)
        write_json(raw_sheets_manifest_path, parsed["raw_sheets_manifest"])
        generated_artifacts.extend(parsed["generated_raw_artifacts"])
    except ModuleError as exc:
        execution_status = "failed"
        domain_status = exc.domain_status
        errors.append({"code": exc.code, "message": exc.message, "context": exc.context})
        structure = blocked_structure(domain_status, exc.message, selected_workbook)
        write_json(workbook_structure_path, structure)
        write_json(raw_sheets_manifest_path, blocked_raw_manifest(domain_status, selected_workbook))
    except Exception as exc:
        execution_status = "failed"
        domain_status = "parse_failed"
        errors.append({"code": "UNHANDLED_ERROR", "message": str(exc), "context": {}})
        structure = blocked_structure(domain_status, str(exc), selected_workbook)
        write_json(workbook_structure_path, structure)
        write_json(raw_sheets_manifest_path, blocked_raw_manifest(domain_status, selected_workbook))

    finished_at = now_iso()
    write_json(errors_path, {"module_id": MODULE_ID, "errors": errors})
    write_run_log(run_log_path, started_at, finished_at, execution_status, domain_status, selected_workbook, structure, errors)
    write_json(
        run_manifest_path,
        {
            "module_id": MODULE_ID,
            "module_version": CONTRACT_VERSION,
            "started_at": started_at,
            "finished_at": finished_at,
            "execution_status": execution_status,
            "domain_status": domain_status,
            "inputs": [
                INPUT_MANIFEST_RELATIVE_PATH.as_posix(),
                "selected workbook referenced by the input manifest",
            ],
            "generated_artifacts": generated_artifacts,
            "log_file": (ARTIFACT_RELATIVE_DIR / RUN_LOG_NAME).as_posix(),
            "errors_file": (ARTIFACT_RELATIVE_DIR / ERRORS_NAME).as_posix(),
        },
    )
    return 0 if execution_status == "success" else 1


def main() -> int:
    return execute(ROOT)


if __name__ == "__main__":
    sys.exit(main())
