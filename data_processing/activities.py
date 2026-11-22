from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MODULE_ID = "06_normalize_activities"
VERSION = "1.0.0"
POLICY_VERSION = "garmin_activity_normalization_v1"
ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "garmin_activity_normalization_v1.json"
TRIM_MANIFEST_PATH = ROOT / "data" / "pipeline" / "03_trim_workbook" / "trimmed_sheets_manifest.json"
API_MANIFEST_PATH = ROOT / "data" / "pipeline" / "04_garmin_activity_ingest" / "activity_ingest_manifest.json"
ARTIFACT_DIR = ROOT / "data" / "pipeline" / MODULE_ID
OUT_JSON = ARTIFACT_DIR / "activities_normalized.json"
OUT_CSV = ARTIFACT_DIR / "activities_normalized.csv"
OUT_BY_DATE = ARTIFACT_DIR / "activities_by_date.json"
OUT_SCHEMA = ARTIFACT_DIR / "activity_schema.json"
OUT_QUALITY = ARTIFACT_DIR / "activity_data_quality_report.json"
RUN_MANIFEST = ARTIFACT_DIR / "run_manifest.json"
LOG_FILE = ARTIFACT_DIR / "run_log.txt"
ERRORS_FILE = ARTIFACT_DIR / "errors.json"
SUCCESS = {"normalized_from_workbook_only","normalized_with_api_enrichment","normalized_from_api_only","normalized_empty_no_activity_sources","normalized_with_warnings"}
NESTED_FIELDS = {"source_presence","splits","api_artifacts","field_sources","warnings"}


def reset_paths(root: Path) -> None:
    global ROOT, POLICY_PATH, TRIM_MANIFEST_PATH, API_MANIFEST_PATH, ARTIFACT_DIR, OUT_JSON, OUT_CSV, OUT_BY_DATE, OUT_SCHEMA, OUT_QUALITY, RUN_MANIFEST, LOG_FILE, ERRORS_FILE
    ROOT = root
    POLICY_PATH = ROOT / "config" / "garmin_activity_normalization_v1.json"
    TRIM_MANIFEST_PATH = ROOT / "data" / "pipeline" / "03_trim_workbook" / "trimmed_sheets_manifest.json"
    API_MANIFEST_PATH = ROOT / "data" / "pipeline" / "04_garmin_activity_ingest" / "activity_ingest_manifest.json"
    ARTIFACT_DIR = ROOT / "data" / "pipeline" / MODULE_ID
    OUT_JSON = ARTIFACT_DIR / "activities_normalized.json"
    OUT_CSV = ARTIFACT_DIR / "activities_normalized.csv"
    OUT_BY_DATE = ARTIFACT_DIR / "activities_by_date.json"
    OUT_SCHEMA = ARTIFACT_DIR / "activity_schema.json"
    OUT_QUALITY = ARTIFACT_DIR / "activity_data_quality_report.json"
    RUN_MANIFEST = ARTIFACT_DIR / "run_manifest.json"
    LOG_FILE = ARTIFACT_DIR / "run_log.txt"
    ERRORS_FILE = ARTIFACT_DIR / "errors.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def add_error(errors: list[dict[str, Any]], code: str, message: str, context: dict[str, Any] | None = None, blocking: bool = False) -> None:
    item = {"code": code, "message": message, "context": context or {}}
    if not blocking:
        item["blocking"] = False
    errors.append(item)


def parse_number(value: Any) -> tuple[int | float | None, bool]:
    text = "" if value is None else str(value).strip()
    if text == "":
        return None, True
    try:
        n = float(text.replace(" ", "").replace(",", "."))
    except ValueError:
        return None, False
    return (int(n) if n.is_integer() else n), True


def parse_string(value: Any) -> str | None:
    text = "" if value is None else str(value).strip()
    return text or None


def parse_start(value: Any) -> tuple[str | None, str | None]:
    text = parse_string(value)
    if not text:
        return None, None
    date_part = text.split("T", 1)[0].split(" ", 1)[0]
    try:
        date_value = datetime.strptime(date_part, "%Y-%m-%d").date().isoformat()
    except ValueError:
        return text, None
    normalized = text.replace(" ", "T") if "T" not in text and " " in text else text
    return normalized, date_value


def convert_value(raw: Any, mapping: dict[str, Any], quality: dict[str, Any], source: str, field: str, activity_id: str | None, errors: list[dict[str, Any]]) -> Any:
    typ = mapping.get("type")
    if typ in {"string", "datetime"}:
        return parse_string(raw)
    n, ok = parse_number(raw)
    if not ok:
        quality["invalid_optional_numeric_values"].append({"source": source, "field": field, "activity_id": activity_id, "value": str(raw)})
        add_error(errors, "INVALID_OPTIONAL_NUMERIC_VALUE", "Invalid optional numeric value was set to null.", {"source": source, "field": field, "activity_id": activity_id})
        return None
    if n is None:
        return None
    conv = mapping.get("conversion")
    if conv == "meters_to_km":
        quality["unit_conversions_applied"]["distance_m_to_km_count"] += 1
        return round(float(n) / 1000.0, 6)
    if conv == "mps_to_kmh":
        quality["unit_conversions_applied"]["speed_mps_to_kmh_count"] += 1
        return round(float(n) * 3.6, 6)
    if conv == "garmin_rpe_0_100_to_0_10":
        if float(n) < 0 or float(n) > 100:
            quality["invalid_optional_numeric_values"].append({"source": source, "field": field, "activity_id": activity_id, "value": str(raw)})
            add_error(errors, "INVALID_OPTIONAL_NUMERIC_VALUE", "Garmin RPE outside 0-100 was set to null.", {"source": source, "field": field, "activity_id": activity_id})
            return None
        return round(float(n) / 10.0, 6)
    if conv == "garmin_feeling_0_100":
        if float(n) < 0 or float(n) > 100:
            quality["invalid_optional_numeric_values"].append({"source": source, "field": field, "activity_id": activity_id, "value": str(raw)})
            add_error(errors, "INVALID_OPTIONAL_NUMERIC_VALUE", "Garmin subjective feeling outside 0-100 was set to null.", {"source": source, "field": field, "activity_id": activity_id})
            return None
        return n
    return n


def empty_record(activity_id: str) -> dict[str, Any]:
    return {
        "activity_id": activity_id,
        "date": None,
        "start_time_local": None,
        "activity_type": None,
        "activity_name": None,
        "source_presence": {"workbook": False, "api_details": False, "api_splits": False, "fit_file": False, "tcx_file": False},
        "distance_km": None,
        "duration_seconds": None,
        "calories": None,
        "average_speed_kmh": None,
        "maximum_speed_kmh": None,
        "average_hr_bpm": None,
        "maximum_hr_bpm": None,
        "average_power_w": None,
        "maximum_power_w": None,
        "elevation_gain_m": None,
        "elevation_loss_m": None,
        "hr_zone_1_seconds": None,
        "hr_zone_2_seconds": None,
        "hr_zone_3_seconds": None,
        "hr_zone_4_seconds": None,
        "hr_zone_5_seconds": None,
        "perceived_effort_rpe": None,
        "subjective_feeling_score": None,
        "splits": [],
        "api_artifacts": {"details_json_path": None, "splits_json_path": None, "fit_file_path": None, "tcx_file_path": None},
        "field_sources": {},
        "warnings": [],
    }


def read_csv_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def find_activities_csv() -> Path | None:
    if not TRIM_MANIFEST_PATH.is_file():
        return None
    try:
        manifest = read_json(TRIM_MANIFEST_PATH)
    except Exception:
        return None
    for sheet in manifest.get("sheets", []):
        if sheet.get("sheet_name") == "Activities" and sheet.get("artifact_path"):
            path = ROOT / str(sheet["artifact_path"])
            return path if path.is_file() else None
    return None


def normalize_workbook(policy: dict[str, Any], quality: dict[str, Any], errors: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    path = find_activities_csv()
    if path is None:
        return {}
    quality["source_availability"]["workbook_activities_csv_available"] = True
    try:
        rows, headers = read_csv_rows(path)
    except Exception as exc:
        add_error(errors, "WORKBOOK_ACTIVITIES_CSV_READ_ERROR", str(exc), blocking=False)
        return {}
    quality["source_record_counts"]["workbook_rows_count"] = len(rows)
    mapping = policy["workbook_mapping"]
    unknown = sorted(set(headers) - set(mapping))
    for field in unknown:
        quality["unmapped_source_fields"].append({"source": "workbook_activities_csv", "field": field})
    candidates: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for idx, row in enumerate(rows, start=2):
        aid = parse_string(row.get("activityId"))
        if not aid:
            quality["excluded_invalid_records"].append({"source": "workbook_activities_csv", "row_number": idx, "reason": "missing_activity_id"})
            add_error(errors, "ACTIVITY_ID_MISSING", "Workbook activity row has no activity_id.", {"row_number": idx})
            continue
        record = empty_record(aid)
        record["source_presence"]["workbook"] = True
        for source_col, spec in mapping.items():
            if source_col not in row:
                continue
            target = spec["target"]
            value = convert_value(row.get(source_col), spec, quality, "workbook_activities_csv", source_col, aid, errors)
            if target == "start_time_local":
                value, date_value = parse_start(value)
                record["date"] = date_value
            record[target] = value
            if value is not None:
                record["field_sources"][target] = "workbook_activities_csv"
        if not record["activity_id"]:
            record["activity_id"] = aid
        if not record["start_time_local"] or not record["date"]:
            quality["excluded_invalid_records"].append({"source": "workbook_activities_csv", "activity_id": aid, "reason": "missing_or_invalid_start_time_local"})
            add_error(errors, "START_TIME_LOCAL_INVALID", "Workbook activity has invalid start_time_local.", {"activity_id": aid})
            continue
        candidates[aid].append(record)
    result: dict[str, dict[str, Any]] = {}
    for aid, recs in candidates.items():
        if len(recs) == 1:
            result[aid] = recs[0]
            continue
        comparable = [{k: v for k, v in r.items() if k not in {"warnings"}} for r in recs]
        if all(item == comparable[0] for item in comparable):
            quality["duplicate_activity_ids"].append({"activity_id": aid, "source": "workbook_activities_csv", "resolution": "identical_duplicate_collapsed"})
            result[aid] = recs[0]
        else:
            quality["duplicate_activity_ids"].append({"activity_id": aid, "source": "workbook_activities_csv", "resolution": "conflicting_duplicate_excluded"})
            add_error(errors, "DUPLICATE_ACTIVITY_ID_CONFLICT", "Conflicting duplicate workbook activity was excluded.", {"activity_id": aid})
    return result


def api_artifacts_from_manifest(quality: dict[str, Any], errors: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    if not API_MANIFEST_PATH.is_file():
        return {}
    quality["source_availability"]["api_ingest_manifest_available"] = True
    try:
        manifest = read_json(API_MANIFEST_PATH)
    except Exception as exc:
        add_error(errors, "API_INGEST_MANIFEST_READ_ERROR", str(exc))
        return {}
    quality["source_availability"]["api_ingest_status"] = manifest.get("status")
    result: dict[str, dict[str, Any]] = {}
    for item in manifest.get("activities", []):
        aid = parse_string(item.get("activity_id"))
        mpath = item.get("manifest_path")
        if not aid or not mpath:
            continue
        dmanifest_path = ROOT / str(mpath)
        if not dmanifest_path.is_file():
            continue
        try:
            dmanifest = read_json(dmanifest_path)
        except Exception:
            continue
        quality["source_record_counts"]["api_activity_manifests_count"] += 1
        artifacts = {"details_json_path": None, "splits_json_path": None, "fit_file_path": None, "tcx_file_path": None}
        for art in dmanifest.get("downloaded_artifacts", []):
            relp = art.get("relative_path")
            typ = art.get("artifact_type")
            if typ == "details_json": artifacts["details_json_path"] = relp
            if typ == "splits_json": artifacts["splits_json_path"] = relp
            if typ == "fit_file": artifacts["fit_file_path"] = relp
            if typ == "tcx_file": artifacts["tcx_file_path"] = relp
        result[aid] = artifacts
    return result


def normalize_splits(payload: Any, policy: dict[str, Any], quality: dict[str, Any], aid: str, errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    root = policy["api_splits_mapping"].get("root", "splits")
    raw = payload.get(root, payload) if isinstance(payload, dict) else payload
    if not isinstance(raw, list):
        add_error(errors, "API_SPLITS_MAPPING_UNAVAILABLE", "API splits JSON structure is not a list.", {"activity_id": aid})
        return []
    out = []
    fields = policy["api_splits_mapping"]["fields"]
    for i, split in enumerate(raw, start=1):
        if not isinstance(split, dict):
            continue
        row = {"split_index": i, "distance_km": None, "duration_seconds": None, "average_speed_kmh": None, "average_hr_bpm": None, "maximum_hr_bpm": None, "average_power_w": None, "elevation_gain_m": None}
        for src, spec in fields.items():
            if src in split:
                row[spec["target"]] = convert_value(split.get(src), spec, quality, "api_splits_json", src, aid, errors)
        out.append(row)
    return out


def merge_api(policy: dict[str, Any], records: dict[str, dict[str, Any]], quality: dict[str, Any], errors: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    artifacts_by_id = api_artifacts_from_manifest(quality, errors)
    if not artifacts_by_id:
        return records
    for aid, artifacts in artifacts_by_id.items():
        details = None
        if artifacts.get("details_json_path"):
            path = ROOT / str(artifacts["details_json_path"])
            if path.is_file():
                try:
                    details = read_json(path); quality["source_record_counts"]["api_details_available_count"] += 1
                except Exception:
                    add_error(errors, "API_DETAILS_MAPPING_UNAVAILABLE", "API details JSON could not be read.", {"activity_id": aid})
        rec = records.get(aid)
        if rec is None:
            rec = empty_record(aid)
        rec["api_artifacts"].update(artifacts)
        rec["source_presence"]["fit_file"] = bool(artifacts.get("fit_file_path") and (ROOT / str(artifacts["fit_file_path"])).is_file())
        rec["source_presence"]["tcx_file"] = bool(artifacts.get("tcx_file_path") and (ROOT / str(artifacts["tcx_file_path"])).is_file())
        quality["source_record_counts"]["fit_files_available_count"] += int(rec["source_presence"]["fit_file"])
        quality["source_record_counts"]["tcx_files_available_count"] += int(rec["source_presence"]["tcx_file"])
        if details is not None:
            rec["source_presence"]["api_details"] = True
            for src, spec in policy["api_details_mapping"].items():
                if src not in details: continue
                target = spec["target"]
                value = convert_value(details.get(src), spec, quality, "api_details_json", src, aid, errors)
                if target == "start_time_local":
                    value, date_value = parse_start(value)
                    if rec.get("date") is None: rec["date"] = date_value
                if rec.get(target) is not None and value is not None and str(rec.get(target)) != str(value):
                    quality["field_conflicts"].append({"activity_id": aid, "field": target, "chosen_source": rec["field_sources"].get(target, "workbook_activities_csv"), "sources": [{"source": rec["field_sources"].get(target), "value": rec.get(target)}, {"source": "api_details_json", "value": value}]})
                    add_error(errors, "SOURCE_FIELD_CONFLICT", "Workbook/API field conflict resolved by source priority.", {"activity_id": aid, "field": target})
                elif rec.get(target) is None and value is not None:
                    rec[target] = value
                    rec["field_sources"][target] = "api_details_json"
            if rec["start_time_local"] and rec["date"] is None:
                _, rec["date"] = parse_start(rec["start_time_local"])
        if artifacts.get("splits_json_path"):
            path = ROOT / str(artifacts["splits_json_path"])
            if path.is_file():
                try:
                    payload = read_json(path); quality["source_record_counts"]["api_splits_available_count"] += 1
                    rec["splits"] = normalize_splits(payload, policy, quality, aid, errors)
                    rec["source_presence"]["api_splits"] = True
                    rec["field_sources"]["splits"] = "api_splits_json"
                except Exception:
                    add_error(errors, "API_SPLITS_MAPPING_UNAVAILABLE", "API splits JSON could not be read.", {"activity_id": aid})
        if rec["activity_id"] and rec["start_time_local"] and rec["date"]:
            records[aid] = rec
        else:
            quality["unresolved_api_activities"].append({"activity_id": aid, "reason": "missing_identity_or_start_time"})
            add_error(errors, "UNRESOLVED_API_ACTIVITY", "API activity did not provide required identity and start time.", {"activity_id": aid})
    return records

def build_quality() -> dict[str, Any]:
    return {"module_id": MODULE_ID, "policy_version": POLICY_VERSION, "status": None,
        "source_availability": {"workbook_activities_csv_available": False, "api_ingest_manifest_available": False, "api_ingest_status": None},
        "source_record_counts": {"workbook_rows_count": 0, "api_activity_manifests_count": 0, "api_details_available_count": 0, "api_splits_available_count": 0, "fit_files_available_count": 0, "tcx_files_available_count": 0},
        "normalized_activities_count": 0, "api_only_activities_count": 0, "excluded_invalid_records": [], "duplicate_activity_ids": [], "field_conflicts": [], "unmapped_source_fields": [], "invalid_optional_numeric_values": [], "unresolved_api_activities": [], "field_coverage": {}, "unit_conversions_applied": {"distance_m_to_km_count": 0, "speed_mps_to_kmh_count": 0}, "raw_artifact_handling": {"fit_files_parsed": False, "tcx_files_parsed": False, "fit_tcx_referenced_only": True}, "warnings": ["Missing activity values were preserved as null and were not replaced with zero."], "ready_for_next_module": True}


def sort_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(records, key=lambda r: (r.get("date") or "", r.get("start_time_local") or "", r.get("activity_id") or ""))


def build_by_date(records: list[dict[str, Any]], status: str) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in records:
        groups[r["date"]].append({"activity_id": r["activity_id"], "start_time_local": r["start_time_local"], "activity_type": r["activity_type"], "activity_name": r["activity_name"], "distance_km": r["distance_km"], "duration_seconds": r["duration_seconds"], "calories": r["calories"], "average_hr_bpm": r["average_hr_bpm"], "maximum_hr_bpm": r["maximum_hr_bpm"], "average_power_w": r["average_power_w"], "elevation_gain_m": r["elevation_gain_m"], "perceived_effort_rpe": r["perceived_effort_rpe"], "subjective_feeling_score": r["subjective_feeling_score"]})
    return {"module_id": MODULE_ID, "contract_version": VERSION, "policy_version": POLICY_VERSION, "status": "grouped", "activities_count": len(records), "dates_count": len(groups), "activities_by_date": {k: groups[k] for k in sorted(groups)}, "ready_for_next_module": True}


def build_schema(policy: dict[str, Any]) -> dict[str, Any]:
    field_defs = []
    for f in policy["output_fields"]:
        if f in NESTED_FIELDS: continue
        field_defs.append({"name": f, "type": "string" if f in {"activity_id","date","start_time_local","activity_type","activity_name"} else "number", "nullable": f not in {"activity_id","date","start_time_local"}, "description": f"Normalized activity field {f}."})
    return {"module_id": MODULE_ID, "schema_version": "normalized_activity_schema_v1", "policy_version": POLICY_VERSION, "primary_key": "activity_id", "date_grouping_field": "date", "date_grouping_source": "start_time_local", "missing_values_policy": "preserve_as_null", "fields": field_defs, "nested_fields": [{"name":"splits","type":"array","nullable":False,"description":"Optional normalized split records sourced only from approved API split mapping."},{"name":"source_presence","type":"object","nullable":False,"description":"Information about available workbook and API artifact sources."},{"name":"api_artifacts","type":"object","nullable":False,"description":"Relative references to locally stored raw API artifacts; FIT and TCX are not parsed here."}], "excluded_derived_fields": ["training_load","efficiency_score","capacity_score","acute_load","chronic_load","acwr","monotony","strain","readiness","pws_score","pws_components","pws_weights","pws_priority"]}


def write_csv(records: list[dict[str, Any]], fields: list[str]) -> None:
    with OUT_CSV.open("w", encoding="utf-8", newline="") as h:
        writer = csv.DictWriter(h, fieldnames=fields)
        writer.writeheader()
        for r in records:
            row = {f: "" if r.get(f) is None else r.get(f) for f in fields if f in r}
            sp = r["source_presence"]
            row.update({"has_workbook_source": sp["workbook"], "has_api_details": sp["api_details"], "has_api_splits": sp["api_splits"], "has_fit_file": sp["fit_file"], "has_tcx_file": sp["tcx_file"]})
            writer.writerow(row)


def load_policy(errors: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not POLICY_PATH.is_file():
        add_error(errors, "ACTIVITY_NORMALIZATION_POLICY_NOT_FOUND", "Activity normalization policy was not found.", blocking=True)
        return None
    try:
        policy = read_json(POLICY_PATH)
    except Exception as exc:
        add_error(errors, "ACTIVITY_NORMALIZATION_POLICY_INVALID", str(exc), blocking=True)
        return None
    if policy.get("policy_version") != POLICY_VERSION or policy.get("missing_values_policy") != "preserve_as_null" or policy.get("fit_tcx_policy", {}).get("parse_fit") is not False or policy.get("fit_tcx_policy", {}).get("parse_tcx") is not False:
        add_error(errors, "ACTIVITY_NORMALIZATION_POLICY_INVALID", "Policy required settings are invalid.", blocking=True)
        return None
    return policy


def normalize(policy: dict[str, Any], errors: list[dict[str, Any]]) -> tuple[str, dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    quality = build_quality()
    records = normalize_workbook(policy, quality, errors)
    workbook_count = len(records)
    records = merge_api(policy, records, quality, errors)
    activity_list = sort_records(list(records.values()))
    api_only = sum(1 for r in activity_list if r["source_presence"]["api_details"] and not r["source_presence"]["workbook"])
    quality["api_only_activities_count"] = api_only
    quality["normalized_activities_count"] = len(activity_list)
    for field in [f for f in policy["csv_fields"] if not f.startswith("has_") and f not in {"activity_id","date","start_time_local"}]:
        available = sum(1 for r in activity_list if r.get(field) is not None)
        total = len(activity_list)
        quality["field_coverage"][field] = {"available_count": available, "missing_count": total - available, "coverage_ratio": round(available / total, 6) if total else 0}
    if not activity_list:
        status = "normalized_empty_no_activity_sources"
    elif workbook_count and any(r["source_presence"]["api_details"] or r["source_presence"]["api_splits"] or r["source_presence"]["fit_file"] or r["source_presence"]["tcx_file"] for r in activity_list):
        status = "normalized_with_api_enrichment"
    elif workbook_count:
        status = "normalized_from_workbook_only"
    elif api_only:
        status = "normalized_from_api_only"
    else:
        status = "normalized_with_warnings"
    if quality["field_conflicts"] or quality["excluded_invalid_records"] or quality["unresolved_api_activities"] or quality["invalid_optional_numeric_values"]:
        if status != "normalized_empty_no_activity_sources":
            status = "normalized_with_warnings" if not (workbook_count and any(r["source_presence"]["api_details"] for r in activity_list)) else status
    quality["status"] = status
    dates = [r["date"] for r in activity_list]
    payload = {"module_id": MODULE_ID, "contract_version": VERSION, "policy_version": POLICY_VERSION, "status": status, "source_summary": {"workbook_activities_available": quality["source_availability"]["workbook_activities_csv_available"], "api_ingest_manifest_available": quality["source_availability"]["api_ingest_manifest_available"], "api_enrichment_applied": any(r["source_presence"]["api_details"] or r["source_presence"]["api_splits"] for r in activity_list)}, "activities_count": len(activity_list), "date_range": {"first_date": min(dates) if dates else None, "last_date": max(dates) if dates else None}, "fields": policy["output_fields"], "activities": activity_list, "missing_values_policy": "preserve_as_null", "ready_for_next_module": True, "private_data_notice": "Normalized activity records may contain private health, training and location-related data and must not be committed to version control."}
    return status, payload, build_by_date(activity_list, status), build_schema(policy), quality


def write_outputs(started: str, status: str, errors: list[dict[str, Any]], generated: list[str], log: list[str]) -> int:
    finished = now_iso(); exec_status = "success" if status in SUCCESS else "failed"
    write_json(ERRORS_FILE, {"module_id": MODULE_ID, "errors": errors}); generated.append(rel(ERRORS_FILE))
    log.extend([f"finished_at={finished}", f"execution_status={exec_status}", f"domain_status={status}", "missing_values_preserved_as_null=true", "fit_files_parsed=false", "tcx_files_parsed=false", "derived_training_metrics_calculated=false", "llm_used=false"])
    LOG_FILE.write_text("\n".join(log)+"\n", encoding="utf-8"); generated.append(rel(LOG_FILE)); generated.append(rel(RUN_MANIFEST))
    write_json(RUN_MANIFEST, {"module_id": MODULE_ID, "module_version": VERSION, "policy_version": POLICY_VERSION, "started_at": started, "finished_at": finished, "execution_status": exec_status, "domain_status": status, "inputs": ["config/garmin_activity_normalization_v1.json", "optional: data/pipeline/03_trim_workbook/trimmed_sheets/Activities.csv", "optional: data/pipeline/04_garmin_activity_ingest/activity_ingest_manifest.json"], "generated_artifacts": generated, "log_file": rel(LOG_FILE), "errors_file": rel(ERRORS_FILE)})
    return 0 if exec_status == "success" else 1


def execute(root: Path | None = None) -> int:
    if root is not None: reset_paths(root)
    started = now_iso(); ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    errors: list[dict[str, Any]] = []; generated: list[str] = []
    log = [f"module_id={MODULE_ID}", f"started_at={started}"]
    try:
        policy = load_policy(errors)
        if policy is None:
            return write_outputs(started, "blocked_invalid_policy", errors, generated, log)
        status, payload, by_date, schema, quality = normalize(policy, errors)
        for path, obj in [(OUT_JSON, payload), (OUT_BY_DATE, by_date), (OUT_SCHEMA, schema), (OUT_QUALITY, quality)]:
            write_json(path, obj); generated.append(rel(path))
        write_csv(payload["activities"], policy["csv_fields"]); generated.append(rel(OUT_CSV))
        log.extend([f"policy_version={POLICY_VERSION}", f"workbook_activities_csv_available={quality['source_availability']['workbook_activities_csv_available']}", f"api_ingest_manifest_available={quality['source_availability']['api_ingest_manifest_available']}", f"api_ingest_status={quality['source_availability']['api_ingest_status']}", f"workbook_rows_count={quality['source_record_counts']['workbook_rows_count']}", f"api_activity_manifests_count={quality['source_record_counts']['api_activity_manifests_count']}", f"normalized_activities_count={quality['normalized_activities_count']}", f"api_only_activities_count={quality['api_only_activities_count']}", f"excluded_invalid_records_count={len(quality['excluded_invalid_records'])}", f"field_conflicts_count={len(quality['field_conflicts'])}", f"distance_m_to_km_count={quality['unit_conversions_applied']['distance_m_to_km_count']}", f"speed_mps_to_kmh_count={quality['unit_conversions_applied']['speed_mps_to_kmh_count']}"])
        return write_outputs(started, status, errors, generated, log)
    except Exception as exc:
        add_error(errors, "ARTIFACT_WRITE_ERROR", f"Activity normalization failed unexpectedly: {exc}", blocking=True)
        return write_outputs(started, "normalization_failed", errors, generated, log)


def main() -> int:
    return execute()

if __name__ == "__main__":
    sys.exit(main())
