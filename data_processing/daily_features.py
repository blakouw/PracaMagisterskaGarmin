from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MODULE_ID = "07_build_daily_features"
VERSION = "1.0.0"
POLICY_VERSION = "daily_features_policy_v1"
ROOT = Path(__file__).resolve().parents[2]
SUCCESS = {"built", "built_without_activity_source", "built_with_activity_source_warnings"}


def configure(root: Path) -> dict[str, Path]:
    base05 = root / "data" / "pipeline" / "05_normalize_daily_records"
    base06 = root / "data" / "pipeline" / "06_normalize_activities"
    out = root / "data" / "pipeline" / MODULE_ID
    return {
        "root": root,
        "policy": root / "config" / "daily_features_policy_v1.json",
        "daily": base05 / "daily_records.json",
        "daily_schema": base05 / "daily_records_schema.json",
        "daily_quality": base05 / "data_quality_report.json",
        "activities": base06 / "activities_normalized.json",
        "activities_by_date": base06 / "activities_by_date.json",
        "activity_schema": base06 / "activity_schema.json",
        "activity_quality": base06 / "activity_data_quality_report.json",
        "out": out,
        "json": out / "daily_features.json",
        "csv": out / "daily_features.csv",
        "parquet": out / "daily_features.parquet",
        "schema": out / "daily_features_schema.json",
        "quality": out / "daily_features_quality_report.json",
        "lineage": out / "daily_features_lineage.json",
        "run": out / "run_manifest.json",
        "log": out / "run_log.txt",
        "errors": out / "errors.json",
    }


PATHS = configure(ROOT)


def reset_paths(root: Path) -> None:
    global ROOT, PATHS
    ROOT = root
    PATHS = configure(root)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def error(errors: list[dict[str, Any]], code: str, msg: str, ctx: dict[str, Any] | None = None, blocking: bool = False) -> None:
    item = {"code": code, "message": msg, "context": ctx or {}}
    if not blocking:
        item["blocking"] = False
    errors.append(item)


def number(value: Any) -> tuple[int | float | None, bool]:
    if value is None:
        return None, True
    if isinstance(value, bool):
        return None, False
    if isinstance(value, (int, float)):
        return value, True
    text = str(value).strip()
    if text == "":
        return None, True
    try:
        n = float(text.replace(" ", "").replace(",", "."))
    except ValueError:
        return None, False
    return (int(n) if n.is_integer() else n), True


def rounded(value: float | int | None) -> float | int | None:
    if value is None:
        return None
    r = round(float(value), 6)
    return int(r) if r.is_integer() else r


def validate_policy(errors: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not PATHS["policy"].is_file():
        error(errors, "DAILY_FEATURES_POLICY_NOT_FOUND", "Daily features policy was not found.", blocking=True)
        return None
    try:
        policy = read_json(PATHS["policy"])
    except Exception as exc:
        error(errors, "DAILY_FEATURES_POLICY_INVALID", str(exc), blocking=True)
        return None
    checks = {
        "policy_version": POLICY_VERSION,
        "primary_key": "date",
        "row_creation_rule": "one_feature_row_per_daily_record_date_only",
        "missing_health_values_policy": "preserve_as_null",
        "no_activity_technical_aggregation_policy": "zero_for_counts_and_sums_null_for_means",
    }
    for key, expected in checks.items():
        if policy.get(key) != expected:
            error(errors, "DAILY_FEATURES_POLICY_INVALID", f"Invalid policy setting: {key}", {"expected": expected, "actual": policy.get(key)}, blocking=True)
            return None
    if not isinstance(policy.get("activity_daily_aggregations"), dict):
        error(errors, "DAILY_FEATURES_POLICY_INVALID", "Activity aggregation policy is missing.", blocking=True)
        return None
    return policy


def load_daily(errors: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, str | None]:
    if not PATHS["daily"].is_file():
        error(errors, "DAILY_RECORDS_NOT_FOUND", "Module 05 daily_records.json is required.", blocking=True)
        return None, "blocked_missing_daily_records"
    try:
        payload = read_json(PATHS["daily"])
    except Exception as exc:
        error(errors, "DAILY_RECORDS_NOT_FOUND", f"Daily records could not be read: {exc}", blocking=True)
        return None, "blocked_missing_daily_records"
    if payload.get("ready_for_next_module") is not True:
        error(errors, "DAILY_RECORDS_NOT_READY", "Module 05 daily records are not ready.", blocking=True)
        return None, "blocked_daily_records_not_ready"
    records = payload.get("records")
    if not isinstance(records, list) or not records:
        error(errors, "DAILY_RECORDS_NOT_READY", "Module 05 daily records are empty or invalid.", blocking=True)
        return None, "blocked_daily_records_not_ready"
    seen: set[str] = set()
    for record in records:
        date = record.get("date") if isinstance(record, dict) else None
        if not isinstance(date, str) or not date:
            error(errors, "DAILY_RECORD_DATE_MISSING", "A daily record is missing date.", blocking=True)
            return None, "blocked_daily_records_not_ready"
        if date in seen:
            error(errors, "DUPLICATE_DAILY_FEATURE_DATE", "Duplicate daily date found.", {"date": date}, blocking=True)
            return None, "blocked_duplicate_daily_dates"
        seen.add(date)
    payload["records"] = sorted(records, key=lambda r: r["date"])
    return payload, None


def load_activities(errors: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any] | None, bool, list[str]]:
    if not PATHS["activities"].is_file() and not PATHS["activities_by_date"].is_file():
        error(errors, "ACTIVITY_SOURCE_NOT_AVAILABLE", "Activity source not available; daily-only table will be built.")
        return [], None, False, ["Activity source artifacts were not available."]
    try:
        payload = read_json(PATHS["activities"]) if PATHS["activities"].is_file() else {"activities": [], "ready_for_next_module": True}
        by_date = read_json(PATHS["activities_by_date"]) if PATHS["activities_by_date"].is_file() else {"ready_for_next_module": True}
    except Exception as exc:
        error(errors, "ACTIVITY_SOURCE_INVALID", f"Activity source could not be read and was ignored: {exc}")
        return [], None, False, ["Activity source artifacts were invalid and ignored."]
    if payload.get("ready_for_next_module") is not True or by_date.get("ready_for_next_module") is not True:
        error(errors, "ACTIVITY_SOURCE_INVALID", "Activity source was not ready and was ignored.")
        return [], payload, False, ["Activity source was not ready and was ignored."]
    activities = payload.get("activities", [])
    if not isinstance(activities, list):
        error(errors, "ACTIVITY_SOURCE_INVALID", "Activity source has invalid shape.")
        return [], payload, False, ["Activity source has invalid shape and was ignored."]
    return [a for a in activities if isinstance(a, dict) and a.get("date")], payload, True, []


def numeric_values(activities: list[dict[str, Any]], field: str, date: str, errors: list[dict[str, Any]]) -> list[int | float]:
    vals: list[int | float] = []
    for activity in activities:
        val, ok = number(activity.get(field))
        if not ok:
            error(errors, "ACTIVITY_AGGREGATION_VALUE_INVALID", "Invalid activity aggregation value ignored.", {"date": date, "activity_id": activity.get("activity_id"), "field": field})
        elif val is not None:
            vals.append(val)
    return vals


def aggregate(activities: list[dict[str, Any]], aggs: dict[str, Any], date: str, errors: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, spec in aggs.items():
        op = spec.get("operation")
        if op == "count_records":
            out[name] = len(activities)
        elif op == "sum_available_values":
            if not activities:
                out[name] = spec.get("empty_day_value", 0)
            else:
                vals = numeric_values(activities, spec["source_field"], date, errors)
                out[name] = rounded(sum(vals)) if vals else None
        elif op == "weighted_average_available_pairs":
            total_weight = 0.0
            weighted = 0.0
            for activity in activities:
                val, ok_val = number(activity.get(spec["value_field"]))
                weight, ok_weight = number(activity.get(spec["weight_field"]))
                if not ok_val or not ok_weight:
                    error(errors, "ACTIVITY_AGGREGATION_VALUE_INVALID", "Invalid weighted-average pair ignored.", {"date": date, "activity_id": activity.get("activity_id"), "field": name})
                    continue
                if val is not None and weight is not None and float(weight) > 0:
                    weighted += float(val) * float(weight)
                    total_weight += float(weight)
            out[name] = rounded(weighted / total_weight) if total_weight else None
        elif op == "max_available_values":
            vals = numeric_values(activities, spec["source_field"], date, errors)
            out[name] = rounded(max(vals)) if vals else None
        elif op == "sorted_unique_non_null_values":
            out[name] = sorted({str(a.get(spec["source_field"])).strip() for a in activities if a.get(spec["source_field"]) not in (None, "")})
        elif op == "sorted_unique_values":
            out[name] = sorted({str(a.get(spec["source_field"])).strip() for a in activities if a.get(spec["source_field"]) not in (None, "")})
        else:
            out[name] = None
    return out


def coverage(records: list[dict[str, Any]], fields: list[str]) -> dict[str, dict[str, Any]]:
    total = len(records)
    return {
        f: {
            "available_count": sum(1 for r in records if r.get(f) not in (None, "", [])),
            "missing_count": total - sum(1 for r in records if r.get(f) not in (None, "", [])),
            "coverage_ratio": round(sum(1 for r in records if r.get(f) not in (None, "", [])) / total, 6) if total else 0,
        }
        for f in fields
        if f != "date"
    }


def build(policy: dict[str, Any], daily: dict[str, Any], activities: list[dict[str, Any]], errors: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, list[str]]]:
    daily_dates = {r["date"] for r in daily["records"]}
    by_date: dict[str, list[dict[str, Any]]] = defaultdict(list)
    orphan_counts: dict[str, int] = defaultdict(int)
    for activity in activities:
        date = str(activity.get("date"))
        if date in daily_dates:
            by_date[date].append(activity)
        else:
            orphan_counts[date] += 1
    orphans = [{"date": d, "activities_count": orphan_counts[d]} for d in sorted(orphan_counts)]
    for item in orphans:
        error(errors, "ORPHAN_ACTIVITY_DATE_FOUND", "Activity date excluded because it is absent from module 05 dates.", item)
    features = []
    for record in daily["records"]:
        date = record["date"]
        acts = sorted(by_date.get(date, []), key=lambda a: (a.get("start_time_local") or "", a.get("activity_id") or ""))
        row = dict(record)
        row.update(aggregate(acts, policy["activity_daily_aggregations"], date, errors))
        features.append(row)
    quality = {
        "days_with_activities_but_missing_distance_values": [],
        "days_with_activities_but_missing_duration_values": [],
        "days_with_activities_but_missing_hr_values": [],
    }
    for date, acts in sorted(by_date.items()):
        if acts and not numeric_values(acts, "distance_km", date, errors):
            quality["days_with_activities_but_missing_distance_values"].append(date)
        if acts and not numeric_values(acts, "duration_seconds", date, errors):
            quality["days_with_activities_but_missing_duration_values"].append(date)
        if acts and not numeric_values(acts, "average_hr_bpm", date, errors):
            quality["days_with_activities_but_missing_hr_values"].append(date)
    return features, orphans, quality


def write_csv_output(records: list[dict[str, Any]], fields: list[str]) -> None:
    with PATHS["csv"].open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for r in records:
            row = {f: "" if r.get(f) is None else (json.dumps(r.get(f), ensure_ascii=False, sort_keys=True) if isinstance(r.get(f), (list, dict)) else r.get(f)) for f in fields}
            writer.writerow(row)


def write_parquet(records: list[dict[str, Any]], fields: list[str], errors: list[dict[str, Any]]) -> dict[str, Any]:
    try:
        import pandas as pd  # type: ignore
        import pyarrow  # noqa: F401  # type: ignore
    except Exception as exc:
        msg = f"Optional Parquet dependencies are unavailable: {exc.__class__.__name__}. JSON and CSV were written."
        error(errors, "PARQUET_DEPENDENCY_UNAVAILABLE", msg)
        return {"requested": True, "written": False, "warning": msg}
    try:
        rows = [{f: (json.dumps(r.get(f), ensure_ascii=False, sort_keys=True) if isinstance(r.get(f), (list, dict)) else r.get(f)) for f in fields} for r in records]
        pd.DataFrame(rows, columns=fields).to_parquet(PATHS["parquet"], index=False)
        return {"requested": True, "written": True, "warning": None}
    except Exception as exc:
        msg = f"Parquet write failed: {exc.__class__.__name__}. JSON and CSV were written."
        error(errors, "PARQUET_WRITE_FAILED", msg)
        return {"requested": True, "written": False, "warning": msg}


def schema(fields: list[str], daily_fields: list[str], aggs: dict[str, Any]) -> dict[str, Any]:
    definitions = []
    for f in fields:
        if f == "date":
            definitions.append({"name": f, "type": "string", "nullable": False, "origin": "05_normalize_daily_records", "transformation": "copied", "description": "Primary day key."})
        elif f in daily_fields:
            definitions.append({"name": f, "type": "number_or_string", "nullable": True, "origin": "05_normalize_daily_records", "transformation": "copied", "description": f"Daily source field {f}; copied without semantic change."})
        else:
            definitions.append({"name": f, "type": aggs[f].get("output_type", "number"), "nullable": f != "activity_count", "origin": "06_normalize_activities", "transformation": aggs[f].get("operation"), "description": "Transparent daily activity aggregation."})
    return {"module_id": MODULE_ID, "schema_version": "daily_features_schema_v1", "policy_version": POLICY_VERSION, "primary_key": "date", "primary_key_format": "YYYY-MM-DD", "row_creation_rule": "one_feature_row_per_daily_record_date_only", "missing_health_values_policy": "preserve_as_null", "activity_empty_day_policy": "zero_for_counts_and_sums_null_for_means", "fields": definitions, "excluded_derived_fields": ["rhr_delta", "ln_rmssd", "acute_load", "chronic_load", "acwr", "acwr_ewma", "monotony", "strain", "readiness", "LQ", "REC", "CAP", "VS", "pws_score", "pws_weights", "pws_priority"]}


def lineage(daily_fields: list[str], agg_fields: list[str]) -> dict[str, Any]:
    return {"module_id": MODULE_ID, "lineage_version": "daily_features_lineage_v1", "source_artifacts": [{"module_id": "05_normalize_daily_records", "artifact_path": rel(PATHS["daily"]), "role": "primary_daily_row_source"}, {"module_id": "06_normalize_activities", "artifact_path": rel(PATHS["activities"]), "role": "optional_activity_aggregation_source"}, {"module_id": "06_normalize_activities", "artifact_path": rel(PATHS["activities_by_date"]), "role": "optional_activity_date_group_source"}], "field_groups": [{"group_name": "daily_source_fields", "fields": [f for f in daily_fields if f != "date"], "origin_module": "05_normalize_daily_records", "transformation": "copied_without_semantic_change"}, {"group_name": "activity_daily_counts_and_sums", "fields": [f for f in agg_fields if f == "activity_count" or f.startswith("activity_total_")], "origin_module": "06_normalize_activities", "transformation": "transparent_daily_aggregation"}, {"group_name": "activity_daily_weighted_means", "fields": [f for f in agg_fields if "weighted_average" in f], "origin_module": "06_normalize_activities", "transformation": "duration_weighted_average_over_available_activity_values"}], "forbidden_metrics_confirmation": {"load_metrics_computed": False, "readiness_computed": False, "pws_computed": False, "llm_used": False}}


def finish(started: str, status: str, errors: list[dict[str, Any]], generated: list[str], optional: list[dict[str, Any]], log: list[str]) -> int:
    finished = now()
    execution_status = "success" if status in SUCCESS else "failed"
    write_json(PATHS["errors"], {"module_id": MODULE_ID, "errors": errors})
    generated.append(rel(PATHS["errors"]))
    PATHS["log"].write_text("\n".join(log + [f"finished_at={finished}", f"execution_status={execution_status}", f"domain_status={status}"]) + "\n", encoding="utf-8")
    generated.append(rel(PATHS["log"]))
    generated.append(rel(PATHS["run"]))
    write_json(PATHS["run"], {"module_id": MODULE_ID, "module_version": VERSION, "policy_version": POLICY_VERSION, "started_at": started, "finished_at": finished, "execution_status": execution_status, "domain_status": status, "inputs": [rel(PATHS["policy"]), rel(PATHS["daily"]), rel(PATHS["daily_schema"]), rel(PATHS["daily_quality"]), "optional: " + rel(PATHS["activities"]), "optional: " + rel(PATHS["activities_by_date"]), "optional: " + rel(PATHS["activity_quality"])], "generated_artifacts": generated, "optional_generated_artifacts": optional, "log_file": rel(PATHS["log"]), "errors_file": rel(PATHS["errors"])})
    return 0 if execution_status == "success" else 1


def execute(root: Path | None = None) -> int:
    if root is not None:
        reset_paths(root)
    started = now()
    PATHS["out"].mkdir(parents=True, exist_ok=True)
    errors: list[dict[str, Any]] = []
    generated: list[str] = []
    optional: list[dict[str, Any]] = []
    log = [f"module_id={MODULE_ID}", f"started_at={started}", f"daily_records_path={rel(PATHS['daily'])}"]
    try:
        policy = validate_policy(errors)
        if policy is None:
            return finish(started, "invalid_features_policy", errors, generated, optional, log)
        daily, blocked = load_daily(errors)
        if daily is None:
            return finish(started, blocked or "blocked_daily_records_not_ready", errors, generated, optional, log)
        activities, activity_payload, activity_valid, warnings = load_activities(errors)
        daily_fields = list(daily.get("fields") or daily["records"][0].keys())
        agg_fields = list(policy["activity_daily_aggregations"].keys())
        fields = daily_fields + [f for f in agg_fields if f not in daily_fields]
        records, orphans, agg_quality = build(policy, daily, activities, errors)
        dates = [r["date"] for r in records]
        parquet = write_parquet(records, fields, errors)
        optional.append({"path": rel(PATHS["parquet"]), "written": parquet["written"], "reason_if_not_written": parquet["warning"]})
        dates_with_activities = sum(1 for r in records if r.get("activity_count", 0) > 0)
        status = "built_without_activity_source" if not activity_valid or not activities else "built"
        if activity_valid and activities and (orphans or any(e["code"] in {"ACTIVITY_AGGREGATION_VALUE_INVALID", "ORPHAN_ACTIVITY_DATE_FOUND"} for e in errors)):
            status = "built_with_activity_source_warnings"
        source = {"daily_records": rel(PATHS["daily"]), "activities_by_date": rel(PATHS["activities_by_date"]) if PATHS["activities_by_date"].is_file() else None}
        payload = {"module_id": MODULE_ID, "contract_version": VERSION, "policy_version": POLICY_VERSION, "status": status, "source_artifacts": source, "activity_source_used": bool(activity_valid and activities), "records_count": len(records), "date_range": {"first_date": min(dates), "last_date": max(dates)}, "fields": fields, "records": records, "missing_health_values_policy": "preserve_as_null", "no_activity_technical_aggregation_policy": "zero_for_counts_and_sums_null_for_means", "derived_metrics_computed": False, "ready_for_next_module": True, "private_data_notice": "Daily feature records contain private health, activity and training data and must not be committed to version control."}
        quality = {"module_id": MODULE_ID, "policy_version": POLICY_VERSION, "status": status, "records_count": len(records), "daily_records_source": {"available": True, "records_count": len(daily["records"]), "quality_report_path": rel(PATHS["daily_quality"])}, "activity_source": {"available": activity_valid, "status": (activity_payload or {}).get("status"), "activities_count": len(activities), "quality_report_path": rel(PATHS["activity_quality"]) if PATHS["activity_quality"].is_file() else None}, "dates_with_activities_count": dates_with_activities, "dates_without_activities_count": len(records) - dates_with_activities, "orphan_activity_dates": orphans, "feature_coverage": coverage(records, fields), "activity_aggregation_quality": agg_quality, "parquet_output": parquet, "derived_metrics_computed": False, "warnings": ["Missing physiological values were preserved as null and were not replaced with zero.", "Activity aggregates are technical source-data summaries, not training quality or readiness metrics."] + warnings + ([parquet["warning"]] if parquet["warning"] else []), "ready_for_next_module": True}
        for path, obj in [(PATHS["json"], payload), (PATHS["schema"], schema(fields, daily_fields, policy["activity_daily_aggregations"])), (PATHS["quality"], quality), (PATHS["lineage"], lineage(daily_fields, agg_fields))]:
            write_json(path, obj)
            generated.append(rel(path))
        write_csv_output(records, fields)
        generated.insert(1, rel(PATHS["csv"]))
        log += [f"policy_version={POLICY_VERSION}", f"daily_records_count={len(records)}", f"date_range={min(dates)}..{max(dates)}", f"activity_source_available={activity_valid}", f"activity_source_status={(activity_payload or {}).get('status')}", f"normalized_activities_available={len(activities)}", f"dates_with_activities={dates_with_activities}", f"dates_without_activities={len(records)-dates_with_activities}", f"orphan_activity_dates_count={len(orphans)}", "aggregation_groups=counts_sums_weighted_means_maxima_lists", "json_written=true", "csv_written=true", f"parquet_written={parquet['written']}", "missing_health_values_preserved_as_null=true", "empty_activity_day_sums_zero_only_for_no_activities=true", "acwr_readiness_pws_computed=false", "llm_used=false"]
        return finish(started, status, errors, generated, optional, log)
    except Exception as exc:
        error(errors, "ARTIFACT_WRITE_ERROR", f"Feature build failed unexpectedly: {exc}", blocking=True)
        return finish(started, "feature_build_failed", errors, generated, optional, log)


def main() -> int:
    return execute()


if __name__ == "__main__":
    sys.exit(main())
