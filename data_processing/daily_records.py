from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MODULE_ID = "05_normalize_daily_records"
VERSION = "1.0.0"
POLICY_VERSION = "garmin_daily_normalization_v1"
ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "garmin_daily_normalization_v1.json"
TRIM_MANIFEST_PATH = ROOT / "data" / "pipeline" / "03_trim_workbook" / "trimmed_sheets_manifest.json"
ARTIFACT_DIR = ROOT / "data" / "pipeline" / MODULE_ID
LOG_FILE = ARTIFACT_DIR / "run_log.txt"
ERRORS_FILE = ARTIFACT_DIR / "errors.json"
RUN_MANIFEST_FILE = ARTIFACT_DIR / "run_manifest.json"
DAILY_JSON_FILE = ARTIFACT_DIR / "daily_records.json"
DAILY_CSV_FILE = ARTIFACT_DIR / "daily_records.csv"
SCHEMA_FILE = ARTIFACT_DIR / "daily_records_schema.json"
QUALITY_FILE = ARTIFACT_DIR / "data_quality_report.json"


def reset_paths(root: Path) -> None:
    global ROOT, POLICY_PATH, TRIM_MANIFEST_PATH, ARTIFACT_DIR, LOG_FILE, ERRORS_FILE, RUN_MANIFEST_FILE, DAILY_JSON_FILE, DAILY_CSV_FILE, SCHEMA_FILE, QUALITY_FILE
    ROOT = root
    POLICY_PATH = ROOT / "config" / "garmin_daily_normalization_v1.json"
    TRIM_MANIFEST_PATH = ROOT / "data" / "pipeline" / "03_trim_workbook" / "trimmed_sheets_manifest.json"
    ARTIFACT_DIR = ROOT / "data" / "pipeline" / MODULE_ID
    LOG_FILE = ARTIFACT_DIR / "run_log.txt"
    ERRORS_FILE = ARTIFACT_DIR / "errors.json"
    RUN_MANIFEST_FILE = ARTIFACT_DIR / "run_manifest.json"
    DAILY_JSON_FILE = ARTIFACT_DIR / "daily_records.json"
    DAILY_CSV_FILE = ARTIFACT_DIR / "daily_records.csv"
    SCHEMA_FILE = ARTIFACT_DIR / "daily_records_schema.json"
    QUALITY_FILE = ARTIFACT_DIR / "data_quality_report.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def add_error(errors: list[dict[str, Any]], code: str, message: str, context: dict[str, Any] | None = None) -> None:
    errors.append({"code": code, "message": message, "context": context or {}})


def parse_date(value: Any) -> str | None:
    text = "" if value is None else str(value).strip()
    if not text:
        return None
    text = text.split("T", 1)[0].strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d.%m.%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            pass
    return None


def parse_number(value: Any) -> tuple[int | float | None, bool]:
    text = "" if value is None else str(value).strip()
    if text == "":
        return None, True
    normalized = text.replace(" ", "").replace(",", ".")
    try:
        number = float(normalized)
    except ValueError:
        return None, False
    if number.is_integer():
        return int(number), True
    return number, True


def parse_value(value: Any, value_type: str, context: dict[str, Any], quality: dict[str, Any], required: bool, errors: list[dict[str, Any]]) -> Any:
    text = "" if value is None else str(value).strip()
    if text == "":
        return None
    if value_type == "string":
        return text or None
    if value_type in {"number", "body_weight"}:
        number, ok = parse_number(text)
        if not ok:
            quality["invalid_numeric_values"].append({**context, "value": text})
            if required:
                add_error(errors, "REQUIRED_NUMERIC_VALUE_INVALID", "Required numeric value is invalid.", context)
            return None
        if value_type == "body_weight" and number is not None:
            if float(number) > 400:
                quality["unit_conversions_applied"]["weight_grams_to_kilograms_count"] += 1
                return round(float(number) / 1000.0, 3)
            return number
        return number
    return text or None


def read_csv_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def load_inputs(errors: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, dict[str, Any] | None, str | None]:
    if not POLICY_PATH.is_file():
        add_error(errors, "NORMALIZATION_POLICY_NOT_FOUND", "Normalization policy was not found.", {"path": rel(POLICY_PATH)})
        return None, None, "invalid_normalization_policy"
    if not TRIM_MANIFEST_PATH.is_file():
        add_error(errors, "TRIMMED_SHEETS_MANIFEST_NOT_FOUND", "Trimmed sheets manifest from module 03 was not found.", {"path": rel(TRIM_MANIFEST_PATH)})
        return None, None, "blocked_missing_trim_manifest"
    try:
        policy = read_json(POLICY_PATH)
        manifest = read_json(TRIM_MANIFEST_PATH)
    except Exception as exc:
        add_error(errors, "NORMALIZATION_POLICY_INVALID", f"Input JSON could not be read: {exc}")
        return None, None, "invalid_normalization_policy"
    if policy.get("policy_version") != POLICY_VERSION or policy.get("missing_values_policy") != "preserve_as_null":
        add_error(errors, "NORMALIZATION_POLICY_INVALID", "Normalization policy has invalid required settings.")
        return None, manifest, "invalid_normalization_policy"
    if manifest.get("ready_for_next_module") is not True:
        add_error(errors, "TRIMMED_SHEETS_NOT_READY", "Module 03 manifest is not ready for next module.")
        return policy, manifest, "blocked_trim_not_ready"
    return policy, manifest, None


def sheet_paths_from_manifest(manifest: dict[str, Any]) -> tuple[dict[str, Path], list[dict[str, str]]]:
    paths: dict[str, Path] = {}
    ignored: list[dict[str, str]] = []
    for sheet in manifest.get("sheets", []):
        name = str(sheet.get("sheet_name", ""))
        artifact = sheet.get("artifact_path")
        if name == "Activities":
            ignored.append({"sheet_name": name, "reason": "Handled exclusively by module 06_normalize_activities."})
            continue
        if artifact:
            paths[name] = ROOT / str(artifact)
    for sheet in manifest.get("missing_sheets", []):
        if sheet.get("sheet_name") == "Activities":
            ignored.append({"sheet_name": "Activities", "reason": "Handled exclusively by module 06_normalize_activities."})
    return paths, ignored


def choose_date_field(headers: list[str], sheet_policy: dict[str, Any]) -> str | None:
    candidates = [sheet_policy.get("date_field"), *sheet_policy.get("alternate_date_fields", [])]
    return next((field for field in candidates if field in headers), None)


def collect_sheet_rows(sheet_name: str, path: Path, sheet_policy: dict[str, Any], primary_dates: set[str], quality: dict[str, Any], errors: list[dict[str, Any]]) -> tuple[dict[str, dict[str, str]], list[str], bool]:
    try:
        rows, headers = read_csv_rows(path)
    except Exception as exc:
        add_error(errors, "INPUT_CSV_READ_ERROR", f"Could not read input CSV for {sheet_name}: {exc}", {"sheet_name": sheet_name})
        return {}, [], False
    date_field = choose_date_field(headers, sheet_policy)
    if not date_field:
        return {}, headers, True
    by_date: dict[str, dict[str, str]] = {}
    duplicates: list[str] = []
    invalid_optional = 0
    for index, row in enumerate(rows, start=2):
        parsed = parse_date(row.get(date_field))
        if not parsed:
            if sheet_name == "Daily_Summary":
                add_error(errors, "PRIMARY_DATE_INVALID", "Daily_Summary contains an invalid or empty date.", {"row_number": index})
            else:
                invalid_optional += 1
            continue
        if parsed in by_date:
            duplicates.append(parsed)
        else:
            by_date[parsed] = row
    if duplicates:
        add_error(errors, "DUPLICATE_DATE_FOUND", "A consumed daily sheet contains duplicate dates.", {"sheet_name": sheet_name, "dates": sorted(set(duplicates))})
        return by_date, headers, False
    if sheet_name != "Daily_Summary":
        quality["date_quality"]["invalid_optional_dates_count"] += invalid_optional
        for date_value in sorted(set(by_date) - primary_dates):
            quality["orphan_optional_rows"].append({"sheet_name": sheet_name, "date": date_value})
        by_date = {date: row for date, row in by_date.items() if date in primary_dates}
    return by_date, headers, True


def normalize(policy: dict[str, Any], manifest: dict[str, Any], errors: list[dict[str, Any]]) -> tuple[str, dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None, list[str]]:
    warnings = ["Missing values were preserved as null and were not replaced with zero."]
    fields: list[str] = policy["output_fields"]
    sheet_paths, ignored_sheets = sheet_paths_from_manifest(manifest)
    if "Daily_Summary" not in sheet_paths or not sheet_paths["Daily_Summary"].is_file():
        add_error(errors, "PRIMARY_SHEET_NOT_FOUND", "Daily_Summary trimmed CSV was not found.")
        return "blocked_missing_primary_sheet", None, None, None, warnings

    quality = {
        "module_id": MODULE_ID,
        "policy_version": POLICY_VERSION,
        "status": "normalized",
        "records_count": 0,
        "date_quality": {"invalid_primary_dates_count": 0, "duplicate_primary_dates_count": 0, "invalid_optional_dates_count": 0, "orphan_optional_rows_count": 0},
        "consumed_sheets": [],
        "ignored_sheets": ignored_sheets,
        "field_coverage": {},
        "field_conflicts": [],
        "invalid_numeric_values": [],
        "orphan_optional_rows": [],
        "unit_conversions_applied": {"weight_grams_to_kilograms_count": 0},
        "warnings": warnings,
        "ready_for_next_module": False,
    }

    sheets_policy = policy["sheets"]
    primary_policy = sheets_policy["Daily_Summary"]
    primary_rows, primary_headers = read_csv_rows(sheet_paths["Daily_Summary"])
    required_sources = {m["source_column"] for m in primary_policy["mappings"] if m.get("required")}
    if policy["primary_source_date_field"] not in primary_headers:
        add_error(errors, "PRIMARY_DATE_FIELD_NOT_MAPPED", "Daily_Summary date field is missing from trimmed CSV.")
        return "blocked_missing_required_field_mapping", None, None, quality, warnings
    if "activeKilocalories" not in required_sources or "activeKilocalories" not in primary_headers:
        add_error(errors, "ACTIVE_KCAL_FIELD_NOT_MAPPED", "Daily_Summary active_kcal source field is missing from policy or CSV.")
        return "blocked_missing_required_field_mapping", None, None, quality, warnings

    primary_dates: list[str] = []
    primary_by_date: dict[str, dict[str, str]] = {}
    duplicate_dates: list[str] = []
    for index, row in enumerate(primary_rows, start=2):
        date_value = parse_date(row.get(policy["primary_source_date_field"]))
        if not date_value:
            quality["date_quality"]["invalid_primary_dates_count"] += 1
            add_error(errors, "PRIMARY_DATE_INVALID", "Daily_Summary contains an invalid or empty date.", {"row_number": index})
            continue
        if date_value in primary_by_date:
            duplicate_dates.append(date_value)
        else:
            primary_by_date[date_value] = row
            primary_dates.append(date_value)
    if duplicate_dates:
        quality["date_quality"]["duplicate_primary_dates_count"] = len(set(duplicate_dates))
        add_error(errors, "DUPLICATE_DATE_FOUND", "Daily_Summary contains duplicate dates.", {"dates": sorted(set(duplicate_dates))})
        return "blocked_duplicate_dates", None, None, quality, warnings
    if errors:
        return "blocked_invalid_primary_dates", None, None, quality, warnings
    if not primary_dates:
        add_error(errors, "NO_DAILY_RECORDS_CREATED", "No valid Daily_Summary dates were available.")
        return "blocked_no_daily_records", None, None, quality, warnings

    primary_date_set = set(primary_dates)
    sheet_data: dict[str, dict[str, dict[str, str]]] = {"Daily_Summary": primary_by_date}
    sheet_headers: dict[str, list[str]] = {"Daily_Summary": primary_headers}
    quality["consumed_sheets"].append({"sheet_name": "Daily_Summary", "status": "consumed_required", "rows_count": len(primary_rows)})

    for sheet_name, sheet_policy in sheets_policy.items():
        if sheet_name in {"Daily_Summary", "Activities"}:
            continue
        path = sheet_paths.get(sheet_name)
        if not path or not path.is_file():
            warnings.append(f"Optional sheet not available for normalization: {sheet_name}")
            continue
        by_date, headers, ok = collect_sheet_rows(sheet_name, path, sheet_policy, primary_date_set, quality, errors)
        if not ok:
            return "blocked_duplicate_dates" if any(e["code"] == "DUPLICATE_DATE_FOUND" for e in errors) else "normalization_failed", None, None, quality, warnings
        sheet_data[sheet_name] = by_date
        sheet_headers[sheet_name] = headers
        quality["consumed_sheets"].append({"sheet_name": sheet_name, "status": "consumed_optional", "rows_count": len(by_date)})

    quality["orphan_optional_rows_count"] = len(quality["orphan_optional_rows"])
    quality["date_quality"]["orphan_optional_rows_count"] = len(quality["orphan_optional_rows"])

    contributions: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for sheet_name, rows_by_date in sheet_data.items():
        for mapping in sheets_policy[sheet_name].get("mappings", []):
            source = mapping["source_column"]
            target = mapping["target_field"]
            if target not in fields or source not in sheet_headers[sheet_name]:
                continue
            for date_value, row in rows_by_date.items():
                value = parse_value(row.get(source), mapping["type"], {"sheet_name": sheet_name, "date": date_value, "source_column": source, "target_field": target}, quality, bool(mapping.get("required")), errors)
                contributions[date_value][target].append({"sheet_name": sheet_name, "source_column": source, "value": value})
    if any(e["code"] == "REQUIRED_NUMERIC_VALUE_INVALID" for e in errors):
        return "blocked_invalid_required_numeric_value", None, None, quality, warnings

    records: list[dict[str, Any]] = []
    priority = policy.get("field_source_priority", {})
    for date_value in sorted(primary_dates):
        record = {field: None for field in fields}
        record["date"] = date_value
        for field in fields:
            if field == "date":
                continue
            candidates = [c for c in contributions[date_value].get(field, []) if c["value"] is not None]
            if not candidates:
                continue
            ordered_sources = priority.get(field, [])
            if ordered_sources:
                candidates.sort(key=lambda item: ordered_sources.index(item["sheet_name"]) if item["sheet_name"] in ordered_sources else len(ordered_sources))
            chosen = candidates[0]
            record[field] = chosen["value"]
            distinct = {(c["sheet_name"], str(c["value"])) for c in candidates}
            if len({str(c["value"]) for c in candidates}) > 1:
                quality["field_conflicts"].append({"date": date_value, "field": field, "chosen_source": chosen["sheet_name"], "sources": [{"sheet_name": c["sheet_name"], "value": c["value"]} for c in candidates]})
        records.append(record)

    if not records:
        add_error(errors, "NO_DAILY_RECORDS_CREATED", "No daily records were created.")
        return "blocked_no_daily_records", None, None, quality, warnings

    for field in fields:
        if field == "date":
            continue
        available = sum(1 for record in records if record.get(field) is not None)
        missing = len(records) - available
        quality["field_coverage"][field] = {"available_count": available, "missing_count": missing, "coverage_ratio": round(available / len(records), 6)}
    quality["records_count"] = len(records)
    quality["ready_for_next_module"] = True
    if quality["field_conflicts"]:
        warnings.append("Conflicting source values were resolved using configured field_source_priority.")
    if quality["orphan_optional_rows"]:
        warnings.append("Orphan optional rows were excluded and reported.")

    daily_payload = {
        "module_id": MODULE_ID,
        "contract_version": VERSION,
        "policy_version": POLICY_VERSION,
        "status": "normalized",
        "source_manifest": rel(TRIM_MANIFEST_PATH),
        "primary_sheet": "Daily_Summary",
        "date_range": {"first_date": records[0]["date"], "last_date": records[-1]["date"]},
        "records_count": len(records),
        "fields": fields,
        "records": records,
        "missing_values_policy": "preserve_as_null",
        "ready_for_next_module": True,
        "private_data_notice": "Normalized daily records contain private health and activity data and must not be committed to version control.",
    }
    schema = {
        "module_id": MODULE_ID,
        "schema_version": "daily_records_schema_v1",
        "policy_version": POLICY_VERSION,
        "primary_key": "date",
        "primary_key_format": "YYYY-MM-DD",
        "record_source_policy": "one_record_per_valid_date_from_Daily_Summary",
        "missing_values_policy": "preserve_as_null",
        "fields": policy["field_definitions"],
        "excluded_derived_fields": ["rhr_delta", "ln_rmssd", "acute_load", "chronic_load", "acwr", "readiness", "pws_score", "pws_components", "pws_weights", "pws_priority"],
    }
    return "normalized", daily_payload, schema, quality, warnings


def write_csv_records(records: list[dict[str, Any]], fields: list[str]) -> None:
    with DAILY_CSV_FILE.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            writer.writerow({field: "" if record.get(field) is None else record.get(field) for field in fields})


def write_run_outputs(started_at: str, domain_status: str, errors: list[dict[str, Any]], generated: list[str], log_lines: list[str]) -> int:
    finished_at = now_iso()
    execution_status = "success" if domain_status == "normalized" else "failed"
    write_json(ERRORS_FILE, {"module_id": MODULE_ID, "errors": errors})
    if rel(ERRORS_FILE) not in generated:
        generated.append(rel(ERRORS_FILE))
    log_lines.extend([
        f"finished_at={finished_at}",
        f"execution_status={execution_status}",
        f"domain_status={domain_status}",
        "activities_sheet_excluded=true",
        "garmin_api_artifacts_used=false",
        "missing_values_preserved_as_null=true",
        "derived_metrics_calculated=false",
        "llm_used=false",
    ])
    LOG_FILE.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    generated.append(rel(LOG_FILE))
    generated.append(rel(RUN_MANIFEST_FILE))
    run_manifest = {
        "module_id": MODULE_ID,
        "module_version": VERSION,
        "policy_version": POLICY_VERSION,
        "started_at": started_at,
        "finished_at": finished_at,
        "execution_status": execution_status,
        "domain_status": domain_status,
        "inputs": [rel(TRIM_MANIFEST_PATH), rel(POLICY_PATH)],
        "generated_artifacts": generated,
        "log_file": rel(LOG_FILE),
        "errors_file": rel(ERRORS_FILE),
    }
    write_json(RUN_MANIFEST_FILE, run_manifest)
    return 0 if execution_status == "success" else 1


def execute(root: Path | None = None) -> int:
    if root is not None:
        reset_paths(root)
    started_at = now_iso()
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    generated: list[str] = []
    errors: list[dict[str, Any]] = []
    log_lines = [f"module_id={MODULE_ID}", f"started_at={started_at}", f"input_manifest={rel(TRIM_MANIFEST_PATH)}"]
    try:
        policy, manifest, blocked_status = load_inputs(errors)
        if blocked_status:
            return write_run_outputs(started_at, blocked_status, errors, generated, log_lines)
        assert policy is not None and manifest is not None
        log_lines.append(f"policy_version={policy['policy_version']}")
        log_lines.append(f"primary_sheet={policy['primary_sheet']}")
        status, daily_payload, schema, quality, warnings = normalize(policy, manifest, errors)
        if status == "normalized" and daily_payload and schema and quality:
            write_json(DAILY_JSON_FILE, daily_payload)
            generated.append(rel(DAILY_JSON_FILE))
            write_csv_records(daily_payload["records"], daily_payload["fields"])
            generated.append(rel(DAILY_CSV_FILE))
            write_json(SCHEMA_FILE, schema)
            generated.append(rel(SCHEMA_FILE))
            write_json(QUALITY_FILE, quality)
            generated.append(rel(QUALITY_FILE))
            log_lines.extend([
                f"primary_rows={daily_payload['records_count']}",
                f"date_range={daily_payload['date_range']['first_date']}..{daily_payload['date_range']['last_date']}",
                f"consumed_sheets={[item['sheet_name'] for item in quality['consumed_sheets']]}",
                f"ignored_sheets={[item['sheet_name'] for item in quality['ignored_sheets']]}",
                f"field_conflicts_count={len(quality['field_conflicts'])}",
                f"orphan_optional_rows_count={len(quality['orphan_optional_rows'])}",
                f"weight_grams_to_kilograms_count={quality['unit_conversions_applied']['weight_grams_to_kilograms_count']}",
            ])
        elif quality:
            quality["status"] = status
            quality["ready_for_next_module"] = False
            write_json(QUALITY_FILE, quality)
            generated.append(rel(QUALITY_FILE))
        for warning in (warnings if 'warnings' in locals() else []):
            log_lines.append(f"warning={warning}")
        return write_run_outputs(started_at, status, errors, generated, log_lines)
    except Exception as exc:  # noqa: BLE001
        add_error(errors, "ARTIFACT_WRITE_ERROR", f"Normalization failed unexpectedly: {exc}")
        return write_run_outputs(started_at, "normalization_failed", errors, generated, log_lines)


def main() -> int:
    return execute()


if __name__ == "__main__":
    sys.exit(main())

