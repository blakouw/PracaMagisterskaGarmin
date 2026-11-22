from __future__ import annotations

import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MODULE_ID = "03_trim_workbook"
CONTRACT_VERSION = "1.0.0"
ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_RELATIVE_DIR = Path("data/pipeline") / MODULE_ID
TRIMMED_RELATIVE_DIR = ARTIFACT_RELATIVE_DIR / "trimmed_sheets"
WORKBOOK_STRUCTURE_RELATIVE_PATH = Path("data/pipeline/02_read_xlsx_workbook/workbook_structure.json")
RAW_SHEETS_MANIFEST_RELATIVE_PATH = Path("data/pipeline/02_read_xlsx_workbook/raw_sheets_manifest.json")
TRIM_POLICY_RELATIVE_PATH = Path("config/garmin_trim_policy_v1.json")


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


def safe_filename(name: str, used: set[str], suffix: str) -> str:
    base = re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("_")
    base = re.sub(r"_+", "_", base) or "Sheet"
    candidate = f"{base}{suffix}"
    index = 2
    while candidate.lower() in used:
        candidate = f"{base}__{index}{suffix}"
        index += 1
    used.add(candidate.lower())
    return candidate


def load_required_json(root: Path, relative_path: Path, code: str, status: str) -> Any:
    path = root / relative_path
    if not path.is_file():
        raise ModuleError(code, f"Required input artifact was not found: {relative_path.as_posix()}", status, {})
    try:
        return read_json(path)
    except json.JSONDecodeError as exc:
        raise ModuleError(code, f"Input artifact is not valid JSON: {relative_path.as_posix()}", "invalid_input_artifacts", {"error": str(exc)}) from exc


def validate_policy(policy: dict[str, Any]) -> dict[str, dict[str, Any]]:
    expected = {
        "policy_version": "garmin_trim_policy_v1",
        "source_type": "raw_sheet_artifacts_from_module_02",
        "selection_mode": "explicit_allowlist",
        "sheet_matching_strategy": "exact_name",
        "column_matching_strategy": "exact_name",
    }
    for key, value in expected.items():
        if policy.get(key) != value:
            raise ModuleError("TRIM_POLICY_INVALID", f"Invalid trim policy field {key}.", "invalid_trim_policy", {"expected": value, "actual": policy.get(key)})
    if policy.get("preserve_raw_values") is not True or policy.get("perform_domain_transformations") is not False:
        raise ModuleError("TRIM_POLICY_INVALID", "Trim policy must preserve raw values and disable domain transformations.", "invalid_trim_policy", {})
    sheets = policy.get("sheets")
    if not isinstance(sheets, list) or not sheets:
        raise ModuleError("TRIM_POLICY_INVALID", "Trim policy must define a non-empty sheets list.", "invalid_trim_policy", {})
    by_name: dict[str, dict[str, Any]] = {}
    for sheet in sheets:
        name = sheet.get("sheet_name")
        requirement = sheet.get("requirement")
        if not name or requirement not in {"required", "optional"}:
            raise ModuleError("TRIM_POLICY_INVALID", "Each policy sheet must define sheet_name and requirement.", "invalid_trim_policy", {"sheet": sheet})
        sheet.setdefault("required_columns", [])
        sheet.setdefault("optional_columns", [])
        by_name[name] = sheet
    return by_name


def validate_inputs(root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, dict[str, Any]]]:
    structure = load_required_json(root, WORKBOOK_STRUCTURE_RELATIVE_PATH, "WORKBOOK_STRUCTURE_NOT_FOUND", "blocked_missing_input_manifest")
    raw_manifest = load_required_json(root, RAW_SHEETS_MANIFEST_RELATIVE_PATH, "RAW_SHEETS_MANIFEST_NOT_FOUND", "blocked_missing_input_manifest")
    policy = load_required_json(root, TRIM_POLICY_RELATIVE_PATH, "TRIM_POLICY_NOT_FOUND", "invalid_trim_policy")
    policy_by_sheet = validate_policy(policy)
    if structure.get("status") != "parsed" or structure.get("ready_for_next_module") is not True:
        raise ModuleError("WORKBOOK_STRUCTURE_NOT_FOUND", "Workbook structure is not parsed or not ready for next module.", "invalid_input_artifacts", {"status": structure.get("status")})
    if raw_manifest.get("ready_for_next_module") is not True:
        raise ModuleError("RAW_SHEETS_MANIFEST_NOT_FOUND", "Raw sheets manifest is not ready for next module.", "invalid_input_artifacts", {})
    return structure, raw_manifest, policy, policy_by_sheet


def load_raw_sheet(root: Path, artifact_path: str) -> dict[str, Any]:
    relative_path = Path(artifact_path)
    if relative_path.is_absolute():
        raise ModuleError("RAW_SHEET_ARTIFACT_NOT_FOUND", "Raw sheet artifact path must be relative to the project root.", "invalid_input_artifacts", {"artifact_path": artifact_path})
    path = (root / relative_path).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ModuleError("RAW_SHEET_ARTIFACT_NOT_FOUND", "Raw sheet artifact path is outside project root.", "invalid_input_artifacts", {"artifact_path": artifact_path})
    if not path.is_file():
        raise ModuleError("RAW_SHEET_ARTIFACT_NOT_FOUND", "Raw sheet artifact referenced by manifest was not found.", "invalid_input_artifacts", {"artifact_path": artifact_path})
    return read_json(path)


def classify_columns(headers: list[str], policy_sheet: dict[str, Any]) -> dict[str, Any]:
    present = set(headers)
    required = list(policy_sheet.get("required_columns", []))
    optional = list(policy_sheet.get("optional_columns", []))
    kept_required = [column for column in required if column in present]
    kept_optional = [column for column in optional if column in present]
    kept = kept_required + kept_optional
    missing_required = [column for column in required if column not in present]
    missing_optional = [column for column in optional if column not in present]
    dropped = [column for column in headers if column not in set(kept)]
    classifications = []
    for column in kept_required:
        classifications.append({"column_name": column, "classification": "KEEP_REQUIRED"})
    for column in kept_optional:
        classifications.append({"column_name": column, "classification": "KEEP_OPTIONAL"})
    for column in dropped:
        classifications.append({"column_name": column, "classification": "DROP_NOT_USED"})
    for column in missing_required:
        classifications.append({"column_name": column, "classification": "MISSING_REQUIRED"})
    for column in missing_optional:
        classifications.append({"column_name": column, "classification": "MISSING_OPTIONAL"})
    return {
        "kept_required": kept_required,
        "kept_optional": kept_optional,
        "kept_columns": kept,
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "dropped_columns": dropped,
        "classifications": classifications,
    }


def write_trimmed_csv(path: Path, headers: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            values = row.get("values", {})
            writer.writerow({column: values.get(column, "") for column in headers})


def process(root: Path, artifact_dir: Path) -> dict[str, Any]:
    structure, raw_manifest, policy, policy_by_sheet = validate_inputs(root)
    trimmed_dir = root / TRIMMED_RELATIVE_DIR
    trimmed_dir.mkdir(parents=True, exist_ok=True)
    for stale_file in trimmed_dir.glob("*.csv"):
        stale_file.unlink()

    present_sheet_names = {sheet["sheet_name"] for sheet in raw_manifest.get("sheets", [])}
    raw_by_name = {sheet["sheet_name"]: sheet for sheet in raw_manifest.get("sheets", [])}
    used_csv_names: set[str] = set()
    kept_sheets: list[dict[str, Any]] = []
    dropped_sheets: list[dict[str, Any]] = []
    missing_sheets: list[dict[str, Any]] = []
    warnings: list[str] = []
    errors: list[dict[str, Any]] = []
    generated_csv: list[str] = []
    total_source_columns = 0
    total_kept_columns = 0
    total_dropped_columns = 0
    required_columns_missing: list[dict[str, Any]] = []
    optional_columns_missing: list[dict[str, Any]] = []

    for sheet_info in raw_manifest.get("sheets", []):
        sheet_name = sheet_info["sheet_name"]
        if sheet_name not in policy_by_sheet:
            dropped_sheets.append({"sheet_name": sheet_name, "classification": "DROP_NOT_USED"})
            continue
        policy_sheet = policy_by_sheet[sheet_name]
        raw_sheet = load_raw_sheet(root, sheet_info["artifact_path"])
        headers = list(raw_sheet.get("headers", []))
        total_source_columns += len(headers)
        column_result = classify_columns(headers, policy_sheet)
        total_kept_columns += len(column_result["kept_columns"])
        total_dropped_columns += len(column_result["dropped_columns"])
        classification = "KEEP_REQUIRED" if policy_sheet["requirement"] == "required" else "KEEP_OPTIONAL"
        csv_filename = safe_filename(sheet_name, used_csv_names, ".csv")
        csv_path = root / TRIMMED_RELATIVE_DIR / csv_filename
        write_trimmed_csv(csv_path, column_result["kept_columns"], raw_sheet.get("rows", []))
        artifact_path = rel(csv_path, root)
        generated_csv.append(artifact_path)
        for column in column_result["missing_required"]:
            required_columns_missing.append({"sheet_name": sheet_name, "column_name": column})
        for column in column_result["missing_optional"]:
            optional_columns_missing.append({"sheet_name": sheet_name, "column_name": column})
        if column_result["missing_optional"]:
            warnings.append(f"{sheet_name}: missing optional columns: {', '.join(column_result['missing_optional'])}")
        if raw_sheet.get("row_count", 0) == 0:
            warnings.append(f"{sheet_name}: kept sheet is empty.")
        kept_sheets.append(
            {
                "sheet_name": sheet_name,
                "classification": classification,
                "artifact_path": artifact_path,
                "row_count": raw_sheet.get("row_count", 0),
                "kept_columns": column_result["kept_columns"],
                "kept_required_columns": column_result["kept_required"],
                "kept_optional_columns": column_result["kept_optional"],
                "missing_required_columns": column_result["missing_required"],
                "missing_optional_columns": column_result["missing_optional"],
                "dropped_columns": column_result["dropped_columns"],
                "dropped_columns_count": len(column_result["dropped_columns"]),
                "column_classifications": column_result["classifications"],
            }
        )

    for sheet_name, policy_sheet in policy_by_sheet.items():
        if sheet_name not in present_sheet_names:
            classification = "MISSING_REQUIRED" if policy_sheet["requirement"] == "required" else "MISSING_OPTIONAL"
            missing_sheets.append({"sheet_name": sheet_name, "classification": classification})
            if classification == "MISSING_OPTIONAL":
                warnings.append(f"Missing optional sheet: {sheet_name}")

    missing_required_sheets = [sheet for sheet in missing_sheets if sheet["classification"] == "MISSING_REQUIRED"]
    if missing_required_sheets:
        for sheet in missing_required_sheets:
            errors.append({"code": "REQUIRED_SHEET_MISSING", "message": f"Required sheet is missing: {sheet['sheet_name']}", "context": sheet})
        status = "blocked_missing_required_sheet"
        ready = False
    elif required_columns_missing:
        for item in required_columns_missing:
            errors.append({"code": "REQUIRED_COLUMN_MISSING", "message": f"Required column is missing: {item['sheet_name']}.{item['column_name']}", "context": item})
        status = "blocked_missing_required_columns"
        ready = False
    else:
        status = "trimmed"
        ready = True

    manifest = {
        "module_id": MODULE_ID,
        "contract_version": CONTRACT_VERSION,
        "policy_version": policy["policy_version"],
        "source_manifest": RAW_SHEETS_MANIFEST_RELATIVE_PATH.as_posix(),
        "status": status,
        "trimmed_artifact_root": TRIMMED_RELATIVE_DIR.as_posix(),
        "sheets": kept_sheets,
        "missing_sheets": missing_sheets,
        "dropped_sheets": dropped_sheets,
        "warnings": warnings,
        "private_data_notice": "Trimmed sheet artifacts may contain private Garmin health and activity data and must not be committed to version control.",
        "ready_for_next_module": ready,
    }
    summary = {
        "module_id": MODULE_ID,
        "contract_version": CONTRACT_VERSION,
        "policy_version": policy["policy_version"],
        "status": status,
        "source_sheets_count": len(raw_manifest.get("sheets", [])),
        "kept_required_sheets_count": len([sheet for sheet in kept_sheets if sheet["classification"] == "KEEP_REQUIRED"]),
        "kept_optional_sheets_count": len([sheet for sheet in kept_sheets if sheet["classification"] == "KEEP_OPTIONAL"]),
        "missing_required_sheets_count": len([sheet for sheet in missing_sheets if sheet["classification"] == "MISSING_REQUIRED"]),
        "missing_optional_sheets_count": len([sheet for sheet in missing_sheets if sheet["classification"] == "MISSING_OPTIONAL"]),
        "dropped_sheets_count": len(dropped_sheets),
        "total_source_columns_count": total_source_columns,
        "total_kept_columns_count": total_kept_columns,
        "total_dropped_columns_count": total_dropped_columns,
        "required_columns_missing": required_columns_missing,
        "optional_columns_missing": optional_columns_missing,
        "ready_for_next_module": ready,
        "warnings": warnings,
    }
    report = build_report(manifest, summary, policy)
    return {"manifest": manifest, "summary": summary, "report": report, "errors": errors, "generated_csv": generated_csv}


def build_report(manifest: dict[str, Any], summary: dict[str, Any], policy: dict[str, Any]) -> str:
    lines = [
        "# Trim Workbook Report",
        "",
        f"Module: `{MODULE_ID}`",
        f"Policy: `{policy['policy_version']}`",
        f"Source manifest: `{RAW_SHEETS_MANIFEST_RELATIVE_PATH.as_posix()}`",
        f"Status: `{manifest['status']}`",
        f"Ready for next module: `{manifest['ready_for_next_module']}`",
        "",
        "## Summary",
        "",
        f"- Source sheets: {summary['source_sheets_count']}",
        f"- Kept required sheets: {summary['kept_required_sheets_count']}",
        f"- Kept optional sheets: {summary['kept_optional_sheets_count']}",
        f"- Dropped sheets: {summary['dropped_sheets_count']}",
        f"- Missing required sheets: {summary['missing_required_sheets_count']}",
        f"- Missing optional sheets: {summary['missing_optional_sheets_count']}",
        f"- Kept columns: {summary['total_kept_columns_count']}",
        f"- Dropped columns: {summary['total_dropped_columns_count']}",
        "",
        "## KEEP - Sheets retained",
        "",
    ]
    if not manifest["sheets"]:
        lines.append("None")
    for sheet in manifest["sheets"]:
        lines.extend([
            f"### {sheet['sheet_name']} ({sheet['classification']})",
            f"- CSV: `{sheet['artifact_path']}`",
            f"- Rows: {sheet['row_count']}",
            f"- Kept columns: {', '.join(sheet['kept_columns']) if sheet['kept_columns'] else 'none'}",
            "",
            f"- KEEP_REQUIRED: {', '.join(sheet['kept_required_columns']) if sheet['kept_required_columns'] else 'none'}",
            f"- KEEP_OPTIONAL: {', '.join(sheet['kept_optional_columns']) if sheet['kept_optional_columns'] else 'none'}",
            f"- MISSING_REQUIRED: {', '.join(sheet['missing_required_columns']) if sheet['missing_required_columns'] else 'none'}",
            f"- MISSING_OPTIONAL: {', '.join(sheet['missing_optional_columns']) if sheet['missing_optional_columns'] else 'none'}",
            f"- DROP_NOT_USED: {', '.join(sheet['dropped_columns']) if sheet['dropped_columns'] else 'none'}",
            "",
        ])
    lines.extend(["## DROP - Sheets not used", ""])
    if not manifest["dropped_sheets"]:
        lines.append("None")
    for sheet in manifest["dropped_sheets"]:
        lines.append(f"- {sheet['sheet_name']} ({sheet['classification']})")
    lines.extend(["", "## MISSING - Expected sheets not found", ""])
    if not manifest["missing_sheets"]:
        lines.append("None")
    for sheet in manifest["missing_sheets"]:
        lines.append(f"- {sheet['sheet_name']} ({sheet['classification']})")
    lines.extend(["", "## Warnings", ""])
    if not manifest["warnings"]:
        lines.append("None")
    for warning in manifest["warnings"]:
        lines.append(f"- {warning}")
    lines.extend([
        "",
        "## Scope",
        "",
        "This module performed explicit data selection only.",
        "It did not normalize data, join dates, convert units, calculate metrics, assess health or readiness, call Garmin API or use LLM.",
        "",
    ])
    return "\n".join(lines)


def blocked_outputs(status: str, message: str) -> tuple[dict[str, Any], dict[str, Any], str]:
    manifest = {
        "module_id": MODULE_ID,
        "contract_version": CONTRACT_VERSION,
        "policy_version": None,
        "source_manifest": RAW_SHEETS_MANIFEST_RELATIVE_PATH.as_posix(),
        "status": status,
        "trimmed_artifact_root": TRIMMED_RELATIVE_DIR.as_posix(),
        "sheets": [],
        "missing_sheets": [],
        "dropped_sheets": [],
        "warnings": [message],
        "private_data_notice": "Trimmed sheet artifacts may contain private Garmin health and activity data and must not be committed to version control.",
        "ready_for_next_module": False,
    }
    summary = {
        "module_id": MODULE_ID,
        "contract_version": CONTRACT_VERSION,
        "policy_version": None,
        "status": status,
        "source_sheets_count": 0,
        "kept_required_sheets_count": 0,
        "kept_optional_sheets_count": 0,
        "missing_required_sheets_count": 0,
        "missing_optional_sheets_count": 0,
        "dropped_sheets_count": 0,
        "total_source_columns_count": 0,
        "total_kept_columns_count": 0,
        "total_dropped_columns_count": 0,
        "required_columns_missing": [],
        "optional_columns_missing": [],
        "ready_for_next_module": False,
        "warnings": [message],
    }
    return manifest, summary, f"# Trim Workbook Report\n\nStatus: `{status}`\n\n- {message}\n"


def write_run_log(path: Path, started_at: str, finished_at: str, execution_status: str, domain_status: str, manifest: dict[str, Any], errors: list[dict[str, Any]]) -> None:
    lines = [
        f"module_id={MODULE_ID}",
        f"started_at={started_at}",
        f"policy_version={manifest.get('policy_version')}",
        f"source_manifest={RAW_SHEETS_MANIFEST_RELATIVE_PATH.as_posix()}",
        f"source_sheets_count={len(manifest.get('sheets', [])) + len(manifest.get('dropped_sheets', []))}",
        "keep_sheets=" + ", ".join(sheet["sheet_name"] for sheet in manifest.get("sheets", [])),
        "drop_sheets=" + ", ".join(sheet["sheet_name"] for sheet in manifest.get("dropped_sheets", [])),
        "missing_sheets=" + ", ".join(sheet["sheet_name"] for sheet in manifest.get("missing_sheets", [])),
    ]
    for sheet in manifest.get("sheets", []):
        lines.append(f"sheet={sheet['sheet_name']} kept_columns={len(sheet['kept_columns'])} dropped_columns={sheet['dropped_columns_count']} csv={sheet['artifact_path']}")
        if sheet["missing_required_columns"]:
            lines.append(f"missing_required_columns={sheet['sheet_name']}: {', '.join(sheet['missing_required_columns'])}")
        if sheet["missing_optional_columns"]:
            lines.append(f"missing_optional_columns={sheet['sheet_name']}: {', '.join(sheet['missing_optional_columns'])}")
    for warning in manifest.get("warnings", []):
        lines.append(f"warning={warning}")
    for error in errors:
        lines.append(f"error={error['code']}: {error['message']}")
    lines.extend([
        "normalization_performed=false",
        "domain_calculations_performed=false",
        "garmin_api_used=false",
        "llm_used=false",
        f"finished_at={finished_at}",
        f"execution_status={execution_status}",
        f"domain_status={domain_status}",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def execute(root: Path = ROOT) -> int:
    started_at = now_iso()
    artifact_dir = root / ARTIFACT_RELATIVE_DIR
    trimmed_dir = root / TRIMMED_RELATIVE_DIR
    artifact_dir.mkdir(parents=True, exist_ok=True)
    trimmed_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = artifact_dir / "trimmed_sheets_manifest.json"
    summary_path = artifact_dir / "trim_summary.json"
    report_path = artifact_dir / "trim_report.md"
    run_manifest_path = artifact_dir / "run_manifest.json"
    run_log_path = artifact_dir / "run_log.txt"
    errors_path = artifact_dir / "errors.json"
    generated_artifacts = [
        (ARTIFACT_RELATIVE_DIR / "trimmed_sheets_manifest.json").as_posix(),
        (ARTIFACT_RELATIVE_DIR / "trim_summary.json").as_posix(),
        (ARTIFACT_RELATIVE_DIR / "trim_report.md").as_posix(),
        (ARTIFACT_RELATIVE_DIR / "run_manifest.json").as_posix(),
        (ARTIFACT_RELATIVE_DIR / "run_log.txt").as_posix(),
        (ARTIFACT_RELATIVE_DIR / "errors.json").as_posix(),
    ]
    errors: list[dict[str, Any]] = []
    try:
        result = process(root, artifact_dir)
        manifest = result["manifest"]
        summary = result["summary"]
        report = result["report"]
        errors = result["errors"]
        generated_artifacts.extend(result["generated_csv"])
        execution_status = "success" if not errors else "failed"
        domain_status = manifest["status"]
    except ModuleError as exc:
        errors = [{"code": exc.code, "message": exc.message, "context": exc.context}]
        manifest, summary, report = blocked_outputs(exc.domain_status, exc.message)
        execution_status = "failed"
        domain_status = exc.domain_status
    except Exception as exc:
        errors = [{"code": "TRIM_FAILED", "message": str(exc), "context": {}}]
        manifest, summary, report = blocked_outputs("trim_failed", str(exc))
        execution_status = "failed"
        domain_status = "trim_failed"
    write_json(manifest_path, manifest)
    write_json(summary_path, summary)
    report_path.write_text(report, encoding="utf-8")
    finished_at = now_iso()
    write_json(errors_path, {"module_id": MODULE_ID, "errors": errors})
    write_run_log(run_log_path, started_at, finished_at, execution_status, domain_status, manifest, errors)
    write_json(run_manifest_path, {
        "module_id": MODULE_ID,
        "module_version": CONTRACT_VERSION,
        "policy_version": manifest.get("policy_version"),
        "started_at": started_at,
        "finished_at": finished_at,
        "execution_status": execution_status,
        "domain_status": domain_status,
        "inputs": [WORKBOOK_STRUCTURE_RELATIVE_PATH.as_posix(), RAW_SHEETS_MANIFEST_RELATIVE_PATH.as_posix(), TRIM_POLICY_RELATIVE_PATH.as_posix()],
        "generated_artifacts": generated_artifacts,
        "log_file": (ARTIFACT_RELATIVE_DIR / "run_log.txt").as_posix(),
        "errors_file": (ARTIFACT_RELATIVE_DIR / "errors.json").as_posix(),
    })
    return 0 if execution_status == "success" else 1


def main() -> int:
    return execute(ROOT)


if __name__ == "__main__":
    sys.exit(main())